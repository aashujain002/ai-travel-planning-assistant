import asyncio
import os
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from activity_retrieval import retrieve_activity_documents
from conversation import (
    ConversationMessage,
    ConversationState,
    add_assistant_message,
    add_user_message,
    get_conversation_history,
)
from date_resolver import resolve_date_range
from grounding_validator import validate_answer
from itinerary_retrieval import retrieve_itinerary
from mcp_client import call_tool
from preference_extractor import extract_preferences
from rag import document_context, retrieve_documents
from request_parameters import RequestParameters, extract_parameters
from router import route_question


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FINAL_MODEL = "gpt-4o-mini"
RAG_CONTENT_PREVIEW_LENGTH = 300
TEST_QUESTIONS = (
    "I prefer cultural activities and food for my Singapore trip.",
    "I also enjoy shopping.",
    "What should I do tomorrow?",
)

FINAL_SYSTEM_INSTRUCTIONS = """You are a Singapore travel-planning assistant.
Answer the user's question using only the supplied evidence. Do not mention internal
capabilities, routing, or evidence collection.

Treat evidence categories differently:
- Conversation context provides preferences and references from earlier turns. It is
  not authoritative travel knowledge and must not be used as factual evidence.
- RAG knowledge-base evidence contains stable Singapore travel facts. Ground claims in
  this evidence and identify their source title and URL. Every factual statement or
  named attraction, neighbourhood, activity, or itinerary item from RAG must include
  an inline source title and URL from the specific supporting evidence.
- Official itinerary evidence contains retrieved, day-specific official itinerary
  guidance. Use it for itinerary planning, preserve the supplied day order, and cite
  its supporting source and URL.
- Activity RAG evidence contains retrieved activity, attraction, food, and local
  experience information. Use it only for clearly labelled AI recommendations and
  cite its supporting source and URL.
- Weather and currency MCP evidence is live external data. Attribute weather facts to
  Weather MCP (Open-Meteo) and currency facts to Currency MCP (Frankfurter) in the
  answer, rather than citing them as knowledge-base sources. Describe weather as a
  forecast for the dates supplied by the tool, not as current conditions.
- Suggestions derived from the evidence are AI recommendations. Put them under a
  "Recommendations:" heading and do not present them as sourced facts.

Do not invent attractions, itineraries, weather, exchange rates, or other facts. If
the supplied evidence is insufficient, say so clearly. Only name a location or activity
when it appears explicitly in the RAG evidence. If an MCP result reports a retrieval
failure, state that the live information is unavailable and do not substitute it with
an invented value or a weather-dependent plan. For a multi-day itinerary, do not fill
days with unsupported attractions; explain when the RAG evidence lacks enough grounded
activities. For example, naming ArtScience Museum, Gardens by the Bay, Clarke Quay,
Singapore Botanic Gardens, or Marina Bay Sands is invalid unless that exact place occurs
in the supplied RAG, activity RAG, or official itinerary evidence. When itinerary
retrieval reports that no matching official itinerary is available and no official
itinerary evidence is supplied, state that limitation. Do not claim that a dedicated
itinerary exists or invent named day-by-day itinerary activities. For a simple factual
question, answer directly without adding generic recommendations.

When itinerary retrieval status reports no matching official itinerary and no generic
RAG or activity RAG evidence is supplied, do not name attractions, provide attraction
examples, or add recommendations. State only the official-itinerary limitation and,
when present, the available MCP data.

When a WEATHER MCP STATUS reports unavailable, state that live weather information is
unavailable. Do not invent a forecast or describe a plan as weather-adjusted. You may
still provide clearly labelled recommendations from supplied RAG evidence. When a
CURRENCY MCP STATUS reports unavailable, state that current conversion information is
unavailable and do not provide an amount or exchange rate. Never include an MCP source
label for an unavailable MCP status.

Response requirements:
- If RAG, activity RAG, or official itinerary evidence is present, add an inline
  Markdown citation after every evidence-derived factual sentence, bullet, or named
  item. Copy that citation verbatim from the corresponding permitted-citations list in
  the user message; do not repeat any instructional wording or placeholders.
- If weather evidence is present, include this exact source label:
  "Current-data source: Weather MCP (Open-Meteo)."
- If currency evidence is present, include this exact source label:
  "Current-data source: Currency MCP (Frankfurter)."
- Put any itinerary or other suggested action under a "Recommendations:" heading. For
  an itinerary, this must be the heading immediately before the day-by-day suggestions.
  When a day lacks a supported named activity, write "No additional specific activity
  is supported by the available knowledge-base evidence." instead of naming one."""


