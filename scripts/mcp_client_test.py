import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from _paths import add_source_directory

add_source_directory()

from mcp_client import call_tool


WEATHER_START_DATE = datetime.now(ZoneInfo("Asia/Singapore")).date()
WEATHER_END_DATE = WEATHER_START_DATE + timedelta(days=2)
TOOL_CALLS = (
    (
        "get_weather",
        {
            "location": "Singapore",
            "start_date": WEATHER_START_DATE.isoformat(),
            "end_date": WEATHER_END_DATE.isoformat(),
        },
    ),
    (
        "get_currency_rate",
        {"amount": 100, "from_currency": "SGD", "to_currency": "INR"},
    ),
)


async def main() -> None:
    print("Calling MCP tools...")
    for tool_name, arguments in TOOL_CALLS:
        print(f"\nCalling {tool_name}...")
        result = await call_tool(tool_name, arguments)
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
