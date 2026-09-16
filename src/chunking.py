from collections import Counter

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from document_builder import load_all_documents


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)


def main() -> None:
    documents = load_all_documents()
    chunks = split_documents(documents)

    source_counts = Counter(document.metadata["source"] for document in documents)
    cbd_document = next(
        document
        for document in documents
        if document.metadata.get("Header 3") == "Singapore CBD"
    )
    cbd_chunks = [
        chunk
        for chunk in chunks
        if chunk.page_content == cbd_document.page_content
        and chunk.metadata == cbd_document.metadata
    ]

    local_delicacies_document = next(
        document
        for document in documents
        if document.metadata.get("Header 2") == "Eat"
        and document.metadata.get("Header 3") == "Local delicacies"
    )
    local_delicacies_chunks = [
        chunk
        for chunk in chunks
        if chunk.metadata == local_delicacies_document.metadata
    ]

    print(f"Before chunking: {len(documents)} Documents")
    print("Documents by source:")
    for source, count in source_counts.items():
        print(f"- {source}: {count}")
    print(f"After chunking: {len(chunks)} chunks")
    print("\nSingapore CBD section:")
    print(f"number of chunks: {len(cbd_chunks)}")
    print(f"chunk length: {len(cbd_chunks[0].page_content)}")

    print("\nEat > Local delicacies section:")
    print(f"original length: {len(local_delicacies_document.page_content)}")
    print(f"number of chunks: {len(local_delicacies_chunks)}")
    print(
        "first 3 chunk lengths: "
        f"{[len(chunk.page_content) for chunk in local_delicacies_chunks[:3]]}"
    )

    print("\nFirst 3 Local delicacies chunks:")
    for index, chunk in enumerate(local_delicacies_chunks[:3], start=1):
        print(f"\nchunk number: {index}")
        print(f"character length: {len(chunk.page_content)}")
        print(f"topic: {chunk.metadata['topic']}")
        print(f"Header 2: {chunk.metadata.get('Header 2')}")
        print(f"Header 3: {chunk.metadata.get('Header 3')}")
        print(f"content preview: {chunk.page_content[:200]}")

    print("\nExample chunk metadata:")
    print(local_delicacies_chunks[0].metadata)


if __name__ == "__main__":
    main()
