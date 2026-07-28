"""
USA Cycling scraper -- REQUIRES PLAYWRIGHT (confirmed: usacycling.org/events
returns only nav links with a plain fetch; the actual event search is a
Sport80 embed loaded client-side).

STATUS: unfinished stub, same situation as uci_scraper.py -- structure
confirmed to need JS, exact selectors not yet confirmed against live DOM.

WORTH CHECKING FIRST: Sport80 is used by other federations too, and some
Sport80 deployments expose a documented public API (it's used widely enough
in endurance sports that this is plausible but NOT confirmed for USA
Cycling specifically). Before investing in Playwright + selector
maintenance here, it's worth 10 minutes checking the browser Network tab
while using the live event search for an XHR call to something like
`*.sport80.com/api/...` -- if that exists and returns JSON, it's a much
better long-term source than parsing rendered HTML.
"""

from bs4 import BeautifulSoup

from ..common.browser import get_rendered_html
from ..common.models import Event

URL = "https://usacycling.org/events"

# PLACEHOLDER -- confirm against live rendered DOM
EVENT_ROW_SELECTOR = ".sport80-event-row"  # almost certainly wrong; placeholder only


def scrape() -> list[dict]:
    try:
        html = get_rendered_html(URL, wait_selector=EVENT_ROW_SELECTOR, timeout_ms=30_000)
    except Exception as exc:
        print(f"[usacycling_scraper] failed (selector needs updating): {exc}")
        return []

    soup = BeautifulSoup(html, "html.parser")
    events = []
    for row in soup.select(EVENT_ROW_SELECTOR):
        text = row.get_text(separator=" | ", strip=True)
        events.append(Event(
            series="USA Cycling",
            name=text,  # TODO: split fields once selector confirmed
            start_date="",  # TODO
            url=URL,
            source="usacycling_scraper",
            tier="playwright",
            raw={"needs_selector_fix": True},
        ).to_dict())
    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape(), indent=2))
