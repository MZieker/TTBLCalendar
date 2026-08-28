#!/usr/bin/env python3
"""Scrapt die TTBL-Spiele (Heim und Auswaerts) von Borussia Duesseldorf
und schreibt die noch anstehenden Spiele nach games.json.

Quelle: https://www.borussia-duesseldorf.com/profis/spielplan
Die Seite enthaelt eine Tabelle (Spalten: Spieltag, Ort, Tag, Datum, Uhrzeit,
Heim, Gast, Ergebnis, Tickets) unterhalb der Ueberschrift "Tischtennis
Bundesliga (TTBL) ...". Heimspiele erkennt man daran, dass in der Spalte
"Ort" der Hallenname steht (statt "auswaerts") und Borussia Duesseldorf in
der Spalte "Heim" steht; bei Auswaertsspielen steht Borussia Duesseldorf in
der Spalte "Gast".
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
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


def parse_games(table) -> list[dict]:
    games = []
    for row in table.find_all("tr"):
        if row.find("b") is not None:
            continue  # Kopfzeile

        cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
        if len(cells) < 7:
            continue

        _spieltag, ort, _tag, datum, uhrzeit, heim, gast = cells[:7]
        heim, gast, ort, datum = heim.strip(), gast.strip(), ort.strip(), datum.strip()

        if not DATE_PATTERN.match(datum):
            continue

        if TEAM_NAME in heim:
            heimspiel = True
            gegner = gast
        elif TEAM_NAME in gast:
            heimspiel = False
            gegner = heim
        else:
            continue  # Zeile betrifft nicht Borussia Duesseldorf

        if not gegner:
            continue

        if heimspiel:
            venue = "Ort noch offen" if ort.upper() == "TBD" or not ort else ort
        else:
            venue = "auswärts"

        games.append(
            {
                "datum": datum,
                "uhrzeit": (
                    uhrzeit.strip() if TIME_PATTERN.match(uhrzeit.strip()) else "TBD"
                ),
                "gegner": gegner,
                "ort": venue,
                "heimspiel": heimspiel,
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


def is_upcoming(game: dict, today: date) -> bool:
    day, month, year = (int(part) for part in game["datum"].split("."))
    return date(year, month, day) >= today


def main() -> int:
    html = fetch_html()
    soup = BeautifulSoup(html, "html.parser")

    table = find_bundesliga_table(soup)
    if table is None:
        print("Konnte die Spielplan-Tabelle nicht finden.", file=sys.stderr)
        return 1

    today = date.today()
    games = sorted(parse_games(table), key=sort_key)
    games = [game for game in games if is_upcoming(game, today)]

    if not games:
        print(
            "Keine anstehenden Spiele gefunden, games.json wird nicht veraendert.",
            file=sys.stderr,
        )
        return 1

    OUTPUT_PATH.write_text(
        json.dumps(games, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    heimspiele = sum(1 for game in games if game["heimspiel"])
    print(
        f"{len(games)} anstehende Spiele gespeichert in {OUTPUT_PATH} "
        f"({heimspiele} Heim, {len(games) - heimspiele} Auswaerts)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
