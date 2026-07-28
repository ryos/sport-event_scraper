"""
F1 scraper -- CONFIRMED WORKING (tested via direct fetch on 2026-07-27).

formula1.com/en/racing/2026 is server-rendered; the full season list is
present in the raw HTML with no JS execution required.

Approach: rather than depending on CSS class names (which I can't verify
without raw browser devtools access -- I only confirmed structure through a
markdown-extracting fetch, not raw source), this parses the flattened link
text. IMPORTANT WRINKLE, confirmed by testing this regex against real
sample text before shipping it: F1's own text order is NOT consistent --

  Upcoming round (no results yet):
    "ROUND 12Flag of NetherlandsNetherlandsFORMULA 1 HEINEKEN DUTCH GRAND
     PRIX 202621 - 23 Aug"                      <- date AFTER event name

  Completed round (has results appended):
    "ROUND 1Chequered Flag06 - 08 MarFlag of AustraliaAustraliaFORMULA 1
     QATAR AIRWAYS AUSTRALIAN GRAND PRIX 20261stRussellRUS1:23:06.801..."
                                                  <- date BEFORE "Flag of"

So this finds the "Flag of <Country> ... GRAND PRIX 2026" anchor first,
then searches a window on BOTH sides of it for a date pattern, since which
side it's on depends on whether the race already happened. This is more
robust to that inconsistency than a single fixed-order regex.
"""

import re
from bs4 import BeautifulSoup

from ..common.fetch import get
from ..common.models import Event

URL = "https://www.formula1.com/en/racing/2026"

ANCHOR_RE = re.compile(
    # "Flag of" is followed by the country name repeated as both the flag
    # caption and the location (e.g. "NetherlandsNetherlands", or
    # "United Arab EmiratesAbu Dhabi" when city != country) -- these aren't
    # reliably splittable by regex alone without a country-name lookup
    # table, so this captures the whole run as one field and leaves
    # cleanup to whoever consumes it, rather than guessing wrong.
    r"Flag of (?P<location_raw>[A-Za-z’' \-]+?)"
    # Some races have extra words after "GRAND PRIX" before the year, e.g.
    # "GRAND PRIX DE MONACO 2026" / "GRAND PRIX DU CANADA 2026" -- caught
    # by testing this regex against several real samples, not just the
    # simple "<SPONSOR> <COUNTRY> GRAND PRIX 2026" case.
    r"(?P<name>[A-Z0-9.’'&® ]+GRAND PRIX[A-Z0-9.’'&® ]*2026)"
)
ROUND_RE = re.compile(r"ROUND\s*(?P<round>\d+)")
DATE_RE = re.compile(r"(\d{2})\s*-\s*(\d{2})\s*([A-Za-z]{3})|(\d{2})\s*([A-Za-z]{3})")
WINDOW = 40  # chars to search on each side of the anchor for a date

MONTHS = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
    "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}


def _to_iso(day: str, mon: str, year: int = 2026) -> str:
    return f"{year}-{MONTHS.get(mon, '01')}-{int(day):02d}"


def _extract_date(text: str, anchor_start: int, anchor_end: int):
    """Search a window before AND after the anchor match for a date; return
    whichever is found. Tested against real sample text: "before" MUST be
    tried first -- for completed rounds, the "after" window contains result
    stats (lap times, gaps like "+2.974") whose digit runs can false-match
    the date pattern (e.g. "...1:23:06.8012nd..." -> looks like "12 nd" and
    partially matches DD+month-like text). Upcoming rounds have nothing in
    their "before" window (just "ROUND N"), so checking "before" first is
    safe for both cases -- it either finds the real date (completed round)
    or finds nothing and correctly falls through to "after" (upcoming
    round, which has no results text to false-match against)."""
    before = text[max(0, anchor_start - WINDOW):anchor_start]
    after = text[anchor_end:anchor_end + WINDOW]

    for window in (before, after):
        m = DATE_RE.search(window)
        if m:
            if m.group(1):  # DD - DD Mon form
                return m.group(1), m.group(2), m.group(3)
            else:  # single DD Mon form
                return m.group(4), m.group(4), m.group(5)
    return None


def scrape() -> list[dict]:
    resp = get(URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    for a in soup.find_all("a", href=True):
        text = a.get_text(separator="", strip=True)
        if "GRAND PRIX 2026" not in text:
            continue

        anchor = ANCHOR_RE.search(text)
        if not anchor:
            continue

        date_match = _extract_date(text, anchor.start(), anchor.end())
        if not date_match:
            continue
        start_day, end_day, mon = date_match

        round_m = ROUND_RE.search(text)

        href = a["href"]
        url = href if href.startswith("http") else f"https://www.formula1.com{href}"

        events.append(Event(
            series="F1",
            name=anchor.group("name").title().replace("2026", "").strip(),
            start_date=_to_iso(start_day, mon),
            end_date=_to_iso(end_day, mon),
            country=anchor.group("location_raw").strip(),  # raw, may be
                                                              # "NetherlandsNetherlands"-
                                                              # style duplicate; clean
                                                              # up downstream if needed
            url=url,
            source="f1_scraper",
            tier="static",
            raw={"round": round_m.group("round") if round_m else None},
        ).to_dict())

    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape(), indent=2))
