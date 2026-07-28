"""
USA BMX scraper -- REQUIRES PLAYWRIGHT (confirmed JS-rendered, established
earlier in this project). STATUS: unfinished stub, selectors unconfirmed.

BETTER ALTERNATIVE, seriously consider before building this out: USA BMX
publishes its full annual National Series schedule as a plain news/blog
post each August (usabmx.com/news-and-media) -- that page IS static HTML
(confirmed readable via plain fetch earlier in this project) and covers the
exact same national-level data this Playwright scraper would produce, with
far less maintenance burden. Reserve Playwright effort here only if you
need the *local track* weekly schedules (e.g. Santa Clara PAL, Oak Creek),
which aren't in the news-post -- those still need the JS-rendered
usabmx.com/tracks/<id>/events/schedule pages.

TODO before relying on this in production:
  1. Confirm selectors against a live rendered track schedule page, e.g.
     usabmx.com/tracks/1031/events/schedule (Santa Clara PAL)
  2. This stub currently targets the national /events page as a placeholder
     -- redirect to per-track URLs once selectors are confirmed, since
     that's the actually-useful local data this tier is for.
"""

from bs4 import BeautifulSoup

from ..common.browser import get_rendered_html
from ..common.models import Event

# Local tracks worth polling directly (national schedule comes from the
# static news-post instead -- see docstring above)
TRACK_URLS = {
    "Santa Clara PAL BMX": "https://www.usabmx.com/tracks/1031/events/schedule",
    "Oak Creek BMX": "https://www.usabmx.com/tracks/find-tracks",  # TODO: swap for Oak Creek's actual track ID
}

# PLACEHOLDER -- confirm against live rendered DOM
EVENT_ROW_SELECTOR = ".track-event-row"  # placeholder only


def scrape() -> list[dict]:
    events = []
    for track, url in TRACK_URLS.items():
        try:
            html = get_rendered_html(url, wait_selector=EVENT_ROW_SELECTOR, timeout_ms=30_000)
        except Exception as exc:
            print(f"[usabmx_scraper] {track} failed (selector needs updating): {exc}")
            continue

        soup = BeautifulSoup(html, "html.parser")
        for row in soup.select(EVENT_ROW_SELECTOR):
            text = row.get_text(separator=" | ", strip=True)
            events.append(Event(
                series="USA BMX (local track)",
                name=f"{track}: {text}",
                start_date="",  # TODO
                venue=track,
                url=url,
                source="usabmx_scraper",
                tier="playwright",
                raw={"needs_selector_fix": True},
            ).to_dict())
    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape(), indent=2))
