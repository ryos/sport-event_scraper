"""
Shared Playwright helper for tier3 scrapers (sites confirmed to be JS
shells: uci.org, usacycling.org/events, our.sqorz.com, usabmx.com/events,
and untested-but-likely candidates crankworx.com / xgames.com).

Usage in a tier3 scraper:

    from ..common.browser import get_rendered_html

    html = get_rendered_html("https://www.uci.org/discipline/bmx-racing/...")
    soup = BeautifulSoup(html, "html.parser")
    ...

Keep wait_selector as tight as possible (a real content element, not just
`body`) -- otherwise you'll scrape the loading skeleton, not the data.
"""

from playwright.sync_api import sync_playwright

DEFAULT_TIMEOUT_MS = 20_000


def get_rendered_html(url: str, wait_selector: str | None = None,
                       wait_ms: int = 2000, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ))
        page.goto(url, timeout=timeout_ms, wait_until="networkidle")
        if wait_selector:
            page.wait_for_selector(wait_selector, timeout=timeout_ms)
        else:
            page.wait_for_timeout(wait_ms)
        html = page.content()
        browser.close()
        return html
