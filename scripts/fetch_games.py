#!/usr/bin/env python3
"""Scrapt die TTBL-Heimspiele von Borussia Düsseldorf und schreibt sie nach games.json.

Quelle: https://www.borussia-duesseldorf.com/profis/spielplan
Die Seite enthaelt eine Tabelle (Spalten: Spieltag, Ort, Tag, Datum, Uhrzeit,
Heim, Gast, Ergebnis, Tickets) unterhalb der Ueberschrift "Tischtennis
Bundesliga (TTBL) ...". Heimspiele erkennt man daran, dass in der Spalte
"Ort" der Hallenname steht (statt "auswaerts").
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SCHEDULE_URL = "https://www.borussia-duesseldorf.com/profis/spielplan"
TEAM_NAME = "Borussia Düsseldorf"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "games.json"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TTBLCalendarBot/1.0; +https://github.com/)"
}
DATE_PATTERN = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")


def fetch_html() -> str:
    response = requests.get(SCHEDULE_URL, headers=REQUEST_HEADERS, timeout=20)
    response.raise_for_status()
    return response.text


def find_bundesliga_table(soup: BeautifulSoup):
    for heading in soup.find_all(["h2", "h3"]):
        if "bundesliga" in heading.get_text(strip=True).lower():
            table = heading.find_next("table", class_="ce-table")
            if table is not None:
                return table
    return soup.find("table", class_="ce-table")


def parse_home_games(table) -> list[dict]:
    games = []
    for row in table.find_all("tr"):
        if row.find("b") is not None:
            continue  # Kopfzeile

        cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
        if len(cells) < 7:
            continue

        _spieltag, ort, _tag, datum, uhrzeit, heim, gast = cells[:7]

        if ort.strip().lower() == "auswärts":
            continue  # Auswaertsspiel
        if TEAM_NAME not in heim:
            continue  # zur Sicherheit: nur echte Heimspiele
        if not DATE_PATTERN.match(datum.strip()):
            continue

        gegner = gast.strip()
        if not gegner:
            continue

        venue = ort.strip()
        if venue.upper() == "TBD" or not venue:
            venue = "Ort noch offen"

        games.append(
            {
                "datum": datum.strip(),
                "uhrzeit": uhrzeit.strip() if TIME_PATTERN.match(uhrzeit.strip()) else "TBD",
                "gegner": gegner,
                "ort": venue,
            }
        )

    return games


def sort_key(game: dict):
    day, month, year = (int(part) for part in game["datum"].split("."))
    try:
        hour, minute = (int(part) for part in game["uhrzeit"].split(":"))
    except ValueError:
        hour, minute = 0, 0
    return (year, month, day, hour, minute)


def main() -> int:
    html = fetch_html()
    soup = BeautifulSoup(html, "html.parser")

    table = find_bundesliga_table(soup)
    if table is None:
        print("Konnte die Spielplan-Tabelle nicht finden.", file=sys.stderr)
        return 1

    games = sorted(parse_home_games(table), key=sort_key)
    if not games:
        print("Keine Heimspiele gefunden, games.json wird nicht veraendert.", file=sys.stderr)
        return 1

    OUTPUT_PATH.write_text(
        json.dumps(games, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{len(games)} Heimspiele gespeichert in {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
