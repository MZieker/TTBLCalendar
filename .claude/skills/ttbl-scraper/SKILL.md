---
name: ttbl-scraper
description: Wie man TTBL-Spielplan- und Tabellendaten für Borussia Düsseldorf (oder ähnliche Vereinsseiten) scrapt und ins games.json-/table.json-Format bringt. Anwenden bei jeder Aufgabe, die Daten von borussia-duesseldorf.com/profis/spielplan oder ttbl.de/bundesliga/table von diesem oder einem strukturell ähnlichen Verein/Team abruft, scripts/fetch_games.py oder scripts/fetch_table.py ändert, oder das games.json-/table.json-Format erweitert.
---

# TTBL-Scraper

Dieses Skill fasst zusammen, wie `scripts/fetch_games.py` und `scripts/fetch_table.py` die beiden Quellseiten parsen, welches JSON-Format sie erzeugen und welche Fallstricke bereits gelöst wurden. Vor Änderungen an diesen Skripten oder an einem strukturell vergleichbaren neuen Scraper lesen.

## Quelle 1: Spielplan (borussia-duesseldorf.com)

**URL:** `https://www.borussia-duesseldorf.com/profis/spielplan`

**Struktur:** Eine `<table class="ce-table">` direkt unter einer `<h2>`/`<h3>`-Überschrift, deren Text `"bundesliga"` enthält (case-insensitive). Es gibt auf derselben Seite noch eine zweite Tabelle für den DTTB-Pokal — deshalb **nicht** einfach die erste `<table class="ce-table">` der Seite nehmen, sondern gezielt über die Überschrift suchen:

```python
def find_bundesliga_table(soup):
    for heading in soup.find_all(["h2", "h3"]):
        if "bundesliga" in heading.get_text(strip=True).lower():
            table = heading.find_next("table", class_="ce-table")
            if table is not None:
                return table
    return soup.find("table", class_="ce-table")  # Fallback
```

**Zeilen/Spalten:** Jede Datenzeile ist ein `<tr>` mit `<td>`-Zellen in der Reihenfolge `Spieltag, Ort, Tag, Datum, Uhrzeit, Heim, Gast, Ergebnis, Tickets` (mind. 7 Zellen nötig). Kopfzeilen enthalten ein `<b>`-Tag und werden übersprungen (`row.find("b") is not None`).

**Heim/Auswärts-Erkennung:** Nicht über die Ort-Spalte, sondern über die Mannschaftsspalten:
- `TEAM_NAME` ("Borussia Düsseldorf") in der `Heim`-Zelle → Heimspiel, Gegner = `Gast`-Zelle.
- `TEAM_NAME` in der `Gast`-Zelle → Auswärtsspiel, Gegner = `Heim`-Zelle.
- Sonst: Zeile betrifft nicht das Team → überspringen.

**Ort/Venue:** Bei Heimspielen steht der Hallenname direkt in der Ort-Spalte (`"TBD"` bzw. leer → `"Ort noch offen"`). Bei Auswärtsspielen zeigt die Seite dort das Wort `"auswärts"` — kein echter Hallenname verfügbar, daher wird die Venue bei Auswärtsspielen fest auf den String `"auswärts"` gesetzt statt den Seiteninhalt zu übernehmen.

**Datum/Uhrzeit-Validierung:** `DATE_PATTERN = r"^\d{2}\.\d{2}\.\d{4}$"`, `TIME_PATTERN = r"^\d{2}:\d{2}$"`. Bei ungültigem Zeitformat wird `"TBD"` als Uhrzeit gesetzt statt die Zeile zu verwerfen.

## Quelle 2: Tabelle (ttbl.de)

**URL:** `https://www.ttbl.de/bundesliga/table/2026-2027/1` (Saison-Segment `2026-2027` im Pfad ändert sich pro Saison)

**Struktur:** Die Seite ist eine Next.js-App; sie enthält aber zuverlässig **genau eine** `<table>` im gesamten HTML (verifiziert per `grep -c "<table"` gegen die Live-Seite). `soup.find("table")` reicht daher aus, kein spezifischer Selektor nötig.

**Wichtig beim Debuggen dieser Seite:** Das rohe HTML enthält eingebettete Zeilenumbrüche mitten in Attributwerten (Next.js RSC-Streaming-Format), wodurch naive zeilenbasierte Tools (`grep -n`, `sed -n 'Np'`) die Tabelle nicht finden, obwohl sie da ist. Erst `tr -d '\n\r'` auf das HTML anwenden (alles zu einer Zeile zusammenfassen), dann suchen. Ein echter HTML-Parser (BeautifulSoup) hat dieses Problem nicht.

**Zeilen/Spalten:** `<tr>` mit `<td>`-Zellen in der Reihenfolge `Rang, Team, Beg. (Begegnungen), S (Siege), N (Niederlagen), Spiele (gewonnene:verlorene Einzelspiele als "3 : 0"), +/- (Differenz aus der Spiele-Spalte), Punkte (eigene:gegnerische Punkte als "2 : 0")` — mind. 8 Zellen nötig. Kopfzeile hat die Klasse `table-header` und wird übersprungen.

**Teamname:** Aus dem `title`-Attribut des `<a>`-Tags in der Team-Zelle lesen (`team_link["title"]`), **nicht** aus dem sichtbaren Text — dieser wechselt responsive zwischen Vollname und 3-Buchstaben-Kürzel je nach Viewport-Klasse (`max-lg:hidden` / `lg:hidden`).

