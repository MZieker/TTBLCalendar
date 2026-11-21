# TTBL Calendar – Borussia Düsseldorf

Eine kleine, statische Fan-Website mit dem Spielplan und der aktuellen Tabelle von **Borussia Düsseldorf** in der Tischtennis-Bundesliga (TTBL).

**🔗 Live: [mzieker.github.io/TTBLCalendar](https://mzieker.github.io/TTBLCalendar/)**

- 📅 **Spielplan**: alle kommenden Heim- und Auswärtsspiele, mit Countdown zum nächsten Spiel
- 🏆 **Tabelle**: der aktuelle Stand der TTBL, Borussia Düsseldorf ist hervorgehoben
- 📄 **PDF-Download**: der Spielplan zum Ausdrucken (`spielplan.pdf`)
- 🌙 **Dark Mode**: umschaltbar, folgt beim ersten Besuch der Systemeinstellung

Die Daten werden **täglich automatisch** per GitHub Actions aktualisiert, ohne Server, Datenbank oder Build-Schritt.

## So funktioniert's

```
borussia-duesseldorf.com ──► scripts/fetch_games.py ──► games.json ──┐
                                                                     ├──► script.js ──► Website
ttbl.de                  ──► scripts/fetch_table.py ──► table.json ──┘

games.json ──► scripts/generate_pdf.py ──► spielplan.pdf
```

| Datei | Aufgabe |
| --- | --- |
| `scripts/fetch_games.py` | Scrapt den Spielplan von [borussia-duesseldorf.com/profis/spielplan](https://www.borussia-duesseldorf.com/profis/spielplan) und speichert nur kommende Spiele |
| `scripts/fetch_table.py` | Scrapt die Tabelle von [ttbl.de/bundesliga/table](https://www.ttbl.de/bundesliga/table). Die Seite leitet automatisch auf die aktuelle Saison und den aktuellen Spieltag weiter |
| `scripts/generate_pdf.py` | Erzeugt aus `games.json` das PDF `spielplan.pdf` (mit `reportlab`) |
| `index.html`, `style.css`, `script.js` | Das Frontend: reines HTML/CSS/JavaScript, kein Framework |
| `.github/workflows/update-games.yml` | Läuft täglich um 05:00 UTC, führt alle drei Skripte aus und committet geänderte Daten |

Das Frontend ruft keine externen APIs auf. Es lädt nur die mitgelieferten Dateien `games.json` und `table.json`.

## Lokal starten

Die Seite muss über einen lokalen Webserver laufen. Wenn du `index.html` direkt als Datei öffnest (`file://`), blockiert der Browser das Laden der JSON-Dateien.

```bash
python -m http.server 8000
```

Danach im Browser [http://localhost:8000](http://localhost:8000) öffnen.

## Daten manuell aktualisieren

```bash
pip install -r scripts/requirements.txt

python scripts/fetch_games.py    # Spielplan  -> games.json
python scripts/fetch_table.py    # Tabelle    -> table.json
python scripts/generate_pdf.py   # PDF        -> spielplan.pdf
```

Alternativ den Workflow auf GitHub unter **Actions → „Update TTBL games and table“ → „Run workflow“** von Hand starten.

## Datenformat

**`games.json`**: ein Eintrag pro kommendem Spiel, sortiert nach Datum:

```json
{ "datum": "26.08.2026", "uhrzeit": "18:30", "gegner": "SV Werder Bremen", "ort": "auswärts", "heimspiel": false }
```

**`table.json`**: ein Eintrag pro Team, sortiert nach Platz:

```json
{ "platz": 1, "name": "Borussia Düsseldorf", "spiele": 8, "siege": 8, "niederlagen": 0, "punkte": 16, "satzdifferenz": 19 }
```

> `satzdifferenz` entspricht der Spalte `+/-` auf ttbl.de, also der Differenz der gewonnenen und verlorenen **Einzelspiele**.

## Hinweise

- Die Scraper hängen am HTML-Aufbau der Quellseiten. Wenn sich deren Layout ändert, bricht das jeweilige Skript mit einer Fehlermeldung ab. Die zuletzt gespeicherten Daten bleiben dann unverändert, und der GitHub-Actions-Lauf wird rot.
- Der Vereinsname `"Borussia Düsseldorf"` muss in `scripts/fetch_games.py` (`TEAM_NAME`) und `script.js` (`OWN_TEAM_NAME`) exakt so geschrieben sein, wie ihn die Quellseiten verwenden. Sonst funktionieren die Heim/Auswärts-Erkennung und die Hervorhebung in der Tabelle nicht mehr.

## Disclaimer

Dies ist ein inoffizielles Fan-Projekt und steht in keiner Verbindung zu Borussia Düsseldorf oder der Tischtennis-Bundesliga. Alle Daten stammen von den öffentlich zugänglichen Websites [borussia-duesseldorf.com](https://www.borussia-duesseldorf.com) und [ttbl.de](https://www.ttbl.de).
