import re
from pathlib import Path
from typing import TypedDict

from bs4 import BeautifulSoup

from ingestion import clean_wikivoyage_html


RAW_HTML_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "wikivoyage_singapore.html"
)
HEADER_TAGS = ("h1", "h2", "h3")
TEXT_TAGS = ("p", "li", "dt", "dd")
INLINE_LINK_TEST_HTML = """
<article>
  <h1>Singapore</h1>
  <p>
    Singapore is a <a href="/huge-city">huge city</a> with several
    <a href="/districts">district</a> articles in
    <a href="/southeast-asia">Southeast Asia</a>.
  </p>
</article>
"""


class ParsedSection(TypedDict):
    headers: dict[str, str]
    text: str


def text_from(element) -> str:
    text = element.get_text(" ", strip=True)
    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def parse_sections(html: str) -> list[ParsedSection]:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("#mw-content-text .mw-parser-output")
    article = article or soup.select_one(".mw-parser-output") or soup

    sections: list[ParsedSection] = []
    headers: dict[str, str] = {}
    text_parts: list[str] = []

    def add_section() -> None:
        text = "\n".join(text_parts).strip()
        if headers and text:
            sections.append({"headers": headers.copy(), "text": text})

    for element in article.find_all([*HEADER_TAGS, *TEXT_TAGS]):
        if element.name in HEADER_TAGS:
            add_section()
            text_parts = []
            heading = text_from(element)

            if element.name == "h1":
                headers = {"Header 1": heading}
            elif element.name == "h2":
                headers.pop("Header 3", None)
                headers["Header 2"] = heading
            else:
                headers["Header 3"] = heading
            continue

        if element.find_parent(TEXT_TAGS) is not None:
            continue

        text = text_from(element)
        if text:
            text_parts.append(text)

    add_section()
    return sections


def assert_inline_text_order() -> str:
    test_sections = parse_sections(INLINE_LINK_TEST_HTML)
    expected_text = (
        "Singapore is a huge city with several district articles in Southeast Asia."
    )

    if test_sections[0]["text"] != expected_text:
        raise AssertionError(f"Inline text order was not preserved: {test_sections}")

    return test_sections[0]["text"]


def main() -> None:
    raw_html = RAW_HTML_PATH.read_text(encoding="utf-8")
    sections = parse_sections(clean_wikivoyage_html(raw_html))

    print(f"Number of sections: {len(sections)}")
    for index, section in enumerate(sections[:5], start=1):
        print(f"\nSection {index}:")
        print(f"headers: {section['headers']}")
        print(f"text: {section['text']}")

    print("\nInline-link text test:")
    print(assert_inline_text_order())

    cbd_section = next(
        section
        for section in sections
        if section["headers"].get("Header 3") == "Singapore CBD"
    )
    print("\nSingapore CBD hierarchy:")
    print(cbd_section["headers"])


if __name__ == "__main__":
    main()