**Zahlen extrahieren:** Alle numerischen Zellen (auch negative wie `-3` in der +/--Spalte) mit `NUMBER_PATTERN = re.compile(r"-?\d+")` und `first_number()` parsen, nicht mit `int(text)` direkt (Zellen wie `"3 : 0"` enthalten mehr als eine Zahl — `first_number` nimmt bewusst nur die erste).

**Punkte-Feld:** Die Punkte-Spalte zeigt `"eigene : gegnerische"` Punkte (2 Punkte pro Sieg, 0 pro Niederlage, keine Unentschieden — verifiziert: der Wert entspricht immer `2 * Siege : 2 * Niederlagen`). Nur die erste Zahl (eigene Punkte) wird als `punkte` übernommen.

**Satzdifferenz-Feld:** Die `+/--Spalte` der Seite ist laut deren eigener Legende die *Differenz gewonnener und verlorener Spiele* (Einzelspiele/Rubber, nicht einzelne Sätze). Es gibt auf der Seite keine echte Satz-Statistik. `satzdifferenz` im JSON ist also eine bewusste Näherung — Kommentar im Code lässt das nicht verschwinden, falls die Seite doch einmal echte Satzdaten ergänzt.

## JSON-Ausgabeformate

**`games.json`** — Array, sortiert nach Datum/Uhrzeit, enthält nur noch anstehende Spiele:

```json
{
  "datum": "26.08.2026",
  "uhrzeit": "18:30",
  "gegner": "SV Werder Bremen",
  "ort": "auswärts",
  "heimspiel": false
}
```

**`table.json`** — Array, sortiert nach `platz`:

```json
{
  "platz": 1,
  "name": "Borussia Düsseldorf",
  "spiele": 1,
  "siege": 1,
  "niederlagen": 0,
  "punkte": 2,
  "satzdifferenz": 3
}
```

`satzdifferenz` fehlt im Objekt, wenn sie sich nicht extrahieren ließ (`if satzdifferenz is not None: team["satzdifferenz"] = ...`) — kein `null`-Wert, sondern das Feld wird ausgelassen. Der Frontend-Code (`script.js`) verwendet dieses Feld aktuell nicht, verlässt sich also nicht auf seine Anwesenheit.

Beide Dateien: UTF-8, `json.dumps(..., ensure_ascii=False, indent=2)` + abschließender Zeilenumbruch — Umlaute bleiben lesbar im Klartext statt als `\uXXXX`-Escapes.

## Bekannte Fallstricke

1. **Layoutänderungen der Quellseite (kein Absturz, sondern Exit-Code 1 + stderr-Meldung):** Beide `main()`-Funktionen brechen kontrolliert ab, wenn die erwartete Tabelle nicht gefunden wird (`find_bundesliga_table` bzw. `soup.find("table")` liefert `None`) oder wenn nach dem Parsen keine Datensätze übrig sind. In beiden Fällen wird `games.json`/`table.json` **nicht überschrieben** — die zuletzt bekannten guten Daten bleiben erhalten, statt durch eine leere Datei ersetzt zu werden. Das ist bewusst so gebaut, damit ein Layout-Bruch der Quellseite nicht die Website mit leeren Daten kaputt macht.
2. **Nicht erreichbare Seite:** `response.raise_for_status()` direkt nach dem `requests.get()` — bei HTTP-Fehlern (4xx/5xx) oder Timeout (`timeout=20`) bricht das Skript mit einer Exception ab (nicht abgefangen), was im GitHub-Actions-Workflow den Job als fehlgeschlagen markiert. Auch hier bleibt die vorherige `games.json`/`table.json` im Repo unverändert, da der Commit-Schritt nie erreicht wird.
3. **Vergangene Spiele herausfiltern:** Nur `fetch_games.py` filtert; passiert **nach** dem Sortieren, über `is_upcoming(game, date.today())` — Vergleich ist rein datumsbasiert (nicht datetime-genau), ein Spiel am heutigen Tag bleibt also auch dann in `games.json`, wenn die Startzeit an diesem Tag schon vorbei ist. `fetch_table.py` filtert nichts, da eine Tabelle immer den Gesamtstand zeigt.
4. **User-Agent:** Beide Skripte senden einen expliziten `User-Agent`-Header (`REQUEST_HEADERS`), da manche Seiten Requests ohne Browser-artigen UA blockieren oder anders ausliefern.
5. **Saison-Rollover:** Die TTBL-Tabellen-URL enthält die Saison im Pfad (`/table/2026-2027/1`). Beim Saisonwechsel muss `TABLE_URL` in `fetch_table.py` manuell aktualisiert werden — das Skript erkennt das nicht automatisch.

## Wann dieses Skill anwenden

- Bei jeder Aufgabe, die `scripts/fetch_games.py` oder `scripts/fetch_table.py` ändert oder erweitert (z. B. neue Felder, andere Filterlogik, anderer Saison-Pfad).
- Bei jeder Aufgabe, die TTBL-Daten (Spielplan oder Tabelle) für Borussia Düsseldorf **oder ein anderes TTBL-Team** von diesen oder strukturell ähnlichen Vereinsseiten abruft — die hier dokumentierten Selektoren/Strategien (Überschriften-basierte Tabellensuche, `title`-Attribut statt sichtbarem Text, `tr -d '\n'` beim manuellen Debuggen von Next.js-Seiten) übertragen sich direkt.
- Bei jeder Aufgabe, die das `games.json`- oder `table.json`-Format erweitert — damit neue Felder konsistent zum bestehenden Schema (Feldnamen auf Deutsch, `heimspiel` als Boolean, optionale Felder werden ausgelassen statt `null` gesetzt) hinzugefügt werden und der Frontend-Code (`script.js`, siehe `CLAUDE.md`) im selben Zug angepasst wird.
