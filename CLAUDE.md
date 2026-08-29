# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static, no-build fan site that displays Borussia Düsseldorf's TTBL (Tischtennis-Bundesliga) schedule and league table. Plain HTML/CSS/JS — no framework, no bundler, no package.json. Two Python scripts scrape the data into JSON files that the frontend fetches at runtime; a third script renders the schedule as a downloadable PDF; a GitHub Actions workflow keeps games.json, table.json and spielplan.pdf up to date automatically.

## Commands

There is no build step and no test suite. Development commands:

```bash
# Serve the site locally (fetch() requires http://, not file://)
python -m http.server 8000

# Install scraper dependencies
pip install -r scripts/requirements.txt

# Re-scrape schedule / table data
python scripts/fetch_games.py
python scripts/fetch_table.py

# Regenerate the downloadable PDF schedule from games.json
python scripts/generate_pdf.py
```

Opening `index.html` directly via `file://` breaks the page: `fetch("games.json")` / `fetch("table.json")` are blocked by CORS under the `file://` origin, so both sections silently fail to render. Always test through a local HTTP server.

## Architecture

**Data flow:** the two Python scrapers are the source of truth generators; the frontend never talks to any live API. `generate_pdf.py` derives a downloadable PDF from the scraped `games.json`.

```
scripts/fetch_games.py  --> games.json  --\
                                            +--> script.js (fetch) --> DOM
scripts/fetch_table.py  --> table.json  --/

games.json --> scripts/generate_pdf.py --> spielplan.pdf --> index.html (download link)
```

- `scripts/fetch_games.py` scrapes `https://www.borussia-duesseldorf.com/profis/spielplan` (one `<table class="ce-table">` under the "Bundesliga" heading). It captures **both** home and away fixtures — a row is a home game when `TEAM_NAME` appears in the "Heim" column, away when it appears in "Gast" — and tags each with `"heimspiel": true/false`. Games whose date is before today are filtered out, so `games.json` only ever contains upcoming fixtures. Venue is the hall name for home games and the literal string `"auswärts"` for away games.
- `scripts/fetch_table.py` scrapes `https://www.ttbl.de/bundesliga/table/2026-2027/1`, which contains exactly one `<table>` (columns: Rang, Team, Beg., S, N, Spiele, +/-, Punkte). Team name is read from the `<a title="...">` attribute (more reliable than the visible, viewport-dependent text). `punkte` is the team's own point total (first number of the site's `"2 : 0"` pair); `satzdifferenz` maps to the site's `+/-` column, which is technically a *Spieldifferenz* (games won/lost), not a literal Sätze count — the closest available stat.
- `scripts/generate_pdf.py` reads `games.json`, re-filters for upcoming fixtures (its own `is_upcoming()` check, independent of the filtering already done by `fetch_games.py`), and renders them via `reportlab` into `spielplan.pdf` (A4, club red/white color scheme, one row per game with a Heim/Auswärts badge). It has no network dependency — it only ever needs `games.json` to already exist.
- Both scraper scripts write pretty-printed, UTF-8 JSON sorted appropriately (`games.json` by date, `table.json` by `platz`) and overwrite their output file directly — no diffing logic in the scripts themselves.
- `.github/workflows/update-games.yml` runs both scrapers daily (`cron: "0 5 * * *"`, plus manual `workflow_dispatch`), then `generate_pdf.py`, then commits+pushes `games.json`/`table.json`/`spielplan.pdf` as `github-actions[bot]` only if `git diff` shows changes.

**Frontend (`script.js`):** two independent `init*()` entry points (`initGames()`, `initTable()`) run at the bottom of the file, each with its own try/catch so a failure in one section doesn't take down the other:

- `initGames()` loads `games.json`, parses `datum`/`uhrzeit` (German `DD.MM.YYYY` / `HH:MM` strings) into `Date` objects, sorts chronologically, renders a card per game (`.is-home`/`.is-away` colors it red vs. blue-gray, `.is-next` highlights the soonest upcoming one), and drives a live-updating countdown (`setInterval`, 1s) toward the next game **across all fixtures, not just home games**.
- `initTable()` loads `table.json`, sorts by `platz`, and renders a table row per team. The row whose `name` exactly equals the `OWN_TEAM_NAME` constant (`"Borussia Düsseldorf"`) gets `.is-own-team` for the red highlight.
- `initTheme()` wires the header `#theme-toggle` button: it toggles `data-theme="dark"` on `<html>` and persists the choice in `localStorage` under the key `"theme"`. First visit falls back to the OS `prefers-color-scheme`. To avoid a flash of the wrong theme, a tiny inline script in `<head>` of `index.html` applies the stored/OS theme before first paint; `initTheme()` then reconciles and keeps the button label/icon in sync. Dark-mode colors are a full palette override under `:root[data-theme="dark"]` in `style.css` — all component colors resolve through CSS custom properties (`--bd-surface`, `--bd-heading`, `--bd-border`, etc.), so adding new UI means using those vars, not literal colors.

**Load-bearing naming convention:** the literal string `"Borussia Düsseldorf"` must stay consistent across `scripts/fetch_games.py` (`TEAM_NAME`), `scripts/fetch_table.py` (implicitly, via whatever the source site titles the team), and `script.js` (`OWN_TEAM_NAME`). If the source sites ever rename the club (e.g. add/drop a legal suffix), the home/away detection and the table row highlighting will silently stop matching.

**JSON schemas the frontend depends on** (changing field names requires updating `script.js` in lockstep):

```jsonc
// games.json — one entry per upcoming fixture
{ "datum": "26.08.2026", "uhrzeit": "18:30", "gegner": "SV Werder Bremen", "ort": "auswärts", "heimspiel": false }

// table.json — one entry per team, sorted by platz
{ "platz": 1, "name": "Borussia Düsseldorf", "spiele": 1, "siege": 1, "niederlagen": 0, "punkte": 2, "satzdifferenz": 3 }
```
