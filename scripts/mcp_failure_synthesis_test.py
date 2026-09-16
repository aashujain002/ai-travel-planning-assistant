import asyncio

from _paths import add_source_directory

add_source_directory()

import orchestrator
from conversation import ConversationState, add_user_message, get_conversation_history
from request_parameters import extract_parameters
from router import route_question


async def _simulated_mcp_failure(*_args: object, **_kwargs: object) -> str:
    raise RuntimeError("Simulated MCP failure")


async def _run_failure_scenario(name: str, question: str) -> None:
    decision = route_question(question)
    extracted_parameters = extract_parameters(question)
    parameters, date_clarification = orchestrator.resolve_request_dates(
        extracted_parameters
    )
    if date_clarification is not None:
        raise RuntimeError(date_clarification)

    original_call_tool = orchestrator.call_tool
    orchestrator.call_tool = _simulated_mcp_failure
    try:
        evidence = await orchestrator.execute_capabilities(
            question, decision.capabilities, parameters
        )
    finally:
        orchestrator.call_tool = original_call_tool

    conversation_state = ConversationState()
    add_user_message(conversation_state, question)
    answer = orchestrator.generate_answer(
        question,
        evidence,
        get_conversation_history(conversation_state),
    )

    print(f"{name} failure answer:")
    print(answer)
    print()


async def main() -> None:
    await _run_failure_scenario(
        "Weather",
        "Plan a 3-day Singapore itinerary starting September 21, 2026 and "
        "adjust it based on the weather.",
    )
    await _run_failure_scenario("Currency", "Convert 100 SGD to INR.")


if __name__ == "__main__":
    asyncio.run(main())
