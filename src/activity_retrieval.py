from langchain_core.documents import Document

from vector_store import load_vector_store


ACTIVITY_TOPICS = (
    "activities",
    "attractions",
    "food_and_local_experiences",
)
ACTIVITY_TOP_K = 8
CONTENT_PREVIEW_LENGTH = 250
TEST_QUERIES = (
    "What are outdoor activities in Singapore?",
    "What are indoor activities in Singapore?",
    "What activities are suitable for a 3-day Singapore trip?",
)


def _build_activity_query(question: str) -> str:
    """Enrich an activity request while retaining its original semantic intent."""
    normalized_question = question.casefold()
    intent_hints = []
    if any(
        term in normalized_question
        for term in ("outdoor", "park", "walk", "nature", "beach", "water")
    ):
        intent_hints.append(
            "Prioritize outdoor recreation, parks, walks, nature, beaches, and "
            "water activities."
        )
    if any(term in normalized_question for term in ("indoor", "rain", "rainy")):
        intent_hints.append(
            "Prioritize indoor and rain-friendly attractions such as performing "
            "arts, cinemas, shopping, cultural venues, and indoor recreation."
        )
    if not intent_hints:
        intent_hints.append(
            "Prioritize Singapore attractions, outdoor and indoor activities, "
            "cultural experiences, food, and local experiences."
        )

    return (
        f"{question}\n\n"
        + "\n".join(intent_hints)
    )


def retrieve_activity_documents(question: str) -> list[Document]:
    """Return activity-oriented documents using semantic search and topic filtering."""
    vector_store = load_vector_store()
    return vector_store.similarity_search(
        _build_activity_query(question),
        k=ACTIVITY_TOP_K,
        filter={"topic": {"$in": list(ACTIVITY_TOPICS)}},
    )


if __name__ == "__main__":
    for query in TEST_QUERIES:
        print(f"\nQuestion: {query}")
        for rank, document in enumerate(retrieve_activity_documents(query), start=1):
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
