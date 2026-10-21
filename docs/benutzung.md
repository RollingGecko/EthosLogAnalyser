# Benutzung

## Installation

Voraussetzung ist Python 3.9 oder neuer (Tkinter ist in der Windows-Installation enthalten).

```bat
git clone https://github.com/RollingGecko/EthosLogAnalyser.git
cd EthosLogAnalyser
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Starten:

```bat
ethosloganalyser
```

oder gleichwertig `python -m ethosloganalyser`. Durch `-e` (editierbare Installation) wirken Änderungen am Code sofort, ohne neu zu installieren.

## Windows-EXE bauen

In der aktivierten virtuellen Umgebung:

```bat
scripts\build_exe.bat
```

Die fertige Datei liegt in `dist\EthosLogAnalyser.exe`. Bei jedem Push baut GitHub die EXE außerdem automatisch; sie ist im jeweiligen Lauf unter **Actions → Tests → Artifacts** herunterladbar.

## Ablauf

1. Reiter **Daten & Einstellungen**: Ordner mit den Ethos-CSV-Logs wählen. Unterordner werden mit durchsucht.
2. Akku eintragen:
   - **Zellchemie** – LiPo, LiHV oder Li-Ion. Bestimmt die Kennlinie Ruhespannung → Ladezustand.
   - **Zellenzahl** – 0 = automatisch aus der höchsten Startspannung.
   - **Nennkapazität** – 0 = unbekannt, dann wird die Kapazität aus den Flügen geschätzt. Mit eingetragener Kapazität werden Ladezustand, Timer und Zellchemie-Prüfung deutlich verlässlicher.
3. Auswertung:
   - **Min. Flugdauer** – kürzere Logs (Bodentests, Abbrüche) werden übersprungen, Standard 120 s.
   - **Motor aktiv ab** – Strom, ab dem der Flug zählt, Standard 1 A.
   - **Reserve bei Landung** – Restladung, für die der Timer berechnet wird, Standard 20 %.
   - **Spalte Spannung / Strom** – nur nötig, wenn die automatische Erkennung die falsche Spalte nimmt (Teil des Spaltennamens genügt).
4. **Auswerten** klicken. Die Einstellungen werden in `%USERPROFILE%\.akku_analyse.json` gespeichert.

## Reiter

| Reiter | Inhalt |
|---|---|
| Zusammenfassung | Übersicht, Akkuzustand, Alterung, Timer-Empfehlung, Antrieb, Funk, Warnungen |
| Akku | Kapazität, Innenwiderstand, Spannung bei Referenzlast, Ruhespannung, Ladezustand je Flug |
| Belastung & Flugprofil | Gas-Histogramm, C-Rate, Energie je Flugphase, Spitzenleistung, G-Kräfte, Flugzeit gegen Timer |
| Antrieb | Kennlinie Leistung/Drehzahl, Leistungsbedarf bei Referenzdrehzahl, Strommessung gegen ESC-Zähler |
| Funk & Bordnetz | RSSI, VFR, Empfängerakku, Empfängerstrom und seine Spitzen, Senderakku |
| Einzelflug | Zeitverläufe in vier Ansichten, Detailbericht mit Vergleich zum Median aller Flüge |
| Tabelle | Alle Kennwerte je Flug |

### Einzelflug bedienen

- **Mausrad**: zoomen um die Mausposition, **Ziehen**: verschieben, **Doppelklick**: ganzer Flug.
- Knöpfe für Start/Landung (je 60 s), Zoom und Verschieben; alle Diagramme bleiben zeitlich gekoppelt.
- **Stromspitze**: springt zu einer erkannten Empfängerstrom-Spitze.
- Die Zeile über den Diagrammen zeigt alle Werte zum Zeitpunkt unter der Maus.

## Export

Unter **Daten & Einstellungen → Export**: Tabelle als CSV (Semikolon, Dezimalkomma – direkt in Excel) oder Bericht, Tabelle und alle Diagramme in einen Ordner.
