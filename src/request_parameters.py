import math
import os
import re
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXTRACTION_MODEL = "gpt-4o-mini"
CURRENCY_CODE_PATTERN = re.compile(r"^[A-Za-z]{3}$")
TEST_QUESTIONS = (
    "What's the weather in Singapore tomorrow?",
    "What's the weather in Singapore from September 23 to September 25, 2026?",
    "How much is 250 SGD in INR?",
    (
        "Plan a 3-day Singapore itinerary from September 23 to September 25, "
        "2026 based on the weather."
    ),
    "How much is 500 SGD in INR?",
    "Plan a 5-day Singapore trip.",
    "Plan a 3-day Singapore itinerary starting next Monday based on the weather.",
    "Plan a 3-day Singapore itinerary next week based on the weather.",
)

EXTRACTION_INSTRUCTIONS = """You extract parameters from travel questions. Return
only parameters stated by the user. Do not answer the question and do not infer
currencies, amounts, locations, or dates that are absent.

Use start_date and end_date only for explicit calendar dates or date ranges. Return
explicit dates as ISO YYYY-MM-DD values. Preserve relative date wording in
date_expression instead of resolving it. For example, "tomorrow", "next Monday", and
"next week" should populate date_expression and leave start_date and end_date unset.
Return currency codes as three-letter ISO codes.

Only populate amount when the user explicitly provides a monetary amount for a currency
conversion or another money-related request. Do not interpret trip duration, day counts,
distances, activity quantities, dates, or any other non-monetary number as an amount.
For example, "3-day itinerary" and "5-day trip" have no amount, while "250 SGD in INR"
has amount 250. A duration without a calendar date or relative date expression must
not populate start_date or end_date. Never assume that a duration starts today.

Populate duration_days only when the user explicitly requests a duration, such as
"3-day", "5 days", or "for three days". A duration must not populate amount. A
monetary quantity such as "250 SGD" must not populate duration_days. Do not derive
duration_days from an explicit date range."""


class RequestParameters(BaseModel):
    location: str | None = Field(default=None)
    start_date: date | None = Field(default=None)
    end_date: date | None = Field(default=None)
    date_expression: str | None = Field(default=None)
    duration_days: int | None = Field(default=None)
    amount: float | None = Field(default=None)
    from_currency: str | None = Field(default=None)
    to_currency: str | None = Field(default=None)


def validate_parameters(parameters: RequestParameters) -> RequestParameters:
    """Validate and normalize values extracted from the request."""
    if parameters.amount is not None and (
        not math.isfinite(parameters.amount) or parameters.amount <= 0
    ):
        raise ValueError("Amount must be a positive finite number.")

    location = parameters.location.strip() if parameters.location else None
    if parameters.location is not None and not location:
        raise ValueError("Location cannot be empty.")

    date_expression = (
        parameters.date_expression.strip()
        if parameters.date_expression is not None
        else None
    )
    if parameters.date_expression is not None and not date_expression:
        raise ValueError("Date expression cannot be empty.")

    if parameters.duration_days is not None and parameters.duration_days <= 0:
        raise ValueError("Duration must be a positive number of days.")

    currencies = {
        "from_currency": parameters.from_currency,
        "to_currency": parameters.to_currency,
    }
    normalized_currencies = {}
    for field_name, currency in currencies.items():
        if currency is None:
            normalized_currencies[field_name] = None
            continue

        normalized_currency = currency.strip().upper()
        if not CURRENCY_CODE_PATTERN.fullmatch(normalized_currency):
            raise ValueError(
                f"{field_name} must be a three-letter ISO currency code."
            )
        normalized_currencies[field_name] = normalized_currency

    start_date = parameters.start_date
    end_date = parameters.end_date
    if start_date is not None and end_date is None:
        end_date = start_date
    elif end_date is not None and start_date is None:
        start_date = end_date
    elif start_date is not None and end_date is not None and start_date > end_date:
        raise ValueError("Start date must be on or before end date.")

    return parameters.model_copy(
        update={
            "location": location,
            "start_date": start_date,
            "end_date": end_date,
            "date_expression": date_expression,
            "duration_days": parameters.duration_days,
            **normalized_currencies,
        }
    )


def extract_parameters(question: str) -> RequestParameters:
    """Extract and validate the parameters explicitly requested in a question."""
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Add it to the project's .env file."
        )

    extractor = ChatOpenAI(
        model=EXTRACTION_MODEL, temperature=0
    ).with_structured_output(RequestParameters)
    parameters = extractor.invoke(
        [
            SystemMessage(content=EXTRACTION_INSTRUCTIONS),
            HumanMessage(content=f"User question: {question}"),
        ]
    )
    return validate_parameters(parameters)


def main() -> None:
    for index, question in enumerate(TEST_QUESTIONS, start=1):
        parameters = extract_parameters(question)
        print(f"Question {index}: {question}")
        print(f"Parameters: {parameters.model_dump(mode='json')}\n")


if __name__ == "__main__":
    main()
