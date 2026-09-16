import json
from html import unescape
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, Tag


HUB_URL = "https://www.visitsingapore.com/singapore-itineraries/"
CONTENT_SELECTOR = (
    ".container.stb-template > .root.responsivegrid > .aem-Grid"
    " > .responsivegrid"
)
SELECTED_ITINERARIES = (
    "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/"
    "itineraries/4-days-in-singapore/",
    "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/"
    "itineraries/7-days-in-singapore/",
    "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/"
    "itineraries/places-to-visit-with-family/",
)


def fetch_html(url: str) -> tuple[str, str, int]:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        return (
            response.read().decode("utf-8"),
            response.geturl(),
            response.status,
        )


def text_from_html(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def itinerary_cards(soup: BeautifulSoup) -> list[dict[str, str]]:
    cards = []

    for component in soup.find_all(attrs={"aem-data": True}):
        try:
            data = json.loads(component["aem-data"])
        except json.JSONDecodeError:
            continue

        if data.get("title_t") and data.get("ctaUrl"):
            cards.append(
                {
                    "title": data["title_t"],
                    "description": text_from_html(data.get("description_t", "")),
                    "url": data["ctaUrl"],
                }
            )

        for tile in data.get("tilesList", []):
            if tile.get("tileHeader_t") and tile.get("tileCTAUrl"):
                cards.append(
                    {
                        "title": tile["tileHeader_t"],
                        "description": text_from_html(
                            unescape(tile.get("tileDescription_t", ""))
                        ),
                        "url": tile["tileCTAUrl"],
                    }
                )

    return cards


def describe_element(element: Tag) -> str:
    identifier = f"#{element['id']}" if element.get("id") else ""
    classes = "".join(f".{class_name}" for class_name in element.get("class", []))
    return f"<{element.name}{identifier}{classes}>"


def main() -> None:
    hub_html, final_url, status = fetch_html(HUB_URL)
    soup = BeautifulSoup(hub_html, "html.parser")
    content = soup.select_one(CONTENT_SELECTOR)
    if content is None:
        raise RuntimeError("Could not find the itinerary hub content container.")

    cards = itinerary_cards(soup)
    print(f"Hub status: accessible (HTTP {status})")
    print(f"Hub URL: {final_url}")
    print(f"HTML title: {soup.title.get_text(' ', strip=True)}")
    print(f"Main content container: {describe_element(content)}")
    print(f"Number of itinerary cards: {len(cards)}")
    print("First 10 itinerary options:")
    for card in cards[:10]:
        print(f"- {card['title']}: {card['description']}")

    print(f"Useful descriptive text present: {any(card['description'] for card in cards)}")
    print("\nSelected itinerary pages:")
    for url in SELECTED_ITINERARIES:
        page_html, page_url, page_status = fetch_html(url)
        page_soup = BeautifulSoup(page_html, "html.parser")
        print(f"- accessible (HTTP {page_status}): {page_url}")
        print(f"  title: {page_soup.title.get_text(' ', strip=True)}")


if __name__ == "__main__":
    main()
