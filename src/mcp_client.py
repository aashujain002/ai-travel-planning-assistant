import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent


SERVER_SCRIPT = Path(__file__).with_name("mcp_server.py")


async def call_tool(tool_name: str, arguments: dict[str, object]) -> str:
    """Call an MCP tool and return its text result."""
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_SCRIPT)],
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = await session.list_tools()
            if not any(tool.name == tool_name for tool in tools.tools):
                raise RuntimeError(f"MCP server did not expose {tool_name!r}.")

            result = await session.call_tool(tool_name, arguments=arguments)

    text_parts = [
        content.text for content in result.content if isinstance(content, TextContent)
    ]
    if result.is_error:
        details = "\n".join(text_parts) or str(result.content)
        raise RuntimeError(f"{tool_name} failed: {details}")
    if not text_parts:
        raise RuntimeError(f"{tool_name} returned no text content.")

    return "\n".join(text_parts)
