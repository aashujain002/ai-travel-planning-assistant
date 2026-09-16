from pathlib import Path

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


def describe_element(element: Tag) -> str:
    identifier = f"#{element['id']}" if element.get("id") else ""
    classes = "".join(f".{class_name}" for class_name in element.get("class", []))
    return f"<{element.name}{identifier}{classes}>"


def main() -> None:
    soup = BeautifulSoup(RAW_HTML_PATH.read_text(encoding="utf-8"), "html.parser")
    content = soup.select_one(CONTENT_SELECTOR)

    if content is None:
        raise RuntimeError("Could not find the Visit Singapore content container.")

    headings = [
        heading.get_text(" ", strip=True)
        for heading in content.select("h1, h2, h3")
        if heading.get_text(" ", strip=True)
    ]

    print(f"HTML title: {soup.title.get_text(' ', strip=True)}")
    print(f"Main content container: {describe_element(content)}")
    print(f"Number of headings: {len(headings)}")
    print("First 5 headings:")
    for heading in headings[:5]:
        print(f"- {heading}")
    print("\nMain content preview:")
    print(content.get_text(" ", strip=True)[:500])


if __name__ == "__main__":
    main()
