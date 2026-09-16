from langchain_core.documents import Document

from _paths import add_source_directory

add_source_directory()

from vector_store import load_vector_store


EVALUATION_TOP_K = 5
CONTENT_PREVIEW_LENGTH = 250
EVALUATION_QUERIES = (
    "What are the main neighbourhoods in Singapore?",
    "What local foods should I try in Singapore?",
    "What can I do outdoors in Singapore?",
    "What can I do indoors in Singapore?",
    "What could I do during a 4-day trip to Singapore?",
    "Plan a 3-day Singapore itinerary based on the available itinerary guidance.",
)


def print_document(rank: int, document: Document) -> None:
    """Print the provenance and a short preview for an evaluation result."""
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
    print(f"   Preview: {preview}")


def main() -> None:
    vector_store = load_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": EVALUATION_TOP_K})

    for query in EVALUATION_QUERIES:
        print(f"\nQuestion: {query}")
        for rank, document in enumerate(retriever.invoke(query), start=1):
            print_document(rank, document)
        print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
