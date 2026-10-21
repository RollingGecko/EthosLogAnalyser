# Ethos-Logformat

Die App liest die CSV-Logs, die FrSky Ethos auf die SD-Karte schreibt (Dateiname `<Modell>-JJJJ-MM-TT-hh-mm-ss.csv`). Datum und Uhrzeit des Fluges stammen aus dem Dateinamen.

## Grundsätzliches

- Erste Zeile: Spaltennamen, Trennzeichen wird automatisch erkannt.
- Encoding meist cp1252; Ethos mischt in den Spaltennamen UTF-8 und Codepage (`Â°`, `au›en`). Die App korrigiert das beim Einlesen (`°`, `außen`).
- Jede Zeile enthält nur die Sensoren, die zu diesem Zeitpunkt einen neuen Wert hatten; doppelte Sensornamen bekommen `.1` angehängt.
- Zeit: Spalten `Date` und `Time` (`hh:mm:ss.fff`).

## Verwendete Spalten

Die Spalten werden über Teile des Namens gefunden (Groß-/Kleinschreibung egal). Steht in deinem Log ein anderer Name, lässt sich Spannung und Strom in den Einstellungen vorgeben.

| Zweck | erkannte Namen | Pflicht |
|---|---|---|
| Akkuspannung | `VFAS`, `ECU`, `Pack`, `Voltage`, `Volt`, `(V)` – nicht Rx/Tx/ADC | ja |
| Akkustrom | `Current`, `Curr`, `Amp`, `(A)` – nicht `RxCurrent` | ja |
| Drehzahl | `ESC RPM`, sonst `RPM` | nein |
| ESC-Verbrauch | `ESC consumption` | nein |
| Höhe | `Altitude`, `Höhe` | nein |
| Beschleunigung | `AccX`, `AccY`, `AccZ` | nein |
| Fluglage | `R.angle` / `Roll`, `P.angle` / `Pitch` / `Nick` | nein |
| Funk | `RSSI…`, `VFR…` (der jeweils aktive Empfänger) | nein |
| Empfänger | `RxBatt…`, `RxCurrent` | nein |
| Senderakku | `TxBat` | nein |
| Gas | `Gas`, `Thr` | nein |
| Knüppel | exakt `QR`/`Ail`, `HR`/`Ele`, `SR`/`Rud` | nein |
| Schalter | jede Spalte nur mit −1/0/1, die sich im Log ändert | nein |

Damit Knüppel, Gas und Schalter im Log stehen, müssen sie in Ethos unter **Logging** als Quellen ausgewählt sein.

## Übersprungene Logs

Im Reiter „Daten & Einstellungen“ steht für jede übersprungene Datei der Grund, z. B.:

- `zu kurz` – Motorlauf kürzer als die Mindest-Flugdauer
- `nur Nullwerte` – Bodenlog ohne Akku-Telemetrie
- `kein Motorstrom erkannt` – Strom nie über „Motor aktiv ab“
- `Spalten nicht gefunden` – Spannung/Strom im Log nicht vorhanden oder anders benannt
