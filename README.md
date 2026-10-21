# EthosLogAnalyser

[![Tests](https://github.com/RollingGecko/EthosLogAnalyser/actions/workflows/tests.yml/badge.svg)](https://github.com/RollingGecko/EthosLogAnalyser/actions/workflows/tests.yml)

Desktop-App (Python/Tkinter) zur Auswertung von **FrSky-Ethos-Fluglogs** (CSV) – mit Schwerpunkt auf Akkuzustand, Antrieb und Funk/Bordnetz. Entstanden für einen Elektro-Jet (Viper-Jet), funktioniert aber mit jedem Ethos-Log, das Spannung und Strom des Flugakkus enthält.

## Was die App auswertet

- **Akku:** Innenwiderstand, Spannung bei Referenzlast, geschätzte Kapazität, Restkapazität (SoH), Alterungstrend und Lebensdauer-Prognose, Timer-Empfehlung. Ladezustand am Ende per Ladungszählung mit Gegenprobe über die Ruhespannung.
- **Belastung & Flugprofil:** C-Rate, Leistung, Gas-Histogramm, Flugphasen, Energie je Phase, G-Kräfte.
- **Antrieb:** Kennlinie Drehzahl → Leistung, Plausibilität Strommessung gegen ESC-Zähler.
- **Funk & Bordnetz:** RSSI, VFR, Empfänger- und Senderakku, Empfängerstrom-Spitzen mit Zuordnung zu Schalter, Manöver, Start/Landung oder „ohne erkennbaren Anlass“.
- **Einzelflug:** Zeitverläufe mit Zoom und Fadenkreuz, Detailbericht mit Vergleich zum Median aller Flüge.

## Schnellstart

```bat
git clone https://github.com/RollingGecko/EthosLogAnalyser.git
cd EthosLogAnalyser
python -m venv .venv
.venv\Scripts\activate
pip install -e .
ethosloganalyser
```

Zum Ausprobieren liegen in `examples/logs/` drei echte Fluglogs. Die Windows-EXE baut `scripts\build_exe.bat`; GitHub baut sie zusätzlich bei jedem Push (Actions → Artifacts).

## Dokumentation

- [Benutzung](docs/benutzung.md) – Installation, Einstellungen, Reiter, Export
- [Methodik](docs/methodik.md) – wie Innenwiderstand, Ladezustand, Kapazität, Timer und Spitzen berechnet werden
- [Ethos-Logformat](docs/ethos-logformat.md) – welche Spalten die App erwartet

## Projektstruktur

```
src/ethosloganalyser/
  config.py       Zellchemie, Parameter, gespeicherte Einstellungen
  io/             Einlesen der Ethos-CSV-Logs
  analysis/       Einzelflug, Empfängerstrom-Spitzen, Gesamtauswertung, Bewertung
  report/         Textberichte
  plots/          Diagramme (ohne Oberfläche nutzbar)
  gui/            Tkinter-Oberfläche
tests/            pytest-Tests
docs/             Dokumentation
examples/logs/    Beispiel-Logs
ethos/            Lua-Skripte für den Sender
scripts/          Build der Windows-EXE
```

## Entwicklung

```bat
pip install -e ".[test]"
python -m pytest
```

Die Tests laufen bei jedem Push und Pull Request automatisch unter Linux und Windows.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
