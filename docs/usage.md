# Usage

The app's user interface is in German. This guide quotes UI labels exactly as they appear in the app, with an English explanation.

## Installation

Requires Python 3.9 or newer (Tkinter ships with the Windows installer).

```bat
git clone https://github.com/RollingGecko/EthosLogAnalyser.git
cd EthosLogAnalyser
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

Start the app:

```bat
ethosloganalyser
```

or, equivalently, `python -m ethosloganalyser`. Thanks to `-e` (editable install), code changes take effect immediately without reinstalling.

## Building the Windows EXE

With the virtual environment activated:

```bat
scripts\build_exe.bat
```

The result is `dist\EthosLogAnalyser.exe`. GitHub also builds the EXE on every push; download it from the respective run under **Actions → Tests → Artifacts**.

## Workflow

1. Tab **Daten & Einstellungen** (data & settings): choose the folder with the Ethos CSV logs. Subfolders are included.
2. Battery (**Akku**):
   - **Zellchemie** (cell chemistry) – LiPo, LiHV or Li-Ion. Selects the resting voltage → state of charge curve.
   - **Zellenzahl** (cell count) – 0 = detect automatically from the highest start voltage.
   - **Nennkapazität** (nominal capacity) – 0 = unknown; the capacity is then estimated from the flights. With a nominal capacity entered, state of charge, timer and the cell chemistry check become considerably more reliable.
3. Analysis (**Auswertung**):
   - **Min. Flugdauer** (minimum flight duration) – shorter logs (ground tests, aborted flights) are skipped; default 120 s.
   - **Motor aktiv ab** (motor running above) – current above which the flight counts; default 1 A.
   - **Reserve bei Landung** (reserve at landing) – remaining charge the timer recommendation aims for; default 20 %.
   - **Spalte Spannung / Strom** (voltage / current column) – only needed if automatic detection picks the wrong column; part of the column name is enough.
4. Click **Auswerten** (analyse). Settings are saved to `%USERPROFILE%\.akku_analyse.json`.

## Tabs

| Tab | Contents |
|---|---|
| Zusammenfassung (summary) | overview, battery condition, ageing, timer recommendation, drive, radio, warnings |
| Akku (battery) | capacity, internal resistance, voltage at reference load, resting voltage, state of charge per flight |
| Belastung & Flugprofil (load & flight profile) | throttle histogram, C-rate, energy per flight phase, peak power, g-forces, flight time vs. timer |
| Antrieb (drive) | power vs. RPM curve, power demand at reference RPM, current sensor vs. ESC counter |
| Funk & Bordnetz (radio & onboard power) | RSSI, VFR, receiver battery, receiver current and its spikes, transmitter battery |
| Einzelflug (single flight) | time series in four views, detail report compared with the median of all flights |
| Tabelle (table) | all metrics per flight |

### Single-flight view

- **Mouse wheel**: zoom around the cursor; **drag**: pan; **double-click**: whole flight.
- Buttons for take-off/landing (60 s each), zoom and pan; all charts stay time-aligned.
- **Stromspitze** (current spike): jumps to a detected receiver current spike.
- The line above the charts shows all values at the time under the cursor.

## Export

Under **Daten & Einstellungen → Export**: the table as CSV (semicolon separator, decimal comma – opens directly in a German Excel) or report, table and all charts into a folder.
