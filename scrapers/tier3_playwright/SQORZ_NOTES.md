# Sqorz -- deliberately not built as a scraper (yet)

`our.sqorz.com/org/usabmx` was confirmed to be an empty JS shell (React/Vue
SPA) with no content in the raw HTML. It's a reasonable Playwright target
in principle, but two things make it lower priority than the other tier3
sites:

1. Sqorz's *documented* API (docs.sqorz.com "APIs for Information and
   Results") is explicitly scoped to the local scoring computer on race
   day's LAN -- it is not a public cloud endpoint, so there's no API
   shortcut here the way there was for BikeReg/Webscorer.
2. Everything Sqorz would give us (USA BMX race results/standings) is
   already covered by usabmx_scraper.py's per-track schedule scrape and
   the static national schedule post -- Sqorz mainly adds *results*
   (who won), which isn't the target of this project (upcoming events),
   not *schedule* data.

Recommendation: skip building this out unless a future need for historical
results/standings (not just upcoming events) comes up. If it does, it's a
straightforward Playwright target structurally -- same pattern as
uci_scraper.py, just pointed at our.sqorz.com/org/usabmx.
