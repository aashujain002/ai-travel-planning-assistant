import json
from html import unescape
from typing import TypedDict
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, Tag


SELECTED_ITINERARIES = {
    "4 Days in Singapore": (
        "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/"
        "itineraries/4-days-in-singapore/"
    ),
    "Enjoy Singapore in 7 Days": (
        "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/"
        "itineraries/7-days-in-singapore/"
    ),
    "Family Getaway in Singapore": (
        "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/"
        "itineraries/places-to-visit-with-family/"
    ),
}
CONTENT_SELECTOR = (
    ".container.stb-template > .root.responsivegrid > .aem-Grid"
    " > .responsivegrid"
)


class ItineraryActivity(TypedDict):
    title: str
    description: str
    time_of_day: str | None


class ItinerarySection(TypedDict):
    itinerary: str
    section: str
    text: str
    activities: list[ItineraryActivity]


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def component_data(component: Tag) -> dict:
    return json.loads(component["aem-data"])


def text_from_html(html: str) -> str:
    return BeautifulSoup(unescape(html), "html.parser").get_text(" ", strip=True)


def format_activity(activity: ItineraryActivity) -> str:
    parts = [activity["title"], activity["description"]]
    text = " ".join(part for part in parts if part)
    return (
        f"{activity['time_of_day'].title()}: {text}"
        if activity["time_of_day"]
        else text
    )


def activity_from_tile(
    tile: dict,
    title_key: str,
    time_of_day_key: str | None = None,
) -> ItineraryActivity:
    title = str(tile.get(title_key, "")).strip()
    description_html = str(tile.get("tileDescription_t", ""))
    description = text_from_html(description_html)
    time_of_day = (
        str(tile.get(time_of_day_key, "")).strip() if time_of_day_key else None
    )

    if not title:
        raise RuntimeError("Itinerary activity is missing a title.")
    if description_html and not description:
        raise RuntimeError(f"Itinerary activity '{title}' has an empty description.")

    return {
        "title": title,
        "description": description,
        "time_of_day": time_of_day or None,
    }


def section_from_activities(
    itinerary_name: str,
    section_name: str,
    activities: list[ItineraryActivity],
) -> ItinerarySection:
    if not section_name:
        raise RuntimeError("Itinerary component is missing a section heading.")
    if not activities:
        raise RuntimeError(f"Itinerary section '{section_name}' has no activities.")

    return {
        "itinerary": itinerary_name,
        "section": section_name,
        "text": "\n\n".join(format_activity(activity) for activity in activities),
        "activities": activities,
    }


def parse_things_to_do_component(
    component: Tag,
    itinerary_name: str,
) -> ItinerarySection:
    data = component_data(component)
    activities = [
        activity_from_tile(
            tile,
            title_key="tileTitle_t",
            time_of_day_key="tilePillCategory",
        )
        for tile in data.get("tiles", [])
    ]
    return section_from_activities(
        itinerary_name,
        str(data.get("header_t", "")).strip(),
        activities,
    )


def parse_title_with_slider_component(
    component: Tag,
    itinerary_name: str,
) -> ItinerarySection:
    data = component_data(component)
    activities = [
        activity_from_tile(tile, title_key="tileHeader_t")
        for tile in data.get("tilesList", [])
    ]
    return section_from_activities(
        itinerary_name,
        str(data.get("heading_t", "")).strip(),
        activities,
    )


def parse_itinerary(url: str, itinerary_name: str) -> list[ItinerarySection]:
    soup = BeautifulSoup(fetch_html(url), "html.parser")
    content = soup.select_one(CONTENT_SELECTOR)
    if content is None:
        raise RuntimeError(f"Could not find the content container for {itinerary_name}.")

    introduction_component = content.find("stb-image-video-text")
    if introduction_component is None:
        raise RuntimeError(f"Could not find the introduction for {itinerary_name}.")

    introduction = component_data(introduction_component)
    introduction_text = text_from_html(introduction.get("description_t", ""))
    if not introduction_text:
        raise RuntimeError(f"Introduction for {itinerary_name} is empty.")

    sections = [
        {
            "itinerary": itinerary_name,
            "section": "Introduction",
            "text": introduction_text,
            "activities": [],
        }
    ]

    for component in content.find_all(
        ["stb-things-to-do", "stb-title-with-slider"]
    ):
        if component.name == "stb-things-to-do":
            sections.append(parse_things_to_do_component(component, itinerary_name))
            continue

        if component_data(component).get("heading_t", "").strip().startswith("Day"):
            sections.append(
                parse_title_with_slider_component(component, itinerary_name)
            )

    return sections


def parse_selected_itineraries() -> dict[str, list[ItinerarySection]]:
    return {
        name: parse_itinerary(url, name)
        for name, url in SELECTED_ITINERARIES.items()
    }


def main() -> None:
    itineraries = parse_selected_itineraries()

    print("| Itinerary | Sections | Activity count |")
    print("| --- | ---: | ---: |")
    for itinerary_name, sections in itineraries.items():
        activities = [
            activity for section in sections for activity in section["activities"]
        ]
        if any(not activity["title"] for activity in activities):
            raise RuntimeError(f"{itinerary_name} contains an activity without a title.")
        print(f"| {itinerary_name} | {len(sections)} | {len(activities)} |")
        print(f"First activity: {activities[0]}")


if __name__ == "__main__":
    main()
