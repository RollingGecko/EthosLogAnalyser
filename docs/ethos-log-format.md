# Ethos log format

The app reads the CSV logs that FrSky Ethos writes to the SD card (file name `<model>-YYYY-MM-DD-hh-mm-ss.csv`). Date and time of the flight are taken from the file name.

## Basics

- First row: column names; the separator is detected automatically.
- Encoding is usually cp1252; Ethos mixes UTF-8 and code page characters in column names (`Â°`, `au›en`). The app fixes this on import (`°`, `außen`).
- Each row only contains the sensors that had a new value at that moment; duplicate sensor names get `.1` appended.
- Time: columns `Date` and `Time` (`hh:mm:ss.fff`).

## Columns used

Columns are matched by parts of their name (case-insensitive). If your log uses a different name, voltage and current columns can be set in the settings.

| Purpose | recognised names | required |
|---|---|---|
| battery voltage | `VFAS`, `ECU`, `Pack`, `Voltage`, `Volt`, `(V)` – not Rx/Tx/ADC | yes |
| battery current | `Current`, `Curr`, `Amp`, `(A)` – not `RxCurrent` | yes |
| RPM | `ESC RPM`, otherwise `RPM` | no |
| ESC consumption | `ESC consumption` | no |
| altitude | `Altitude`, `Höhe` | no |
| acceleration | `AccX`, `AccY`, `AccZ` | no |
| attitude | `R.angle` / `Roll`, `P.angle` / `Pitch` / `Nick` | no |
| radio | `RSSI…`, `VFR…` (whichever receiver is active) | no |
| receiver | `RxBatt…`, `RxCurrent` | no |
| transmitter battery | `TxBat` | no |
| throttle | `Gas`, `Thr` | no |
| sticks | exactly `QR`/`Ail`, `HR`/`Ele`, `SR`/`Rud` | no |
| switches | any column with only −1/0/1 that changes during the log | no |

For sticks, throttle and switches to appear in the log, they must be selected as sources under **Logging** in Ethos.

## Skipped logs

The tab “Data & settings” lists the reason for every skipped file in the selected language, e.g.:

- `too short` – motor run shorter than the minimum flight duration
- `only zero values` – ground log without battery telemetry
- `no motor current detected` – current never above the “motor running” threshold
- `Columns not found` – voltage/current not in the log or named differently