@dataclass
class CapabilityEvidence:
    capabilities: list[str]
    rag_documents: list[Document] | None = None
    itinerary_documents: list[Document] | None = None
    itinerary_retrieval_message: str | None = None
    activity_documents: list[Document] | None = None
    weather_result: str | None = None
    weather_error: str | None = None
    currency_result: str | None = None
    currency_error: str | None = None


def resolve_request_dates(
    parameters: RequestParameters,
) -> tuple[RequestParameters, str | None]:
    """Resolve supported relative dates using the current Singapore calendar date."""
    if parameters.start_date is not None and parameters.end_date is not None:
        if (
            parameters.start_date == parameters.end_date
            and parameters.duration_days is not None
        ):
            expanded_end_date = parameters.start_date + timedelta(
                days=parameters.duration_days - 1
            )
            return parameters.model_copy(
                update={"end_date": expanded_end_date}
            ), None
        return parameters, None

    if parameters.date_expression is None:
        return parameters, None

    today = datetime.now(ZoneInfo("Asia/Singapore")).date()
    resolved_dates = resolve_date_range(
        parameters.date_expression, parameters.duration_days, today
    )
    if resolved_dates is None:
        if parameters.date_expression.strip().casefold() == "next week":
            return parameters, "Which day would you like the trip to start?"
        return (
            parameters,
            "Please provide specific travel dates for the weather forecast.",
        )

    start_date, end_date = resolved_dates
    return parameters.model_copy(
        update={"start_date": start_date, "end_date": end_date}
    ), None


def validate_capability_parameters(
    capabilities: Sequence[str], parameters: RequestParameters
) -> str | None:
    """Return a clarification when a selected capability lacks required inputs."""
    if "weather" in capabilities:
        if parameters.location is None:
            return "Which location would you like the weather forecast for?"
        if parameters.start_date is None or parameters.end_date is None:
            return "What dates would you like the weather forecast for?"
    if "currency" in capabilities:
        if parameters.amount is None:
            return "What amount would you like me to convert?"
        if parameters.from_currency is None:
            return "Which currency would you like to convert from?"
        if parameters.to_currency is None:
            return "Which currency would you like to convert to?"
    return None


def _is_activity_oriented_question(question: str) -> bool:
    normalized_question = question.casefold()
    return any(
        phrase in normalized_question
        for phrase in (
            "activities",
            "things to do",
            "what can i do",
            "indoor",
            "outdoor",
            "cultural",
            "food experiences",
        )
    )


async def execute_capabilities(
    question: str, capabilities: Sequence[str], parameters: RequestParameters
) -> CapabilityEvidence:
    """Execute each selected capability and return its unprocessed evidence."""
    unsupported_capabilities = set(capabilities) - {"rag", "weather", "currency"}
    if unsupported_capabilities:
        unsupported = ", ".join(sorted(unsupported_capabilities))
        raise ValueError(f"Unsupported capabilities: {unsupported}")

    evidence = CapabilityEvidence(capabilities=list(capabilities))
    if "rag" in capabilities:
        if parameters.duration_days is None:
            if _is_activity_oriented_question(question):
                evidence.activity_documents = retrieve_activity_documents(question)
            else:
                evidence.rag_documents = retrieve_documents(question)
        else:
            itinerary_documents = retrieve_itinerary(
                question, parameters.duration_days
            )
            if itinerary_documents:
                evidence.itinerary_documents = itinerary_documents
            else:
                evidence.itinerary_retrieval_message = (
                    "No matching official itinerary is available."
                )
            evidence.activity_documents = retrieve_activity_documents(question)
    if "weather" in capabilities:
        missing_weather_parameters = [
            field_name
            for field_name, value in {
                "location": parameters.location,
                "start_date": parameters.start_date,
                "end_date": parameters.end_date,
            }.items()
            if value is None
        ]
        if missing_weather_parameters:
            missing = ", ".join(missing_weather_parameters)
            raise ValueError(f"Weather requires parameters: {missing}")

        try:
            evidence.weather_result = await call_tool(
                "get_weather",
                {
                    "location": parameters.location,
                    "start_date": parameters.start_date.isoformat(),
                    "end_date": parameters.end_date.isoformat(),
                },
            )
        except RuntimeError:
            evidence.weather_error = "Live weather information is currently unavailable."
    if "currency" in capabilities:
        missing_currency_parameters = [
            field_name
            for field_name, value in {
                "amount": parameters.amount,
                "from_currency": parameters.from_currency,
                "to_currency": parameters.to_currency,
            }.items()
            if value is None
        ]
        if missing_currency_parameters:
            missing = ", ".join(missing_currency_parameters)
            raise ValueError(f"Currency requires parameters: {missing}")

        try:
            evidence.currency_result = await call_tool(
                "get_currency_rate",
                {
                    "amount": parameters.amount,
                    "from_currency": parameters.from_currency,
                    "to_currency": parameters.to_currency,
                },
            )
        except RuntimeError:
            evidence.currency_error = "Live currency information is currently unavailable."

    return evidence


