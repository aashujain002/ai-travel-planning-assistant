from importlib.metadata import version

import langchain
import langchain_openai
import langchain_text_splitters
import dotenv
import mcp
import httpx

print("Environment OK")
print("LangChain version:", langchain.__version__)
print("MCP version:", version("mcp"))
print("HTTPX version:", version("httpx"))
