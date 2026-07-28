"""
Shared Event schema for all scrapers.

Every scraper returns a list of dicts matching this shape so results can be
merged directly into events_2026.py (or written out as JSON for a separate
merge step). Keep fields consistent even when a source doesn't have a value
for one -- use None rather than omitting the key.
"""

from dataclasses import dataclass, asdict, field
from datetime import date
from typing import Optional


@dataclass
class Event:
    series: str                 # e.g. "F1", "USA BMX", "UCI BMX Racing WC", "Red Bull"
    name: str                   # e.g. "Dutch Grand Prix"
    start_date: str             # ISO format YYYY-MM-DD
    end_date: Optional[str] = None
    venue: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    url: Optional[str] = None
    source: str = ""            # which scraper produced this row
    tier: str = ""              # "static" | "api" | "playwright"
    raw: dict = field(default_factory=dict)  # anything extra worth keeping

    def to_dict(self):
        return asdict(self)


def dedupe(events: list[dict]) -> list[dict]:
    """Drop exact (series, name, start_date) duplicates -- useful when a
    source is polled by more than one scraper (e.g. UCI via Wikipedia AND
    a future direct scrape)."""
    seen = set()
    out = []
    for e in events:
        key = (e.get("series"), e.get("name"), e.get("start_date"))
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out
