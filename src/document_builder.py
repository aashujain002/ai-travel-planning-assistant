import re
from pathlib import Path

from langchain_core.documents import Document

from ingestion import clean_wikivoyage_html
from section_parser import ParsedSection, parse_sections
from visit_itineraries_parser import (
    SELECTED_ITINERARIES,
    ItinerarySection,
    parse_selected_itineraries,
)
from visit_singapore_parser import VisitSingaporeSection, parse_visit_singapore


RAW_HTML_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "wikivoyage_singapore.html"
)
SOURCE_NAME = "Wikivoyage Singapore Travel Guide"
SOURCE_URL = "https://en.wikivoyage.org/wiki/Singapore"
VISIT_SINGAPORE_PLAN_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "visit_singapore_plan.html"
)
VISIT_SINGAPORE_SOURCE_NAME = "Visit Singapore – Plan Your Trip"
VISIT_SINGAPORE_SOURCE_URL = (
    "https://www.visitsingapore.com/mice/en/tools-and-resources/plan-your-trip/"
)
VISIT_SINGAPORE_ITINERARIES_SOURCE_NAME = (
    "Visit Singapore – Official Itineraries"
)
TOPIC_BY_SECTION = {
    "Districts": "neighbourhoods",
    "Understand": "culture_and_practical_tips",
    "Get in": "visitor_preparation",
    "Get around": "transportation",
    "See": "attractions",
    "Do": "activities",
    "Eat": "food_and_local_experiences",
    "Stay safe": "culture_and_practical_tips",
}
TOPIC_BY_VISIT_SECTION = {
    "Curated for Your Downtime": "activities",
    "What You Need To Know About Singapore": "general",
    "Travel Tips": "visitor_preparation",
    "Payment Methods": "culture_and_practical_tips",
    "Commuting around the island": "transportation",
    "Ways to Pay": "transportation",
    "Taxi or Private Hire Car": "transportation",
    "Taxi Fares": "transportation",
}
DAY_SECTION_PATTERN = re.compile(r"^Day\s+(\d+)\b", re.IGNORECASE)


def extract_day_number(section_name: str) -> int | None:
    """Return the day number for an itinerary day section."""
    match = DAY_SECTION_PATTERN.match(section_name.strip())
    return int(match.group(1)) if match else None


def sections_to_documents(sections: list[ParsedSection]) -> list[Document]:
    documents = []

    for section in sections:
        headers = section["headers"]
        metadata = {
            "source": SOURCE_NAME,
            "url": SOURCE_URL,
            "topic": TOPIC_BY_SECTION.get(headers.get("Header 2"), "general"),
            **headers,
        }
        documents.append(Document(page_content=section["text"], metadata=metadata))

    return documents


def visit_sections_to_documents(
    sections: list[VisitSingaporeSection],
) -> list[Document]:
    documents = []

    for section in sections:
        section_name = section["section"]
        metadata = {
            "source": VISIT_SINGAPORE_SOURCE_NAME,
            "url": VISIT_SINGAPORE_SOURCE_URL,
            "topic": TOPIC_BY_VISIT_SECTION.get(section_name, "general"),
            "section": section_name,
        }
        documents.append(Document(page_content=section["text"], metadata=metadata))

    return documents


def itinerary_sections_to_documents(
    itineraries: dict[str, list[ItinerarySection]],
) -> list[Document]:
    documents = []

    for itinerary_name, sections in itineraries.items():
        url = SELECTED_ITINERARIES.get(itinerary_name)
        if url is None:
            raise RuntimeError(f"No URL is configured for {itinerary_name}.")

        for section in sections:
            metadata = {
                "source": VISIT_SINGAPORE_ITINERARIES_SOURCE_NAME,
                "url": url,
                "topic": "itineraries",
                "itinerary": section["itinerary"],
                "section": section["section"],
                "day_number": extract_day_number(section["section"]),
            }
            documents.append(
                Document(page_content=section["text"], metadata=metadata)
            )

    return documents


def load_all_documents() -> list[Document]:
    wikivoyage_html = RAW_HTML_PATH.read_text(encoding="utf-8")
    wikivoyage_documents = sections_to_documents(
        parse_sections(clean_wikivoyage_html(wikivoyage_html))
    )

    visit_singapore_html = VISIT_SINGAPORE_PLAN_PATH.read_text(encoding="utf-8")
    visit_singapore_documents = visit_sections_to_documents(
        parse_visit_singapore(visit_singapore_html)
    )
    itinerary_documents = itinerary_sections_to_documents(
        parse_selected_itineraries()
    )

    return [
        *wikivoyage_documents,
        *visit_singapore_documents,
        *itinerary_documents,
    ]


def main() -> None:
    raw_html = RAW_HTML_PATH.read_text(encoding="utf-8")
    sections = parse_sections(clean_wikivoyage_html(raw_html))
    documents = sections_to_documents(sections)

    for index, document in enumerate(documents[:5], start=1):
        print(f"\nDocument {index}:")
        print(f"page_content: {document.page_content}")
        print(f"metadata: {document.metadata}")

    visit_sections = parse_visit_singapore(
        VISIT_SINGAPORE_PLAN_PATH.read_text(encoding="utf-8")
    )
    visit_documents = visit_sections_to_documents(visit_sections)

    print("\nVisit Singapore Documents:")
    for section_name in (
        "Travel Tips",
        "Commuting around the island",
        "Taxi or Private Hire Car",
    ):
        document = next(
            document
            for document in visit_documents
            if document.metadata["section"] == section_name
        )
        print(f"\nSection: {section_name}")
        print(f"page_content: {document.page_content}")
        print(f"metadata: {document.metadata}")

    itinerary_documents = itinerary_sections_to_documents(
        parse_selected_itineraries()
    )
    print("\nOfficial Itinerary Documents:")
    for itinerary_name in SELECTED_ITINERARIES:
        document = next(
            document
            for document in itinerary_documents
            if document.metadata["itinerary"] == itinerary_name
        )
        print(f"\nItinerary: {itinerary_name}")
        print(f"page_content: {document.page_content}")
        print(f"metadata: {document.metadata}")


if __name__ == "__main__":
    main()
