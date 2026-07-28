"""
Webscorer -- genuine public JSON API per-race.
Docs: https://www.webscorer.com/blog/post/2021/09/28/how-to-access-race-data-via-json-api

Endpoint shape: https://www.webscorer.com/json/race?raceid=<id>&apiid=<id>

CAVEAT (important): this endpoint is per-race, not a calendar search --
there's no documented "list all upcoming races for organizer X" endpoint.
That means this scraper can only refresh KNOWN race IDs, not discover new
ones automatically. Practical options:
  1. Maintain a small manually-updated RACE_IDS list below (find IDs from
     each org's Webscorer results page URL) and refresh a few times a
     season when new races are announced.
  2. Pair this with generic_date_scraper.py against the org's own site
     (3CX, B-17, Crusher Cup all have their own pages) to discover new
     race announcements, then add the resulting Webscorer race ID here
     once it exists.
This is a real limitation of Webscorer's API, not a bug in this script.
"""

from ..common.fetch import get_json
from ..common.models import Event

BASE = "https://www.webscorer.com/json/race"

# Fill in as races are discovered -- see module docstring for why this
# can't be auto-discovered via the API alone.
RACE_IDS: dict[str, str] = {
    # "series_label": "raceid",
}


def scrape() -> list[dict]:
    events = []
    for series, race_id in RACE_IDS.items():
        try:
            data = get_json(BASE, params={"raceid": race_id})
        except Exception as exc:
            print(f"[webscorer_scraper] raceid={race_id} failed: {exc}")
            continue

        events.append(Event(
            series=series,
            name=data.get("raceName", "Unknown race"),
            start_date=str(data.get("raceDate", ""))[:10],
            venue=data.get("location"),
            url=f"https://www.webscorer.com/race?raceid={race_id}",
            source="webscorer_scraper",
            tier="api",
            raw=data,
        ).to_dict())
    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape(), indent=2))
