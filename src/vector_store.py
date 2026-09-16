import hashlib
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from chunking import split_documents
from document_builder import load_all_documents


PROJECT_ROOT = Path(__file__).resolve().parent.parent
VECTOR_STORE_DIRECTORY = PROJECT_ROOT / "data" / "vectorstore"
COLLECTION_NAME = "singapore_travel_knowledge"
EMBEDDING_MODEL = "text-embedding-3-small"


def chunk_ids(chunks: list[Document]) -> list[str]:
    return [
        hashlib.sha256(
            json.dumps(
                {
                    "page_content": chunk.page_content,
                    "metadata": chunk.metadata,
                    "position": position,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        for position, chunk in enumerate(chunks)
    ]


def load_vector_store() -> Chroma:
    """Load the persistent Chroma store used by retrieval components."""
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Add it to the project's .env file."
        )
    if not VECTOR_STORE_DIRECTORY.exists():
        raise RuntimeError(
            f"Vector store directory does not exist: {VECTOR_STORE_DIRECTORY}"
        )

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTOR_STORE_DIRECTORY),
    )


def build_vector_store() -> Chroma:
    load_dotenv(PROJECT_ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Add it to the project's .env file."
        )

    print("Loading documents...")
    documents = load_all_documents()
    print(f"{len(documents)} documents loaded")

    chunks = split_documents(documents)
    print(f"{len(chunks)} chunks created")

    print("Creating embeddings...")
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    print("Building Chroma vector store...")
    VECTOR_STORE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        ids=chunk_ids(chunks),
        collection_name=COLLECTION_NAME,
        persist_directory=str(VECTOR_STORE_DIRECTORY),
    )
    print("Vector store created successfully")

    return vector_store


if __name__ == "__main__":
    build_vector_store()
