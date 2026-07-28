# Event scraper suite -- status report

Built for the GitHub Actions automation experiment. Honest status of every
piece, so you know what to trust vs. what needs a pass before relying on it.

## What's actually been tested

This sandbox can only reach a short allowlist of domains (pypi, npm,
github, etc.) -- **not** formula1.com, redbull.com, or en.wikipedia.org --
so nothing here has been run against a live network call. What I *could*
do, and did:

- **Regression-tested the regex logic** for `f1_scraper.py` and
  `redbull_scraper.py` against real sample text captured from this
  project's earlier `web_fetch` calls against those exact pages. Both
  found and fixed real bugs in the process (see each file's docstring/
  comments for specifics -- a false-positive date match from result
  timing stats in the F1 scraper, and a missing "DD Month YYYY" date
  format in the Red Bull scraper). Final regex passes 5/5 and 3/3 sample
  cases respectively.
- **Compiled every file** (`python -m py_compile`) -- no syntax errors.
- Everything else (Wikipedia, BikeReg, Webscorer, and all tier3 stubs) is
  written against documented API contracts or the summarized text I saw
  during earlier fetches, but **not** regression-tested the way the two
  regex scrapers were, since I didn't have exact JSON/HTML samples saved
  to test against offline.

**Before trusting any of this in the actual cron job: run `python
run_all.py` once from an environment with real network access (your
machine, or the GitHub Actions job itself with `workflow_dispatch`) and
read the output before turning on the schedule.**

## Tier 1 -- static HTML (`scrapers/tier1_static/`)

| Scraper | Status |
|---|---|
| `f1_scraper.py` | Regex logic tested against 5 real sample patterns, all pass. Ready to try live. |
| `redbull_scraper.py` | Regex logic tested against 3 real sample patterns, all pass. Ready to try live. Filters to bike/BMX/MTB keywords only -- Red Bull's events page covers every sport. |
| `wikipedia_uci_scraper.py` | Uses the real MediaWiki API (not scraping). **Known gap: dates come back as raw Wikipedia text ("6–7 June"), not ISO** -- needs a date-normalizer pass before this is usable as-is. Treat as a secondary/confirmation source, not primary -- volunteer-edited pages can lag real announcements and don't carry broadcast info. |
| `generic_date_scraper.py` | Covers Repack Racing, CCCX, B-17 Racing, Pump Track World Championships. Explicitly a **starting point, not a finished scraper** -- I don't have verified CSS selectors for these (only saw markdown-extracted text in earlier fetches, not raw DOM). First run will be noisy; read the module docstring for the tightening process. |

## Tier 2 -- real APIs (`scrapers/tier2_api/`)

| Scraper | Status |
|---|---|
| `bikereg_scraper.py` | Hits BikeReg's real documented JSON API. Field names (`Name`, `StartDate`, etc.) are per their docs but **not confirmed against a live response** in this session -- verify on first run. |
| `webscorer_scraper.py` | Hits Webscorer's real documented JSON API. **Important limitation, not a bug**: this API is per-race-ID only, there's no "list upcoming races" endpoint, so `RACE_IDS` needs manual upkeep a few times a season. See module docstring for the discovery workflow. |

## Tier 3 -- Playwright (`scrapers/tier3_playwright/`)

All of these are **unfinished stubs**. I confirmed (via direct fetch earlier
in this project) that uci.org, usacycling.org/events, and our.sqorz.com
return empty JS shells with a plain fetch -- so Playwright is genuinely
required -- but I do NOT have the actual post-render CSS selectors, since
that requires opening real browser devtools against the live rendered
page, which isn't possible from this chat environment.

- `uci_scraper.py`, `usacycling_scraper.py`, `usabmx_scraper.py` -- each has
  a `TODO` block at the top of the file with the exact next step (run
  `get_rendered_html()` locally, inspect the DOM, replace the placeholder
  selector).
