"""
Red Bull events scraper -- CONFIRMED WORKING (tested via direct fetch on
2026-07-27). www.redbull.com/us-en/events is server-rendered.

Red Bull's events page covers every sport (surfing, cliff diving, dance,
gaming...), not just bike stuff, so this filters to a bike/BMX/MTB category
allowlist after parsing. The link text pattern is looser than F1's -- Red
Bull doesn't use one consistent template across event types -- so this is
a best-effort date + name extractor, not a strict positional parse. Expect
to tune BIKE_KEYWORDS and the date regex as false positives/negatives show
up in the first few real runs.
"""

import re
from bs4 import BeautifulSoup

from ..common.fetch import get
from ..common.models import Event

URL = "https://www.redbull.com/us-en/events"

BIKE_KEYWORDS = (
    "bike", "bmx", "mtb", "mountain bike", "cycling", "downhill",
    "slopestyle", "pump track", "cerro abajo", "hardline", "joyride",
    "district ride", "rampage", "formation",
)

_MONTH_NAMES = (
    r"January|February|March|April|May|June|July|August|September|"
    r"October|November|December"
)
# US listing pages use "June 20 – 21, 2026" / "June 20, 2026"; some
# international event pages use "25 July 2026" -- tested both against this
# combined pattern to avoid silently missing one format.
DATE_RE = re.compile(
    rf"(?:(?P<mon>{_MONTH_NAMES})\s+(?P<d1>\d{{1,2}})"
    rf"(?:\s*[–\-]\s*(?P<d2>\d{{1,2}}))?,?\s+(?P<year>20\d{{2}}))"
    rf"|(?:(?P<d1b>\d{{1,2}})\s+(?P<monb>{_MONTH_NAMES})\s+(?P<yearb>20\d{{2}}))"
)

MONTHS = {
    "January": "01", "February": "02", "March": "03", "April": "04", "May": "05",
    "June": "06", "July": "07", "August": "08", "September": "09",
    "October": "10", "November": "11", "December": "12",
}


def scrape() -> list[dict]:
    resp = get(URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    events = []

    for a in soup.find_all("a", href=True):
        text = a.get_text(separator=" ", strip=True)
        if not any(k in text.lower() for k in BIKE_KEYWORDS):
            continue

        m = DATE_RE.search(text)
        if not m:
            continue

        if m.group("year"):  # "Month D[-D], YYYY" branch
            year, mon = m.group("year"), MONTHS[m.group("mon")]
            d1, d2 = m.group("d1"), m.group("d2")
        else:  # "D Month YYYY" branch
            year, mon = m.group("yearb"), MONTHS[m.group("monb")]
            d1, d2 = m.group("d1b"), None

        start_date = f"{year}-{mon}-{int(d1):02d}"
        end_date = f"{year}-{mon}-{int(d2):02d}" if d2 else start_date

        # Name is everything before the date match in the link text
        name = text[:m.start()].strip(" -")
        href = a["href"]
        url = href if href.startswith("http") else f"https://www.redbull.com{href}"

        events.append(Event(
            series="Red Bull",
            name=name or text,
            start_date=start_date,
            end_date=end_date,
            url=url,
            source="redbull_scraper",
            tier="static",
        ).to_dict())

    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape(), indent=2))
