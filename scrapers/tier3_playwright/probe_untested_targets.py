"""
Probe script -- NOT a scraper. Run this FIRST against the sites we never
actually tested (Crankworx, X Games, Vans BMX Pro Cup, Formula Drift,
Northstar California, FMB World Tour calendar index). It fetches each URL
two ways -- plain requests vs. Playwright-rendered -- and reports whether
the plain fetch already has enough content, so you know which tier each
site actually belongs in before writing a real scraper for it.

Run:  python -m scrapers.tier3_playwright.probe_untested_targets

Output: for each site, the character count of plain-fetched body text vs.
Playwright-rendered body text. A big gap (rendered >> plain) means it's a
real tier3/Playwright site. Similar counts mean it was actually tier1 all
along and doesn't need a browser -- move it to generic_date_scraper.py's
SITES list instead and save yourself the Playwright overhead.
"""

from bs4 import BeautifulSoup

from ..common.fetch import get
from ..common.browser import get_rendered_html

TARGETS = {
    "Crankworx": "https://crankworx.com/",
    "X Games": "https://xgames.com/",
    "Vans BMX Pro Cup": "https://www.vansbmxprocup.com/",
    "Formula Drift schedule": "https://www.formulad.com/schedule",
    "Northstar California": "https://www.northstarcalifornia.com/",
    "FMB World Tour calendar index": "https://www.fmbworldtour.com/calendar/",
}


def _body_text_len(html: str) -> int:
    return len(BeautifulSoup(html, "html.parser").get_text(strip=True))


def probe():
    for name, url in TARGETS.items():
        try:
            plain_len = _body_text_len(get(url).text)
        except Exception as exc:
            plain_len = f"ERROR: {exc}"

        try:
            rendered_len = _body_text_len(get_rendered_html(url, wait_ms=3000))
        except Exception as exc:
            rendered_len = f"ERROR: {exc}"

        print(f"{name:35s} plain={plain_len!s:>12}  rendered={rendered_len!s:>12}")


if __name__ == "__main__":
    probe()
