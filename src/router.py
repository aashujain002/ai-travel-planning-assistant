import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROUTER_MODEL = "gpt-4o-mini"
TEST_QUESTIONS = (
    "What are the main neighbourhoods in Singapore?",
    "What's the weather forecast for Singapore?",
    "How much is 100 SGD in INR?",
    "Plan a 3-day Singapore itinerary next week based on the weather.",
)

ROUTER_INSTRUCTIONS = """You are a travel assistant capability router. Classify the
user's request by selecting every capability needed to answer it. Do not answer the
user's question.

Available capabilities:
- rag: Stable Singapore destination knowledge, including attractions, neighbourhoods,
  transportation, food, activities, itineraries, and practical travel tips.
- weather: Current or forecast weather, rain, temperature, or planning that depends
  on weather conditions.
- currency: Current exchange rates, currency conversions, or amounts between
  currencies.

Select more than one capability whenever needed. A weather-aware Singapore itinerary
needs both rag and weather. A Singapore food or trip-planning request that also asks
for a currency conversion needs both rag and currency. Do not select rag merely
because Singapore is mentioned if the request only asks for weather or currency."""


class RouteDecision(BaseModel):
    capabilities: list[Literal["rag", "weather", "currency"]] = Field(min_length=1)


def route_question(question: str) -> RouteDecision:
    """Classify a question into the capabilities needed to answer it."""
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Add it to the project's .env file."
        )

    router = ChatOpenAI(
        model=ROUTER_MODEL, temperature=0
    ).with_structured_output(RouteDecision)
    return router.invoke(
        [
            SystemMessage(content=ROUTER_INSTRUCTIONS),
            HumanMessage(content=question),
        ]
    )


def main() -> None:
    for index, question in enumerate(TEST_QUESTIONS, start=1):
        decision = route_question(question)
        print(f"Question {index}: {question}")
        print(f"Capabilities: {' + '.join(decision.capabilities)}\n")


if __name__ == "__main__":
    main()
