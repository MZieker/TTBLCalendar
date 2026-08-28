#!/usr/bin/env python3
"""Scrapt die aktuelle TTBL-Tabelle und schreibt sie nach table.json.

Quelle: https://www.ttbl.de/bundesliga/table/2026-2027/1
Die Seite enthaelt genau eine <table> mit den Spalten Rang, Team, Beg.
(Begegnungen), S (Siege), N (Niederlagen), Spiele (gewonnene : verlorene
Einzelspiele), +/- (Differenz aus der Spiele-Spalte) und Punkte (eigene :
gegnerische Punkte, jeweils 2 Punkte pro Sieg). Aus der Punkte-Spalte wird
nur die eigene Punktzahl uebernommen; aus der +/--Spalte die Spieldifferenz
als naeherungsweises Aequivalent zur "Satzdifferenz".
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

TABLE_URL = "https://www.ttbl.de/bundesliga/table/2026-2027/1"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "table.json"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TTBLCalendarBot/1.0; +https://github.com/)"
}
NUMBER_PATTERN = re.compile(r"-?\d+")


def fetch_html() -> str:
    response = requests.get(TABLE_URL, headers=REQUEST_HEADERS, timeout=20)
    response.raise_for_status()
    return response.text


def first_number(text: str) -> int | None:
    match = NUMBER_PATTERN.search(text)
    return int(match.group()) if match else None


def parse_table(table) -> list[dict]:
    teams = []
    for row in table.find_all("tr"):
        if "table-header" in (row.get("class") or []):
            continue  # Kopfzeile

        cells = row.find_all("td")
        if len(cells) < 8:
            continue

        (
            rank_cell,
            team_cell,
            beg_cell,
            s_cell,
            n_cell,
            _spiele_cell,
            diff_cell,
            punkte_cell,
        ) = cells[:8]

        platz = first_number(rank_cell.get_text(strip=True))
        team_link = team_cell.find("a")
        name = (
            team_link["title"].strip()
            if team_link and team_link.has_attr("title")
            else team_cell.get_text(strip=True)
        )

        spiele = first_number(beg_cell.get_text(strip=True))
        siege = first_number(s_cell.get_text(strip=True))
        niederlagen = first_number(n_cell.get_text(strip=True))
        satzdifferenz = first_number(diff_cell.get_text(strip=True))
        punkte = first_number(punkte_cell.get_text(strip=True))

        if platz is None or not name:
            continue

        team = {
            "platz": platz,
            "name": name,
            "spiele": spiele,
            "siege": siege,
            "niederlagen": niederlagen,
            "punkte": punkte,
        }
        if satzdifferenz is not None:
            team["satzdifferenz"] = satzdifferenz

        teams.append(team)

    return teams


def main() -> int:
    html = fetch_html()
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if table is None:
        print("Konnte die Tabelle nicht finden.", file=sys.stderr)
        return 1

    teams = sorted(parse_table(table), key=lambda team: team["platz"])
    if not teams:
        print(
            "Keine Tabellendaten gefunden, table.json wird nicht veraendert.",
            file=sys.stderr,
        )
        return 1

    OUTPUT_PATH.write_text(
        json.dumps(teams, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{len(teams)} Teams gespeichert in {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
