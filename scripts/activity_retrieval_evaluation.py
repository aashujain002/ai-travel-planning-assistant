from langchain_core.documents import Document

from _paths import add_source_directory

add_source_directory()

from vector_store import load_vector_store


EVALUATION_TOP_K = 10
ACTIVITY_TOPICS = ("activities", "attractions", "food_and_local_experiences")
CONTENT_PREVIEW_LENGTH = 250
EVALUATION_QUERIES = (
    "What are outdoor activities in Singapore?",
    "What are indoor activities in Singapore?",
    "What are cultural activities in Singapore?",
    "What food experiences can I have in Singapore?",
    "What activities are suitable for a 3-day Singapore trip?",
)


def print_document(rank: int, document: Document) -> None:
    """Print the metadata and a short preview for an activity retrieval result."""
    metadata = document.metadata
    section = (
        metadata.get("section")
        or metadata.get("Header 3")
        or metadata.get("Header 2")
        or "Not specified"
    )
    preview = " ".join(document.page_content.split())[:CONTENT_PREVIEW_LENGTH]

    print(f"\n{rank}. Source: {metadata.get('source', 'Unknown source')}")
    print(f"   Topic: {metadata.get('topic', 'Not specified')}")
    print(f"   Itinerary: {metadata.get('itinerary', 'Not specified')}")
    print(f"   Section: {section}")
    print(f"   Day number: {metadata.get('day_number', 'Not specified')}")
    print(f"   Preview: {preview}")


def main() -> None:
    vector_store = load_vector_store()
    for query in EVALUATION_QUERIES:
        documents = vector_store.similarity_search(
            query,
            k=EVALUATION_TOP_K,
            filter={"topic": {"$in": list(ACTIVITY_TOPICS)}},
        )
        print(f"\nQuestion: {query}")
        for rank, document in enumerate(documents, start=1):
            print_document(rank, document)
        print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
