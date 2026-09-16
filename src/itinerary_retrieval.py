import re
from functools import cache

from langchain_core.documents import Document

from document_builder import (
    VISIT_SINGAPORE_ITINERARIES_SOURCE_NAME,
    itinerary_sections_to_documents,
)
from vector_store import load_vector_store
from visit_itineraries_parser import parse_selected_itineraries


SEMANTIC_CANDIDATE_COUNT = 10
ITINERARY_DURATION_PATTERN = re.compile(r"^(\d+) Days in Singapore$")
TEST_CASES = (
    ("What could I do during a 4-day trip to Singapore?", 4),
    ("Plan a 3-day Singapore itinerary based on the available itinerary guidance.", 3),
)


def itinerary_duration(itinerary_name: str) -> int | None:
    """Return the stated number of days for an official itinerary name."""
    match = ITINERARY_DURATION_PATTERN.fullmatch(itinerary_name)
    return int(match.group(1)) if match else None


def select_itinerary_name(question: str, duration_days: int) -> str | None:
    """Choose a semantically relevant official itinerary with the requested duration."""
    vector_store = load_vector_store()
    candidates = vector_store.similarity_search(
        question,
        k=SEMANTIC_CANDIDATE_COUNT,
        filter={"source": VISIT_SINGAPORE_ITINERARIES_SOURCE_NAME},
    )
    for candidate in candidates:
        itinerary_name = candidate.metadata.get("itinerary")
        if (
            isinstance(itinerary_name, str)
            and itinerary_duration(itinerary_name) == duration_days
        ):
            return itinerary_name
    return None


@cache
def official_itinerary_documents() -> tuple[Document, ...]:
    """Load the complete official itinerary sections used for coherent selection."""
    return tuple(
        itinerary_sections_to_documents(parse_selected_itineraries())
    )


def retrieve_itinerary(question: str, duration_days: int) -> list[Document]:
    """Return ordered official day sections for a semantically relevant duration."""
    if duration_days <= 0:
        raise ValueError("Duration must be a positive number of days.")

    itinerary_name = select_itinerary_name(question, duration_days)
    if itinerary_name is None:
        return []

    day_documents = [
        document
        for document in official_itinerary_documents()
        if document.metadata.get("itinerary") == itinerary_name
        and document.metadata.get("day_number") is not None
        and document.metadata["day_number"] <= duration_days
    ]
    day_documents.sort(key=lambda document: document.metadata["day_number"])

    expected_day_numbers = list(range(1, duration_days + 1))
    if [document.metadata["day_number"] for document in day_documents] != expected_day_numbers:
        raise RuntimeError(
            f"{itinerary_name} does not contain all day sections for {duration_days} days."
        )
    return day_documents


def main() -> None:
    for question, duration_days in TEST_CASES:
        documents = retrieve_itinerary(question, duration_days)
        print(f"\nQuestion: {question}")
        if not documents:
            print("No matching official itinerary is available.")
            continue

        print(f"Selected itinerary: {documents[0].metadata['itinerary']}")
        for document in documents:
            metadata = document.metadata
            print(f"\nDay {metadata['day_number']}: {metadata['section']}")
            print(f"Source: {metadata['source']}")
            print(f"URL: {metadata['url']}")


if __name__ == "__main__":
    main()
