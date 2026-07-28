"""
BikeReg -- genuine public JSON API, no key required for public event data.
Docs: https://www.bikereg.com/api/EventSearchDoc.aspx

Covers YBONC and anything else registered through BikeReg. Query by region
or keyword; there's also a GraphQL endpoint that's faster per BikeReg's own
docs, but the REST search below is simpler to start with and has the fuller
dataset per their notes.
"""

from ..common.fetch import get_json
from ..common.models import Event

API = "https://www.bikereg.com/api/search"

# BikeReg regions relevant to this project -- adjust/expand as needed.
# (Region names are BikeReg's own taxonomy; verify against
# bikereg.com's region filter dropdown if results look thin.)
REGIONS = ["Northern California", "Pacific Northwest"]


def scrape() -> list[dict]:
    events = []
    for region in REGIONS:
        try:
            data = get_json(API, params={"region": region})
        except Exception as exc:
            print(f"[bikereg_scraper] region={region} failed: {exc}")
            continue

        # BikeReg's response is a list of event dicts; field names per their
        # docs include Name, StartDate, EndDate, City, State, EventID.
        # Defensive .get() usage since this hasn't been run against live
        # data in this session -- confirm exact field names on first run
        # and adjust the .get() keys below if they differ.
        for item in data if isinstance(data, list) else data.get("Events", []):
            events.append(Event(
                series="BikeReg",
                name=item.get("Name", "Unknown event"),
                start_date=item.get("StartDate", "")[:10],
                end_date=(item.get("EndDate") or item.get("StartDate", ""))[:10],
                city=item.get("City"),
                venue=item.get("Venue"),
                url=f"https://www.bikereg.com/{item.get('EventID', '')}"
                    if item.get("EventID") else None,
                source="bikereg_scraper",
                tier="api",
                raw=item,
            ).to_dict())
    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape(), indent=2))
