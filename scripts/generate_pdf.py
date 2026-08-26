#!/usr/bin/env python3
"""Erzeugt aus games.json ein PDF (spielplan.pdf) mit dem Spielplan von
Borussia Duesseldorf.

Liest die von scripts/fetch_games.py geschriebene games.json und rendert
daraus eine Tabelle mit allen zukuenftigen Spielen (Datum, Uhrzeit, Gegner,
Ort, Heim/Auswaerts) im Rot/Weiss-Farbschema des Vereins.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

GAMES_PATH = Path(__file__).resolve().parent.parent / "games.json"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "spielplan.pdf"

BD_RED = colors.HexColor("#c8102e")
BD_RED_DARK = colors.HexColor("#93001f")
BD_WHITE = colors.HexColor("#ffffff")
BD_GRAY = colors.HexColor("#f4f4f4")
BD_TEXT = colors.HexColor("#1a1a1a")
BD_TEXT_LIGHT = colors.HexColor("#6b6b6b")

TITLE_STYLE = ParagraphStyle(
    "Title",
    fontName="Helvetica-Bold",
    fontSize=24,
    textColor=BD_RED,
    spaceAfter=2,
)
SUBTITLE_STYLE = ParagraphStyle(
    "Subtitle",
    fontName="Helvetica",
    fontSize=13,
    textColor=BD_TEXT_LIGHT,
    spaceAfter=18,
)


def load_games() -> list[dict]:
    if not GAMES_PATH.exists():
        print(f"{GAMES_PATH} nicht gefunden.", file=sys.stderr)
        return []
    return json.loads(GAMES_PATH.read_text(encoding="utf-8"))


def is_upcoming(game: dict, today: date) -> bool:
    day, month, year = (int(part) for part in game["datum"].split("."))
    return date(year, month, day) >= today


def build_table(games: list[dict]) -> Table:
    header = ["Datum", "Uhrzeit", "Gegner", "Ort", ""]
    rows = [header]
    for game in games:
        rows.append(
            [
                game["datum"],
                game.get("uhrzeit", "TBD"),
                game["gegner"],
                game["ort"],
                "Heim" if game["heimspiel"] else "Auswärts",
            ]
        )

    table = Table(rows, colWidths=[22 * mm, 18 * mm, 55 * mm, 45 * mm, 22 * mm], repeatRows=1)

    style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), BD_RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), BD_WHITE),
        ("ALIGN", (0, 0), (1, -1), "CENTER"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 1, BD_RED_DARK),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, BD_GRAY),
        ("TEXTCOLOR", (0, 1), (-1, -1), BD_TEXT),
    ]

    for row_index, game in enumerate(games, start=1):
        if row_index % 2 == 0:
            style.append(("BACKGROUND", (0, row_index), (-1, row_index), BD_GRAY))
        badge_color = BD_RED if game["heimspiel"] else BD_TEXT_LIGHT
        style.append(("TEXTCOLOR", (4, row_index), (4, row_index), badge_color))
        style.append(("FONTNAME", (4, row_index), (4, row_index), "Helvetica-Bold"))

    table.setStyle(TableStyle(style))
    return table


def main() -> int:
    games = load_games()
    today = date.today()
    games = sorted(
        (game for game in games if is_upcoming(game, today)),
        key=lambda game: datetime.strptime(game["datum"], "%d.%m.%Y"),
    )

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        title="Spielplan TTBL - Borussia Düsseldorf",
    )

    story = [
        Paragraph("Borussia Düsseldorf", TITLE_STYLE),
        Paragraph("Spielplan TTBL", SUBTITLE_STYLE),
    ]

    if games:
        story.append(build_table(games))
    else:
        story.append(
            Paragraph(
                "Aktuell sind keine anstehenden Spiele bekannt.",
                ParagraphStyle("Empty", fontName="Helvetica", fontSize=11, textColor=BD_TEXT),
            )
        )

    story.append(Spacer(1, 12 * mm))
    story.append(
        Paragraph(
            f"Stand: {today.strftime('%d.%m.%Y')} · Inoffizielle Fan-Seite · Daten ohne Gewähr",
            ParagraphStyle("Footer", fontName="Helvetica", fontSize=8, textColor=BD_TEXT_LIGHT),
        )
    )

    doc.build(story)
    print(f"{len(games)} Spiele in {OUTPUT_PATH} gespeichert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
