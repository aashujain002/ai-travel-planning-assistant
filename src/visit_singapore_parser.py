import re
from pathlib import Path
from typing import TypedDict

from bs4 import BeautifulSoup, Tag


RAW_HTML_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "visit_singapore_plan.html"
)
CONTENT_SELECTOR = (
    ".container.stb-template > .root.responsivegrid > .aem-Grid"
    " > .responsivegrid"
)
CTA_LABELS = {
    "find out more",
    "find out more requirements",
    "use a fare calculator",
    "get a mrt map",
    "view all",
}


class VisitSingaporeSection(TypedDict):
    section: str
    text: str


def text_from(element: Tag) -> str:
    text = element.get_text(" ", strip=True)
    return re.sub(r"\s+([,.;:!?])", r"\1", text)


def is_cta(element: Tag) -> bool:
    label = element.get_text(" ", strip=True).casefold()
    classes = element.get("class", [])
    return label in CTA_LABELS or any(class_name.startswith("_cta_") for class_name in classes)


def parse_visit_singapore(html: str) -> list[VisitSingaporeSection]:
    soup = BeautifulSoup(html, "html.parser")
    content = soup.select_one(CONTENT_SELECTOR)
    if content is None:
        raise RuntimeError("Could not find the Visit Singapore content container.")

    grid = content.find("div", class_="aem-Grid", recursive=False)
    if grid is None:
        raise RuntimeError("Could not find the Visit Singapore component grid.")

    sections = []
    for block in grid.find_all(recursive=False):
        if not isinstance(block, Tag) or "containerComponent" not in block.get("class", []):
            continue

        for link_or_button in block.find_all(["a", "button"]):
            if is_cta(link_or_button):
                link_or_button.decompose()

        heading = block.find(["h1", "h2", "h3", "h4"])
        section_name = text_from(heading) if heading else None
        if heading is not None:
            heading.extract()

        text = text_from(block)
        if section_name and text:
            sections.append({"section": section_name, "text": text})

    return sections


def main() -> None:
    sections = parse_visit_singapore(RAW_HTML_PATH.read_text(encoding="utf-8"))

    print(f"Number of parsed sections: {len(sections)}")
    for index, section in enumerate(sections, start=1):
        print(f"\nSection {index}")
        print("-" * 16)
        print(f"section: {section['section']}")
        print(f"text: {section['text']}")

    parsed_content = "\n".join(section["text"] for section in sections).casefold()
    print("\nCTA labels remaining:")
    print(f"Find out more: {'find out more' in parsed_content}")
    print(f"View All: {'view all' in parsed_content}")


if __name__ == "__main__":
    main()
