"""
Runs every scraper and writes a combined output/events_scraped.json.

Tiers are run separately and reported separately, since tier1/tier2 are
production-ready (or close to it) and tier3 is still stub/TODO status --
see each module's docstring. Keeping them visibly separate in the log
output makes it obvious at a glance which numbers to trust.

Usage:
    python run_all.py                 # tier1 + tier2 only (safe default)
    python run_all.py --with-tier3    # also attempt the Playwright stubs
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from scrapers.common.models import dedupe

OUTPUT_PATH = Path(__file__).parent / "output" / "events_scraped.json"


def run_tier1():
    from scrapers.tier1_static import f1_scraper, redbull_scraper, wikipedia_uci_scraper, generic_date_scraper
    events = []
    for mod in (f1_scraper, redbull_scraper, wikipedia_uci_scraper, generic_date_scraper):
        try:
            result = mod.scrape()
            print(f"[tier1] {mod.__name__}: {len(result)} events")
            events.extend(result)
        except Exception as exc:
            print(f"[tier1] {mod.__name__} FAILED: {exc}", file=sys.stderr)
    return events


def run_tier2():
    from scrapers.tier2_api import bikereg_scraper, webscorer_scraper
    events = []
    for mod in (bikereg_scraper, webscorer_scraper):
        try:
            result = mod.scrape()
            print(f"[tier2] {mod.__name__}: {len(result)} events")
            events.extend(result)
        except Exception as exc:
            print(f"[tier2] {mod.__name__} FAILED: {exc}", file=sys.stderr)
    return events


def run_tier3():
    from scrapers.tier3_playwright import uci_scraper, usacycling_scraper, usabmx_scraper
    events = []
    for mod in (uci_scraper, usacycling_scraper, usabmx_scraper):
        try:
            result = mod.scrape()
            print(f"[tier3] {mod.__name__}: {len(result)} events (STUB -- verify selectors)")
            events.extend(result)
        except Exception as exc:
            print(f"[tier3] {mod.__name__} FAILED (expected until selectors are fixed): {exc}", file=sys.stderr)
    return events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-tier3", action="store_true",
                        help="Also run the tier3 Playwright stubs (selectors unverified -- expect failures/noise)")
    args = parser.parse_args()

    from scrapers.common.fetch import cache_stats
    print(f"[cache] {cache_stats()}  (0 cached_urls on a fresh/cold cache is expected on the first run)")

    all_events = run_tier1() + run_tier2()
    if args.with_tier3:
        all_events += run_tier3()

    all_events = dedupe(all_events)

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "event_count": len(all_events),
        "events": all_events,
    }, indent=2))

    print(f"\nWrote {len(all_events)} events to {OUTPUT_PATH}")
    print(f"[cache] {cache_stats()}")


if __name__ == "__main__":
    main()
