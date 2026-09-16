from _paths import add_source_directory

add_source_directory()

from activity_retrieval import ACTIVITY_TOPICS
from vector_store import load_vector_store


INDOOR_QUERY = "indoor activities in Singapore things to do when it rains"
TOP_K = 15
CONTENT_PREVIEW_LENGTH = 800


def main() -> None:
    vector_store = load_vector_store()
    documents = vector_store.similarity_search(
        INDOOR_QUERY,
        k=TOP_K,
        filter={"topic": {"$in": list(ACTIVITY_TOPICS)}},
    )

    print(f"Question: {INDOOR_QUERY}")
    for rank, document in enumerate(documents, start=1):
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
        print(f"   Section: {section}")
        print(f"   Preview: {preview}")


if __name__ == "__main__":
    main()
