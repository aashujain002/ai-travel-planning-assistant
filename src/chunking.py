from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from document_builder import sections_to_documents
from ingestion import clean_wikivoyage_html
from section_parser import parse_sections


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
RAW_HTML_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "wikivoyage_singapore.html"
)


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)


def main() -> None:
    raw_html = RAW_HTML_PATH.read_text(encoding="utf-8")
    documents = sections_to_documents(parse_sections(clean_wikivoyage_html(raw_html)))
    chunks = split_documents(documents)

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