def print_execution_results(evidence: CapabilityEvidence) -> None:
    """Print raw capability evidence for the parameter integration demo."""
    if evidence.rag_documents is not None:
        print("\nRAG results:")
        for index, document in enumerate(evidence.rag_documents, start=1):
            preview = " ".join(document.page_content.split())[:RAG_CONTENT_PREVIEW_LENGTH]
            print(f"{index}. {preview}")
    if evidence.itinerary_documents is not None:
        print("\nOfficial itinerary results:")
        for document in evidence.itinerary_documents:
            metadata = document.metadata
            print(f"Day {metadata['day_number']}: {metadata['section']}")
            print(f"Source: {metadata['source']}")
            print(f"URL: {metadata['url']}")
    if evidence.itinerary_retrieval_message is not None:
        print(f"\nItinerary result: {evidence.itinerary_retrieval_message}")
    if evidence.activity_documents is not None:
        print("\nActivity RAG results:")
        for index, document in enumerate(evidence.activity_documents, start=1):
            metadata = document.metadata
            section = (
                metadata.get("section")
                or metadata.get("Header 3")
                or metadata.get("Header 2")
                or "Not specified"
            )
            preview = " ".join(document.page_content.split())[
                :RAG_CONTENT_PREVIEW_LENGTH
            ]
            print(f"{index}. {section} ({metadata.get('source', 'Unknown source')})")
            print(f"   {preview}")
    if evidence.weather_result is not None:
        print(f"\nWeather result:\n{evidence.weather_result}")
    if evidence.weather_error is not None:
        print(f"\nWeather status:\nUnavailable: {evidence.weather_error}")
    if evidence.currency_result is not None:
        print(f"\nCurrency result:\n{evidence.currency_result}")
    if evidence.currency_error is not None:
        print(f"\nCurrency status:\nUnavailable: {evidence.currency_error}")


def _provenance_fallback(evidence: CapabilityEvidence) -> str:
    """Return a non-factual response that satisfies available provenance requirements."""
    sections = [
        "Unable to produce a response that meets the required provenance standards."
    ]
    knowledge_documents = (
        (evidence.rag_documents or [])
        + (evidence.activity_documents or [])
        + (evidence.itinerary_documents or [])
    )
    permitted_urls = [
        document.metadata["url"]
        for document in knowledge_documents
        if isinstance(document.metadata.get("url"), str) and document.metadata["url"]
    ]
    if permitted_urls:
        sections.append(f"Knowledge-base source: {permitted_urls[0]}")
    if evidence.weather_result is not None:
        sections.append("Current-data source: Weather MCP (Open-Meteo).")
    if evidence.currency_result is not None:
        sections.append("Current-data source: Currency MCP (Frankfurter).")
    return "\n\n".join(sections)


