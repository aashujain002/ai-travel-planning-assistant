from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from vector_store import load_vector_store


TOP_K = 4
CHAT_MODEL = "gpt-4o-mini"
TEST_QUESTION = "What will the weather in Singapore be tomorrow?"

SYSTEM_INSTRUCTIONS = """You are a Singapore travel-planning assistant.
Use only the retrieved context for factual claims about Singapore. Do not invent
unsupported facts. If the context is insufficient, say so clearly. Distinguish
factual information from recommendations. Cite every factual statement with its
source title and URL, using the provenance supplied in the context."""


def document_context(document: Document) -> str:
    metadata = document.metadata
    section = metadata.get("section") or metadata.get("Header 3") or metadata.get(
        "Header 2", ""
    )
    itinerary = metadata.get("itinerary")

    lines = [
        f"SOURCE: {metadata['source']}",
        f"URL: {metadata['url']}",
        f"TOPIC: {metadata['topic']}",
    ]
    if itinerary:
        lines.append(f"ITINERARY: {itinerary}")
    if section:
        lines.append(f"SECTION: {section}")
    lines.extend(["", "CONTENT:", document.page_content])
    return "\n".join(lines)


def retrieve_documents(question: str) -> list[Document]:
    """Retrieve the most relevant Singapore travel documents for a question."""
    vector_store = load_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": TOP_K})
    return retriever.invoke(question)


def answer_question(question: str) -> str:
    context = "\n\n---\n\n".join(
        document_context(document) for document in retrieve_documents(question)
    )

    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_INSTRUCTIONS),
            HumanMessage(
                content=f"Retrieved context:\n\n{context}\n\nUser question: {question}"
            ),
        ]
    )
    return response.content


def main() -> None:
    print(f"Question: {TEST_QUESTION}\n")
    print(answer_question(TEST_QUESTION))


if __name__ == "__main__":
    main()
