from pathlib import Path

from langchain_core.documents import Document

from ingestion import clean_wikivoyage_html
from section_parser import ParsedSection, parse_sections


RAW_HTML_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "wikivoyage_singapore.html"
)
SOURCE_NAME = "Wikivoyage Singapore Travel Guide"
SOURCE_URL = "https://en.wikivoyage.org/wiki/Singapore"
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


def main() -> None:
    raw_html = RAW_HTML_PATH.read_text(encoding="utf-8")
    sections = parse_sections(clean_wikivoyage_html(raw_html))
    documents = sections_to_documents(sections)

    for index, document in enumerate(documents[:5], start=1):
        print(f"\nDocument {index}:")
        print(f"page_content: {document.page_content}")
        print(f"metadata: {document.metadata}")


if __name__ == "__main__":
    main()
