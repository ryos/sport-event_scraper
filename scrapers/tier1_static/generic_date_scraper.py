"""
Generic starter scraper for sites confirmed to render server-side (Repack
Racing, CCCX/3CX, B-17 Racing, Pump Track World Championships) but where I
don't have verified CSS selectors -- earlier fetches in this project
returned extracted/markdown text, not raw DOM with class names, so I can't
write precise selector-based parsers for these the way I could for F1 and
Red Bull.

This is a HONEST STARTING POINT, not a finished scraper: it pulls every
plain-text block near a date-like pattern and returns it as a raw
candidate event. Expect noisy/duplicate output on the first run. The fix is
mechanical, not conceptual: run this once, look at the actual output next
to the real page, then tighten SELECTOR_HINTS per site once you can see
which HTML container actually wraps each event (view-source or devtools).

DO NOT wire this straight into the calendar without a manual review pass
on first use.
"""

import re
from dataclasses import dataclass
from bs4 import BeautifulSoup

from ..common.fetch import get
from ..common.models import Event

DATE_RE = re.compile(
    r"(?P<mon>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+"
    r"(?P<d1>\d{1,2})(?:\s*[-–]\s*(?P<d2>\d{1,2}))?,?\s*(?P<year>20\d{2})?",
)

MONTHS = {m: f"{i+1:02d}" for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
)}


@dataclass
class SiteConfig:
    series: str
    url: str
    default_year: int = 2026
    # Optional CSS selector for the container that wraps one event; leave
    # None to fall back to scanning every <a> tag (noisier but a safe default
    # until selectors are confirmed against the live page).
    event_selector: str | None = None


SITES = [
    SiteConfig(series="Repack Racing / CCCX", url="https://repackracing.com/"),
    SiteConfig(series="CCCX Cycling", url="https://cccxcycling.com/"),
    SiteConfig(series="B-17 Racing", url="https://b17racing.com/"),
    SiteConfig(series="Velosolutions UCI Pump Track World Championships",
               url="https://pumptrackworldchampionships.com/"),
]


def _parse_date(m: re.Match, default_year: int) -> tuple[str, str]:
    year = m.group("year") or str(default_year)
    mon = MONTHS.get(m.group("mon"), "01")
    d1 = int(m.group("d1"))
    d2 = int(m.group("d2")) if m.group("d2") else d1
    return f"{year}-{mon}-{d1:02d}", f"{year}-{mon}-{d2:02d}"


def scrape_site(cfg: SiteConfig) -> list[dict]:
    resp = get(cfg.url)
    soup = BeautifulSoup(resp.text, "html.parser")
    containers = soup.select(cfg.event_selector) if cfg.event_selector else soup.find_all("a", href=True)

    events = []
    for el in containers:
        text = el.get_text(separator=" ", strip=True)
        m = DATE_RE.search(text)
        if not m:
            continue
        start, end = _parse_date(m, cfg.default_year)
        href = el.get("href") if el.name == "a" else None
        events.append(Event(
            series=cfg.series,
            name=text[:120],  # untrimmed candidate name -- review manually
            start_date=start,
            end_date=end,
            url=href,
            source="generic_date_scraper",
            tier="static",
            raw={"needs_review": True},
        ).to_dict())
    return events


def scrape() -> list[dict]:
    events = []
    for cfg in SITES:
        try:
            events.extend(scrape_site(cfg))
        except Exception as exc:  # keep going even if one site is down/changed
            print(f"[generic_date_scraper] {cfg.series} failed: {exc}")
    return events


if __name__ == "__main__":
    import json
    print(json.dumps(scrape(), indent=2))
