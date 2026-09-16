import asyncio

from _paths import add_source_directory

add_source_directory()

import orchestrator
from request_parameters import extract_parameters
from router import route_question


async def _simulated_mcp_failure(*_args: object, **_kwargs: object) -> str:
    raise RuntimeError("Simulated MCP failure")


async def _run_failure_scenario(question: str) -> None:
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
        await orchestrator.execute_capabilities(
            question, decision.capabilities, parameters
        )
    except RuntimeError as error:
        print(f"Application raised: {error}")
    finally:
        orchestrator.call_tool = original_call_tool


async def main() -> None:
    scenarios = (
        (
            "Weather",
            "Plan a 3-day Singapore itinerary starting September 21, 2026 "
            "and adjust it based on the weather.",
        ),
        ("Currency", "Convert 100 SGD to INR."),
    )

    for name, question in scenarios:
        print(f"{name} failure simulation:")
        await _run_failure_scenario(question)
        print()


if __name__ == "__main__":
    asyncio.run(main())
