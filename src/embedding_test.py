import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

from chunking import split_documents
from document_builder import sections_to_documents
from ingestion import clean_wikivoyage_html
from section_parser import parse_sections


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_HTML_PATH = PROJECT_ROOT / "data" / "raw" / "wikivoyage_singapore.html"


def load_wikivoyage_chunks():
    raw_html = RAW_HTML_PATH.read_text(encoding="utf-8")
    documents = sections_to_documents(parse_sections(clean_wikivoyage_html(raw_html)))
    return split_documents(documents)


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Add it to the project's .env file."
        )

    chunks = load_wikivoyage_chunks()
    selected_chunk = next(
        chunk
        for chunk in chunks
        if chunk.metadata.get("Header 2") == "Get around"
    )

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector = embeddings.embed_query(selected_chunk.page_content)

    print("Selected chunk:")
    print(f"topic: {selected_chunk.metadata['topic']}")
    print(f"Header 2: {selected_chunk.metadata.get('Header 2')}")
    print(f"Header 3: {selected_chunk.metadata.get('Header 3')}")
    print(f"Embedding dimension: {len(vector)}")
    print(f"First 10 values: {vector[:10]}")
    print("Embedding operation: embed_query")


if __name__ == "__main__":
    main()
