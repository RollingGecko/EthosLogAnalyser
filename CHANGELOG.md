# Änderungen

## 0.2.0

- Code als Python-Paket `ethosloganalyser` aufgeteilt: `io` (Einlesen), `analysis` (Auswertung), `report` (Texte), `plots` (Diagramme), `gui` (Oberfläche). Die Auswertung ist unverändert – geprüft an 73 Logdateien (35 Flüge) mit identischen Tabellen, Texten und Diagrammen.
- Installation über `pyproject.toml`; Start mit `ethosloganalyser` oder `python -m ethosloganalyser`.
- Automatische Tests (pytest) für Einlesen, Einzelflug, Empfängerstrom-Spitzen, Gesamtauswertung, Berichte, Diagramme und Oberfläche; laufen bei jedem Push auf GitHub unter Linux und Windows.
- GitHub baut bei jedem Push die Windows-EXE (`scripts/build_exe.bat`).
- Dokumentation in `docs/`: Benutzung, Methodik, Ethos-Logformat.
- Behoben: Dezimalkomma in Logwerten wurde mit pandas 3 nicht mehr umgewandelt.
- Behoben: Logs ohne Datumsspalte, die über Mitternacht laufen, führten mit pandas 3 zu einem Absturz.

## 0.1.0

- Erste Version (`EthosLogAnalyser.py`).
