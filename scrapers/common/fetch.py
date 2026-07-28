"""
Shared fetch helper for the tier1 (static HTML) and tier2 (API) scrapers.

Not used by tier3 -- those go through Playwright directly since they need a
real browser context, not just requests.

CACHING: uses requests-cache (SQLite-backed) so repeated runs against an
unchanged page don't do a full re-fetch. This is HTTP-level caching only --
it speeds up runs and is polite to the small-org sites we're hitting, but
it is NOT event history/diffing (see README's "Caching" section for why
that's a separate, not-yet-built piece). Default expiry is 6 days, just
under the weekly cron interval, so a normal Monday run always gets fresh
data but a same-day re-run (e.g. manual retry, or the tier3 job running
right after tier1/2) reuses what was already fetched instead of hammering
the same URLs twice.
"""

import time
from pathlib import Path

import requests
import requests_cache

CACHE_PATH = "cache/http_cache"  # -> cache/http_cache.sqlite; persisted via
                                   # actions/cache in the workflow (see
                                   # .github/workflows/update-events.yml)
Path("cache").mkdir(exist_ok=True)  # requests_cache doesn't create the dir itself
DEFAULT_EXPIRE_SECONDS = 6 * 24 * 60 * 60  # 6 days -- just under the weekly cron

# A single shared cached session for the whole process. Sites that return
# real Cache-Control/ETag headers get revalidated properly; sites that
# don't (a lot of small WordPress-y sites won't) fall back to the flat
# DEFAULT_EXPIRE_SECONDS TTL.
_session = requests_cache.CachedSession(
    CACHE_PATH,
    backend="sqlite",
    expire_after=DEFAULT_EXPIRE_SECONDS,
    stale_if_error=True,  # serve a stale cached copy rather than failing
                            # the whole scraper if a site is briefly down
)

DEFAULT_HEADERS = {
    # A plain "python-requests" UA gets blocked or served a stripped-down
    # page on some of these sites. A normal browser UA is more reliable.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def get(url: str, params: dict | None = None, retries: int = 3, timeout: int = 20,
        sleep_between: float = 1.0, force_refresh: bool = False) -> requests.Response:
    """GET with caching + retries. Pass force_refresh=True to bypass the
    cache for a single call (e.g. when debugging a scraper against the
    live page instead of a possibly-stale cached copy)."""
    last_exc = None
    for attempt in range(retries):
        try:
            resp = _session.get(
                url, params=params, headers=DEFAULT_HEADERS, timeout=timeout,
                refresh=force_refresh,
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            time.sleep(sleep_between * (attempt + 1))
    raise last_exc


def get_json(url: str, params: dict | None = None, **kwargs) -> dict | list:
    return get(url, params=params, **kwargs).json()


def cache_stats() -> dict:
    """Quick visibility into what's cached -- handy to print at the start
    of a run so it's obvious in the Actions log whether requests are
    actually hitting the cache or not."""
    responses = _session.cache.responses
    return {
        "cached_urls": len(responses),
        "cache_path": f"{CACHE_PATH}.sqlite",
    }
