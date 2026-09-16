from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.documents import Document

if TYPE_CHECKING:
    from orchestrator import CapabilityEvidence


WEATHER_SOURCE_LABEL = "Current-data source: Weather MCP (Open-Meteo)."
CURRENCY_SOURCE_LABEL = "Current-data source: Currency MCP (Frankfurter)."


def validate_answer(answer: str, evidence: CapabilityEvidence) -> list[str]:
    """Return missing provenance requirements for an evidence-grounded answer."""
    problems: list[str] = []

    if evidence.weather_result is not None and WEATHER_SOURCE_LABEL not in answer:
        problems.append(
            f'Missing weather source label: "{WEATHER_SOURCE_LABEL}"'
        )

    if evidence.currency_result is not None and CURRENCY_SOURCE_LABEL not in answer:
        problems.append(
            f'Missing currency source label: "{CURRENCY_SOURCE_LABEL}"'
        )

    knowledge_documents = (
        (evidence.rag_documents or [])
        + (evidence.activity_documents or [])
        + (evidence.itinerary_documents or [])
    )
    permitted_urls = {
        url
        for document in knowledge_documents
        if isinstance((url := document.metadata.get("url")), str) and url
    }
    if knowledge_documents and not permitted_urls:
        problems.append(
            "Knowledge-base evidence is present but does not include a permitted source URL."
        )
    elif permitted_urls and not any(url in answer for url in permitted_urls):
        problems.append(
            "Missing a permitted source URL for the supplied knowledge-base evidence."
        )

    return problems


def _document(url: str) -> Document:
    return Document(
        page_content="Example Singapore travel evidence.",
        metadata={"source": "Example source", "url": url},
    )


if __name__ == "__main__":
    from orchestrator import CapabilityEvidence

    example_evidence = CapabilityEvidence(
        capabilities=["rag", "weather", "currency"],
        rag_documents=[_document("https://example.com/rag")],
        activity_documents=[_document("https://example.com/activities")],
        itinerary_documents=[_document("https://example.com/itinerary")],
        weather_result="Weather forecast",
        currency_result="Currency conversion",
    )
    valid_answer = """Recommendations:
Choose an activity supported by the retrieved evidence.
[Source](https://example.com/activities)

Current-data source: Weather MCP (Open-Meteo).
Current-data source: Currency MCP (Frankfurter)."""
    invalid_answer = "Recommendations:\nChoose an activity."

    print(f"Valid answer problems: {validate_answer(valid_answer, example_evidence)}")
    print("Invalid answer problems:")
    for problem in validate_answer(invalid_answer, example_evidence):
        print(f"- {problem}")
