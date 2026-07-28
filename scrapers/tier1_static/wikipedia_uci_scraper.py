"""
Wikipedia scraper -- used as a proxy for UCI calendars since uci.org itself
is a JS shell we can't parse without Playwright (see tier3/uci_scraper.py).

Uses the official MediaWiki Action API (action=parse), which is a genuine
public API, not scraping -- no robots.txt concerns, stable JSON contract.
https://www.mediawiki.org/wiki/API:Parsing_wikitext

Trade-off: Wikipedia's season-recap pages (e.g. "2026 UCI BMX Racing World
Cup") are maintained by volunteer editors and sometimes lag a real UCI
announcement by days, and don't include TV/broadcast info. Treat this as a
secondary confirmation source / early-warning feed, not the sole source of
truth -- pair it with the UCI Playwright scraper once that's built and
compare, rather than fully replacing it.
"""

import pandas as pd
from io import StringIO

from ..common.fetch import get
from ..common.models import Event

API = "https://en.wikipedia.org/w/api.php"

# One page per discipline/season -- extend this list as needed
PAGES = {
    "UCI BMX Racing World Cup": "2026 UCI BMX Racing World Cup",
    "UCI Mountain Bike World Cup": "2026 UCI Mountain Bike World Cup",
}


def _fetch_tables(title: str) -> list[pd.DataFrame]:
    resp = get(API, params={
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
    })
    html = resp.json()["parse"]["text"]["*"]
    try:
        return pd.read_html(StringIO(html))
    except ValueError:
        return []


def scrape() -> list[dict]:
    events = []
    for series, title in PAGES.items():
        tables = _fetch_tables(title)
        for df in tables:
            cols = {c.lower(): c for c in df.columns.astype(str)}
            if "date" not in cols or "location" not in cols and "venue" not in cols:
                continue
            loc_col = cols.get("location") or cols.get("venue")
            for _, row in df.iterrows():
                date_val = str(row[cols["date"]])
                loc_val = str(row[loc_col])
                if not date_val or date_val.lower() == "nan":
                    continue
                events.append(Event(
                    series=series,
                    name=f"{series} — {loc_val}",
                    start_date=date_val,  # NOTE: raw Wikipedia date text (e.g.
                                            # "6–7 June") -- needs a real
                                            # date-normalizer pass with the
                                            # season year applied; not ISO yet
                    venue=loc_val,
                    url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    source="wikipedia_uci_scraper",
                    tier="static",
                ).to_dict())
    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape(), indent=2))
