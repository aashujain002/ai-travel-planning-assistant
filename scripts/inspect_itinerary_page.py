import json
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, Tag


ITINERARY_PAGES = {
    "4 Days": (
        "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/"
        "itineraries/4-days-in-singapore/"
    ),
    "7 Days": (
        "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/"
        "itineraries/7-days-in-singapore/"
    ),
    "Family Getaway": (
        "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/"
        "itineraries/places-to-visit-with-family/"
    ),
}
CONTENT_SELECTOR = (
    ".container.stb-template > .root.responsivegrid > .aem-Grid"
    " > .responsivegrid"
)


def fetch_html(url: str) -> tuple[str, str, int]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8"), response.geturl(), response.status


def component_data(component: Tag) -> dict:
    return json.loads(component["aem-data"])


def inspect_page(label: str, url: str) -> None:
    html, final_url, status = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    content = soup.select_one(CONTENT_SELECTOR)
    if content is None:
        raise RuntimeError(f"Could not find the {label} content container.")

    intro_components = content.find_all("stb-image-video-text")
    day_components = content.find_all("stb-things-to-do")
    slider_components = [
        component
        for component in content.find_all("stb-title-with-slider")
        if component_data(component).get("heading_t", "").strip().startswith("Day")
    ]
    day_data = [component_data(component) for component in day_components]
    slider_data = [component_data(component) for component in slider_components]

    print(f"\n{label}")
    print("-" * 16)
    print(f"HTTP status: {status}")
    print(f"Page URL: {final_url}")
    print(f"HTML title: {soup.title.get_text(' ', strip=True)}")
    print(f"Introduction component present: {bool(intro_components)}")
    if intro_components:
        print(f"Introduction title: {component_data(intro_components[0]).get('title_t')}")
    print(f"stb-things-to-do count: {len(day_components)}")
    print(f"Day slider component count: {len(slider_components)}")
    print("Sections:")
    for day in day_data:
        print(f"- {day.get('header_t')} ({len(day.get('tiles', []))} tiles)")
    for slider in slider_data:
        print(
            f"- {slider.get('heading_t').strip()} "
            f"({len(slider.get('tilesList', []))} tiles)"
        )


def main() -> None:
    for label, url in ITINERARY_PAGES.items():
        inspect_page(label, url)


if __name__ == "__main__":
    main()
