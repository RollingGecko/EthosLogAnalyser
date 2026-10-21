# EthosLogAnalyser

Desktop-App (Python/Tkinter) zur Auswertung von **FrSky-Ethos-Fluglogs** (CSV) – mit Schwerpunkt auf Akkuzustand, Antrieb und Funk/Bordnetz. Entstanden für einen Elektro-Jet (Viper-Jet), funktioniert aber mit jedem Ethos-Log, das Spannung und Strom des Flugakkus enthält.

## Was die App auswertet

- **Akku:** Innenwiderstand (gesamt und im Flugverlauf), Spannung bei Referenzlast, geschätzte Kapazität, Restkapazität (SoH), Alterungstrend und Lebensdauer-Prognose, Timer-Empfehlung. Ladezustand am Ende per Ladungszählung mit Gegenprobe über die Ruhespannung.
- **Belastung & Flugprofil:** C-Rate, Leistung, Gas-Histogramm, Flugphasen (Steigflug/Reise/Sinkflug), Energie je Phase, G-Kräfte.
- **Antrieb:** Kennlinie Drehzahl → Leistung (Hinweis auf Verschleiß/Fremdkörper), Plausibilität Strommessung gegen ESC-Zähler.
- **Funk & Bordnetz:** RSSI, VFR, Empfänger- und Senderakku, Empfängerstrom-Spitzen mit Zuordnung zu Schalter, Manöver, Start/Landung oder „ohne erkennbaren Anlass“.
- **Einzelflug:** Zeitverläufe mit Zoom, Verschieben und Fadenkreuz, Detailbericht mit Vergleich zum Median aller Flüge.
- **Auffälligkeiten:** Grenzwert-Warnungen und Ausreißer-Erkennung über alle Flüge.

## Installation

Python 3.9 oder neuer (Tkinter ist enthalten):

```bash
pip install -r requirements.txt
python EthosLogAnalyser.py
```

### EXE unter Windows bauen

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed EthosLogAnalyser.py
```

Die EXE liegt danach in `dist/`.

## Benutzung

1. Im Reiter **Daten & Einstellungen** den Ordner mit den Ethos-CSV-Logs wählen (Unterordner werden mit durchsucht).
2. Zellchemie, Zellenzahl (0 = automatisch) und Nennkapazität eintragen.
3. **Auswerten** klicken. Logs kürzer als die Mindest-Flugdauer (Standard 2 min) werden übersprungen.

Zum Ausprobieren liegen im Ordner `beispiel-logs/` drei echte Fluglogs.

## Grenzen

- Ohne Temperaturdaten: Der Innenwiderstand hängt stark von der Akku-Temperatur ab.
- Keine Einzelzellspannungen: schwache Zellen sind nicht erkennbar.
- Ladezustand und Timer hängen von der richtigen Nennkapazität ab.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
