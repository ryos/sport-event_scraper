"""
UCI scraper -- REQUIRES PLAYWRIGHT (confirmed: uci.org/discipline/... returns
only nav/footer chrome with a plain fetch; content is loaded client-side).

STATUS: unfinished stub. I confirmed the page needs JS rendering, but I
have NOT confirmed the actual CSS selectors for the rankings/calendar table
after rendering -- that requires opening browser devtools against the live
rendered page, which needs a real Playwright run (not available in this
chat environment). The TODOs below are the concrete next step, not
optional polish.

TODO before relying on this in production:
  1. Run get_rendered_html() locally against a target UCI URL, e.g.
     https://www.uci.org/discipline/bmx-racing/2IM2tidwZ8mImqzFMsFwB4?tab=rankings
  2. Print/inspect the returned HTML (or use `page.screenshot()` /
     Playwright Inspector) to find the actual container + row selectors
  3. Replace CALENDAR_ROW_SELECTOR below with the real one
  4. Consider: UCI's calendar tab might be a separate XHR call you could
     hit directly (check the Network tab for a JSON response) -- if so,
     that's simpler and more stable than parsing rendered HTML at all.
"""

from bs4 import BeautifulSoup

from ..common.browser import get_rendered_html
from ..common.models import Event

URLS = {
    "UCI BMX Racing": "https://www.uci.org/discipline/bmx-racing/2IM2tidwZ8mImqzFMsFwB4?tab=calendar",
    "UCI BMX Freestyle": "https://www.uci.org/discipline/bmx-freestyle",  # TODO: confirm exact slug/ID
}

# PLACEHOLDER -- confirm against live rendered DOM (see TODO above)
CALENDAR_ROW_SELECTOR = "[data-testid='calendar-row']"


def scrape() -> list[dict]:
    events = []
    for series, url in URLS.items():
        try:
            html = get_rendered_html(url, wait_selector=CALENDAR_ROW_SELECTOR)
        except Exception as exc:
            print(f"[uci_scraper] {series} failed (selector likely needs updating): {exc}")
            continue

        soup = BeautifulSoup(html, "html.parser")
        for row in soup.select(CALENDAR_ROW_SELECTOR):
            text = row.get_text(separator=" | ", strip=True)
            events.append(Event(
                series=series,
                name=text,  # TODO: split into name/date/venue once selector confirmed
                start_date="",  # TODO
                url=url,
                source="uci_scraper",
                tier="playwright",
                raw={"needs_selector_fix": True},
            ).to_dict())
    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape(), indent=2))
