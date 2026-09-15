from pathlib import Path

from bs4 import BeautifulSoup, Comment
from langchain_text_splitters import HTMLHeaderTextSplitter


RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
WIKIVOYAGE_SOURCE = RAW_DATA_DIR / "wikivoyage_singapore.html"
PREVIEW_LENGTH = 300
PREVIEW_DOCUMENT_COUNT = 10
CLEANED_TEXT_PREVIEW_LENGTH = 500
NOISE_TERMS = ("Main menu", "Navigation", "Mapnik", "Leaflet")


def clean_wikivoyage_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("#mw-content-text .mw-parser-output")

    if article is None:
        raise RuntimeError("Could not find the Wikivoyage article body.")

    page_title = soup.select_one("#firstHeading")
    if page_title is not None and page_title.get_text(strip=True):
        article.insert(0, page_title.extract())
    else:
        title_metadata = soup.select_one("meta[property='og:title']")
        if title_metadata is not None and title_metadata.get("content"):
            page_title = soup.new_tag("h1")
            page_title.string = title_metadata["content"].split(" – ", 1)[0]
            article.insert(0, page_title)

    for comment in article.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    for selector in (
        "script",
        "style",
        "#toc",
        ".toc",
        ".vector-toc",
        ".vector-menu",
        ".mw-editsection",
        "sup.reference",
        ".reference",
        ".mw-kartographer-container",
        ".mw-kartographer-map",
        ".leaflet-control",
    ):
        for element in article.select(selector):
            element.decompose()

    return str(article)


def main() -> None:
    original_html = WIKIVOYAGE_SOURCE.read_text(encoding="utf-8")
    cleaned_html = clean_wikivoyage_html(original_html)
    cleaned_text = BeautifulSoup(cleaned_html, "html.parser").get_text(
        " ", strip=True
    )

    print(f"Original HTML length: {len(original_html)}")
    print(f"Cleaned HTML length: {len(cleaned_html)}")
    print("\nCleaned text preview:")
    print(cleaned_text[:CLEANED_TEXT_PREVIEW_LENGTH])
    print("\nNoise terms remaining in cleaned text:")
    for term in NOISE_TERMS:
        print(f"{term}: {term.casefold() in cleaned_text.casefold()}")

    splitter = HTMLHeaderTextSplitter(
        headers_to_split_on=[
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ],
    )
    documents = splitter.split_text(cleaned_html)

    if not documents:
        raise RuntimeError(f"No documents were loaded from {WIKIVOYAGE_SOURCE}.")

    print(f"Number of Documents: {len(documents)}")

    for index, document in enumerate(documents[:PREVIEW_DOCUMENT_COUNT], start=1):
        print(f"\nDocument {index}:")
        print("-" * 16)
        print(f"metadata: {document.metadata}")
        print(f"content preview: {document.page_content[:PREVIEW_LENGTH]}")


if __name__ == "__main__":
    main()