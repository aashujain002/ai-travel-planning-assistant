from pathlib import Path

from bs4 import BeautifulSoup, Tag

from inspect_visit_singapore import CONTENT_SELECTOR


RAW_HTML_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "raw"
    / "visit_singapore_plan.html"
)
TEXT_PREVIEW_LENGTH = 250


def first_heading(block: Tag) -> str | None:
    heading = block.find(["h1", "h2", "h3"])
    return heading.get_text(" ", strip=True) if heading else None


def main() -> None:
    soup = BeautifulSoup(RAW_HTML_PATH.read_text(encoding="utf-8"), "html.parser")
    content = soup.select_one(CONTENT_SELECTOR)
    if content is None:
        raise RuntimeError("Could not find the Visit Singapore content container.")

    grid = content.find("div", class_="aem-Grid", recursive=False)
    if grid is None:
        raise RuntimeError("Could not find the Visit Singapore component grid.")

    blocks = [
        block
        for block in grid.find_all(recursive=False)
        if isinstance(block, Tag) and block.get_text(" ", strip=True)
    ]

    print(f"Meaningful direct content blocks: {len(blocks)}")
    for index, block in enumerate(blocks[:20], start=1):
        print(f"\nBlock {index}")
        print("-" * 16)
        print(f"tag: {block.name}")
        print(f"classes: {block.get('class')}")
        print(f"heading: {first_heading(block)}")
        print(f"text preview: {block.get_text(' ', strip=True)[:TEXT_PREVIEW_LENGTH]}")


if __name__ == "__main__":
    main()