def generate_answer(
    question: str,
    evidence: CapabilityEvidence,
    conversation_history: Sequence[ConversationMessage],
) -> str:
    """Generate a grounded answer from the selected capability evidence."""
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Add it to the project's .env file."
        )

    evidence_sections = []
    if evidence.rag_documents is not None:
        rag_context = "\n\n---\n\n".join(
            document_context(document) for document in evidence.rag_documents
        )
        citations = "\n".join(
            f"- [{document.metadata['source']}]({document.metadata['url']})"
            for document in evidence.rag_documents
        )
        evidence_sections.append(
            f"RAG KNOWLEDGE-BASE EVIDENCE:\n{rag_context}\n\n"
            f"PERMITTED RAG CITATIONS:\n{citations}"
        )
    if evidence.itinerary_documents is not None:
        itinerary_context = "\n\n---\n\n".join(
            (
                f"DAY: {document.metadata['day_number']}\n"
                f"{document_context(document)}"
            )
            for document in evidence.itinerary_documents
        )
        citations = "\n".join(
            f"- [{document.metadata['source']}]({document.metadata['url']})"
            for document in evidence.itinerary_documents
        )
        evidence_sections.append(
            f"OFFICIAL ITINERARY EVIDENCE:\n{itinerary_context}\n\n"
            f"PERMITTED OFFICIAL ITINERARY CITATIONS:\n{citations}"
        )
    if evidence.itinerary_retrieval_message is not None:
        evidence_sections.append(
            "ITINERARY RETRIEVAL STATUS:\n"
            f"{evidence.itinerary_retrieval_message}"
        )
    if evidence.activity_documents is not None:
        activity_context = "\n\n---\n\n".join(
            document_context(document) for document in evidence.activity_documents
        )
        citations = "\n".join(
            f"- [{document.metadata['source']}]({document.metadata['url']})"
            for document in evidence.activity_documents
        )
        evidence_sections.append(
            f"ACTIVITY RAG EVIDENCE:\n{activity_context}\n\n"
            f"PERMITTED ACTIVITY RAG CITATIONS:\n{citations}"
        )
    if evidence.weather_result is not None:
        evidence_sections.append(
            "WEATHER MCP EVIDENCE (live external data from Open-Meteo):\n"
            f"{evidence.weather_result}"
        )
    if evidence.weather_error is not None:
        evidence_sections.append(
            f"WEATHER MCP STATUS:\nUnavailable: {evidence.weather_error}"
        )
    if evidence.currency_result is not None:
        evidence_sections.append(
            "CURRENCY MCP EVIDENCE (live external data from Frankfurter):\n"
            f"{evidence.currency_result}"
        )
    if evidence.currency_error is not None:
        evidence_sections.append(
            f"CURRENCY MCP STATUS:\nUnavailable: {evidence.currency_error}"
        )

    formatted_evidence = "\n\n".join(evidence_sections)
    formatted_history = "\n".join(
        f"{message.role.title()}: {message.content}"
        for message in conversation_history
    )
    llm = ChatOpenAI(model=FINAL_MODEL, temperature=0)
    response = llm.invoke(
        [
            SystemMessage(content=FINAL_SYSTEM_INSTRUCTIONS),
            HumanMessage(
                content=(
                    f"CONVERSATION CONTEXT:\n{formatted_history}\n\n"
                    f"USER QUESTION:\n{question}\n\n"
                    f"{formatted_evidence}"
                )
            ),
        ]
    )
    if not isinstance(response.content, str):
        raise RuntimeError("Final LLM returned a non-text response.")

    problems = validate_answer(response.content, evidence)
    if not problems:
        return response.content

    correction_response = llm.invoke(
        [
            SystemMessage(content=FINAL_SYSTEM_INSTRUCTIONS),
            HumanMessage(
                content=(
                    f"CONVERSATION CONTEXT:\n{formatted_history}\n\n"
                    f"USER QUESTION:\n{question}\n\n"
                    f"{formatted_evidence}\n\n"
                    f"PREVIOUS ANSWER:\n{response.content}\n\n"
                    "The previous answer failed these grounding requirements:\n"
                    f"{chr(10).join(f'- {problem}' for problem in problems)}\n\n"
                    "Revise the answer using only the supplied evidence. Do not "
                    "introduce any new facts. Correct only the grounding and "
                    "provenance issues. Return only the corrected answer."
                )
            ),
        ]
    )
    if not isinstance(correction_response.content, str):
        raise RuntimeError("Corrected final LLM response was non-text.")
    if validate_answer(correction_response.content, evidence):
        return _provenance_fallback(evidence)
    return correction_response.content


async def main() -> None:
    conversation_state = ConversationState()
    for question in TEST_QUESTIONS:
        add_user_message(conversation_state, question)
        for preference in extract_preferences(question):
            if preference not in conversation_state.preferences:
                conversation_state.preferences.append(preference)

        decision = route_question(question)
        extracted_parameters = extract_parameters(question)
        parameters, date_clarification = resolve_request_dates(extracted_parameters)
        print(f"Question: {question}")
        print(f"Capabilities: {' + '.join(decision.capabilities)}")
        print(
            f"Extracted parameters: {extracted_parameters.model_dump(mode='json')}"
        )
        print(f"Resolved parameters: {parameters.model_dump(mode='json')}")

        clarification = date_clarification or validate_capability_parameters(
            decision.capabilities, parameters
        )
        if clarification is not None:
            print(f"\nClarification: {clarification}")
        else:
            evidence = await execute_capabilities(
                question, decision.capabilities, parameters
            )
            print_execution_results(evidence)
            answer = generate_answer(
                question,
                evidence,
                get_conversation_history(conversation_state),
            )
            add_assistant_message(conversation_state, answer)
            print(f"\nAnswer:\n{answer}")
        print(f"\nStored preferences: {conversation_state.preferences}")
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
