from langchain_core.documents import Document

from _paths import add_source_directory

add_source_directory()

from vector_store import load_vector_store


QUERIES = (
    "What is the best way to get around Singapore?",
    "What local foods should I try in Singapore?",
    "What could I do during a 4-day trip to Singapore?",
)
TOP_K = 4
CONTENT_PREVIEW_LENGTH = 300


def print_result(index: int, document: Document) -> None:
    metadata = document.metadata
    print(f"\nResult {index}")
    print(f"Source: {metadata['source']}")
    print(f"URL: {metadata['url']}")
    print(f"Topic: {metadata['topic']}")
    if metadata.get("itinerary"):
        print(f"Itinerary: {metadata['itinerary']}")
    if metadata.get("section"):
        print(f"Section: {metadata['section']}")
    if metadata.get("Header 2"):
        print(f"Header 2: {metadata['Header 2']}")
    if metadata.get("Header 3"):
        print(f"Header 3: {metadata['Header 3']}")
    print(f"Content: {document.page_content[:CONTENT_PREVIEW_LENGTH]}")


def main() -> None:
    vector_store = load_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K})

    for query in QUERIES:
        print(f"\nQuery: {query}")
        documents = retriever.invoke(query)
        for index, document in enumerate(documents, start=1):
            print_result(index, document)


if __name__ == "__main__":
    main()
