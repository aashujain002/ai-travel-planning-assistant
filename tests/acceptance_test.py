import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import orchestrator
from conversation import ConversationState, add_assistant_message, add_user_message, get_conversation_history
from preference_extractor import extract_preferences
from request_parameters import extract_parameters
from router import route_question


WEATHER_SOURCE_LABEL = "Current-data source: Weather MCP (Open-Meteo)."
CURRENCY_SOURCE_LABEL = "Current-data source: Currency MCP (Frankfurter)."


async def run_question(
    question: str,
    conversation_state: ConversationState | None = None,
) -> tuple[object, object, orchestrator.CapabilityEvidence | None, str | None]:
    """Execute one request through routing, extraction, capabilities, and synthesis."""
    decision = route_question(question)
    extracted_parameters = extract_parameters(question)
    parameters, date_clarification = orchestrator.resolve_request_dates(
        extracted_parameters
    )
    clarification = date_clarification or orchestrator.validate_capability_parameters(
        decision.capabilities, parameters
    )
    if clarification is not None:
        return decision, parameters, None, clarification

    evidence = await orchestrator.execute_capabilities(
        question, decision.capabilities, parameters
    )
    state = conversation_state or ConversationState()
    add_user_message(state, question)
    answer = orchestrator.generate_answer(
        question,
        evidence,
        get_conversation_history(state),
    )
    add_assistant_message(state, answer)
    return decision, parameters, evidence, answer


async def test_rag_factual_answer() -> None:
    decision, _, evidence, answer = await run_question(
        "What are the main neighbourhoods in Singapore?"
    )
    assert "rag" in decision.capabilities
    assert evidence is not None and evidence.rag_documents
    assert answer is not None


async def test_activity_retrieval() -> None:
    _, _, evidence, answer = await run_question(
        "What are indoor activities in Singapore?"
    )
    assert evidence is not None and evidence.activity_documents
    assert answer is not None


async def test_official_itinerary() -> None:
    _, _, evidence, _ = await run_question("Give me a 4-day Singapore itinerary.")
    assert evidence is not None and evidence.itinerary_documents
    assert [document.metadata["day_number"] for document in evidence.itinerary_documents] == [
        1,
        2,
        3,
        4,
    ]


async def test_missing_official_itinerary() -> None:
    _, _, evidence, _ = await run_question("Give me a 3-day Singapore itinerary.")
    assert evidence is not None
    assert evidence.itinerary_documents is None
    assert evidence.itinerary_retrieval_message is not None
    assert evidence.activity_documents


async def test_weather_mcp() -> None:
    decision, _, evidence, answer = await run_question(
        "What will the weather be in Singapore on September 21, 2026?"
    )
    assert "weather" in decision.capabilities
    assert evidence is not None and evidence.weather_result is not None
    assert "2026-09-21" in evidence.weather_result
    assert answer is not None and WEATHER_SOURCE_LABEL in answer


async def test_currency_mcp() -> None:
    decision, _, evidence, answer = await run_question("Convert 100 SGD to INR.")
    assert "currency" in decision.capabilities
    assert evidence is not None and evidence.currency_result is not None
    assert answer is not None and CURRENCY_SOURCE_LABEL in answer


async def test_combined_rag_and_mcp() -> None:
    decision, _, evidence, answer = await run_question(
        "Plan a 3-day Singapore itinerary starting September 21, 2026 and "
        "adjust it based on the weather."
    )
    assert {"rag", "weather"}.issubset(decision.capabilities)
    assert evidence is not None and evidence.activity_documents
    assert evidence.weather_result is not None
    assert all(
        date in evidence.weather_result
        for date in ("2026-09-21", "2026-09-22", "2026-09-23")
    )
    assert answer is not None and WEATHER_SOURCE_LABEL in answer


async def test_ambiguous_relative_date() -> None:
    question = "Plan a 3-day trip next week based on the weather."
    decision = route_question(question)
    parameters = extract_parameters(question)
    _, clarification = orchestrator.resolve_request_dates(parameters)
    assert "weather" in decision.capabilities
    assert clarification == "Which day would you like the trip to start?"


async def test_multi_turn_context() -> None:
    state = ConversationState()

    async def run_context_turn(question: str) -> tuple[
        object, object, orchestrator.CapabilityEvidence | None, str | None
    ]:
        for preference in extract_preferences(question):
            if preference not in state.preferences:
                state.preferences.append(preference)
        return await run_question(question, state)

    await run_context_turn("I prefer cultural activities and food.")
    await run_context_turn("I also enjoy shopping.")
    _, _, evidence, answer = await run_context_turn("What should I do tomorrow?")

    assert state.preferences == ["cultural activities", "food", "shopping"]
    assert [message.role for message in get_conversation_history(state)] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert evidence is not None and evidence.rag_documents
    assert answer is not None and answer.strip()
    permitted_urls = {
        document.metadata["url"] for document in evidence.rag_documents
    }
    assert any(url in answer for url in permitted_urls)
    assert any(
        preference in answer.casefold()
        for preference in ("cultural", "food", "shopping")
    )


async def simulated_mcp_failure(*_args: object, **_kwargs: object) -> str:
    raise RuntimeError("Simulated MCP failure")


async def test_mcp_failure() -> None:
    original_call_tool = orchestrator.call_tool
    orchestrator.call_tool = simulated_mcp_failure
    try:
        _, _, weather_evidence, weather_answer = await run_question(
            "Plan a 3-day Singapore itinerary starting September 21, 2026 and "
            "adjust it based on the weather."
        )
        _, _, currency_evidence, currency_answer = await run_question(
            "Convert 100 SGD to INR."
        )
    finally:
        orchestrator.call_tool = original_call_tool

    assert weather_evidence is not None
    assert weather_evidence.weather_result is None
    assert weather_evidence.weather_error is not None
    assert weather_answer is not None and WEATHER_SOURCE_LABEL not in weather_answer
    assert currency_evidence is not None
    assert currency_evidence.currency_result is None
    assert currency_evidence.currency_error is not None
    assert currency_answer is not None and CURRENCY_SOURCE_LABEL not in currency_answer


async def main() -> None:
    tests = (
        ("RAG factual answer", test_rag_factual_answer),
        ("Activity retrieval", test_activity_retrieval),
        ("Official itinerary", test_official_itinerary),
        ("Missing official itinerary", test_missing_official_itinerary),
        ("Weather MCP", test_weather_mcp),
        ("Currency MCP", test_currency_mcp),
        ("Combined RAG + MCP", test_combined_rag_and_mcp),
        ("Ambiguous relative date", test_ambiguous_relative_date),
        ("Multi-turn context", test_multi_turn_context),
        ("MCP failure", test_mcp_failure),
    )

    failures = 0
    for name, test in tests:
        try:
            await test()
        except AssertionError as error:
            failures += 1
            print(f"FAIL: {name} - {error}")
        except Exception as error:
            failures += 1
            print(f"ERROR: {name} - {error}")
        else:
            print(f"PASS: {name}")

    if failures:
        raise SystemExit(f"{failures} acceptance test(s) failed.")


if __name__ == "__main__":
    asyncio.run(main())