- `SQORZ_NOTES.md` -- explains why Sqorz is deliberately deprioritized
  rather than built out (its real API is LAN-only, not public cloud; and
  it mainly adds *results*, not *upcoming events*, which isn't this
  project's target).
- `probe_untested_targets.py` -- **run this first**, before writing scrapers
  for Crankworx, X Games, Vans BMX Pro Cup, Formula Drift, Northstar, or
  the FMB calendar index. It tells you plain-fetch vs. Playwright-rendered
  content length for each, so you know which tier each one actually
  belongs in before investing selector-writing effort.

## Running it

```bash
pip install -r requirements.txt
playwright install --with-deps chromium   # only needed for tier3

python run_all.py                 # tier1 + tier2 (recommended default)
python run_all.py --with-tier3    # also attempt the unfinished tier3 stubs
python -m scrapers.tier3_playwright.probe_untested_targets  # classify untested sites
```

Output goes to `output/events_scraped.json`.

## GitHub Actions (`.github/workflows/update-events.yml`)

Two jobs:
1. **`scrape-static-and-api`** -- tier1 + tier2, runs on the actual weekly
   cron (Monday 14:00 UTC). This is the one that's realistic to trust
   unattended once you've done one manual verification run.
2. **`scrape-playwright-stubs`** -- tier3, manual-trigger only
   (`workflow_dispatch` with `with_tier3: true`). Deliberately kept off
   the schedule until the selector TODOs are resolved -- `continue-on-error:
   true` is set so it won't block anything, but there's no point running
   broken selectors on a timer.

Both jobs currently just upload `events_scraped.json` as a workflow
artifact. The step to actually merge this into `events_2026.py` and commit
is stubbed out (commented) in the workflow file -- intentionally left for
after you've validated the JSON shape against a couple of real runs,
rather than wiring up an auto-commit against unverified data.

## Caching (implemented: HTTP response + Playwright browser binary caching)

Two layers, both purely about **speed/politeness**, not history/diffing
(that's a separate, not-yet-built piece — see "not built" note below):

1. **HTTP response caching** (`scrapers/common/fetch.py`) — uses
   `requests-cache` with a SQLite backend at `cache/http_cache.sqlite`,
   6-day default TTL (just under the weekly cron interval), and
   `stale_if_error=True` so a briefly-down site serves its last-known-good
   cached copy instead of failing the whole scraper. Verified end-to-end
   locally: a second call to the same URL comes back in ~4ms with
   `from_cache=True` instead of re-fetching. `get(url, force_refresh=True)`
   bypasses the cache for a single call when debugging.
2. **Playwright browser binary caching** (tier3 job in the workflow) —
   Chromium download (~100+ MB) is cached via `actions/cache`, keyed on
   the pinned Playwright version in `requirements.txt`. Once warm, this
   should hit every run until that version changes.

In the GitHub Actions workflow, both use `actions/cache`: the HTTP cache
saves a new copy each run (`key` includes `run_id`) but restores from the
most recent previous run via `restore-keys`, so the cache persists and
grows/refreshes across scheduled runs rather than starting cold every
Monday.

**What this does NOT give you**, since it's HTTP-level caching, not an
events database: no historical record of past calendar states, and no
"what's new since last week" diffing. That's a different piece (see the
"Suggested next steps" below) — commit-per-run + a `first_seen` field is
the more direct path there, discussed separately.



1. Run `python run_all.py` locally (real network) and read the output.
2. Fix whatever the F1/Red Bull scrapers get wrong against live data --
   should be minor if anything, given the regex testing already done.
3. Run `generic_date_scraper.py` alone, compare its (noisy) output against
   the real Repack/CCCX/B-17/Pump Track pages, tighten selectors.
4. Run `probe_untested_targets.py`, sort Crankworx/XGames/Vans/Formula
   Drift/Northstar/FMB-index into tier1 or tier3 based on the result.
5. Only then flip on the weekly cron for real.
