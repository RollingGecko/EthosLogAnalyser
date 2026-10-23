# Usage

The user interface is available in German, English and Spanish. This guide quotes the English labels; the German label follows in parentheses where it helps.

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

The result is `dist\EthosLogAnalyser.exe`. GitHub also builds the EXE on every push; download it from the respective run under **Actions → Tests → Artifacts**. Released versions are attached to the [releases](https://github.com/RollingGecko/EthosLogAnalyser/releases) (see [Releasing](releasing.md)).

## Workflow

1. Tab **Data & settings** (Daten & Einstellungen): choose the folder with the Ethos CSV logs. Subfolders are included.
2. **Battery** (Akku):
   - **Cell chemistry** – LiPo, LiHV or Li-Ion. Selects the resting voltage → state of charge curve.
   - **Cell count** – 0 = detect automatically from the highest start voltage.
   - **Nominal capacity** – 0 = unknown; the capacity is then estimated from the flights. With a nominal capacity entered, state of charge, timer and the cell chemistry check become considerably more reliable.
3. **Analysis** (Auswertung):
   - **Min. flight duration** – shorter logs (ground tests, aborted flights) are skipped; default 120 s.
   - **Motor running from** – current above which the flight counts; default 1 A.
   - **Reserve at landing** – remaining charge the timer recommendation aims for; default 20 %.
   - **Voltage / current column** – only needed if automatic detection picks the wrong column; part of the column name is enough.
4. Click **Analyse** (Auswerten). Settings are saved to `%USERPROFILE%\.akku_analyse.json`.

## Language

The language is chosen under **Data & settings → Language** (Deutsch, English, Español). The window is rebuilt immediately in the new language; an existing analysis result, the selected flight, view and zoom are kept, so the logs do not have to be analysed again. The choice is saved together with the other settings and used at the next start. Without a saved choice, the app starts in the language of the operating system if it is supported, otherwise in English.

The language applies to the whole user interface, the text reports, the charts and the exports (file names, the text columns of the CSV table). The column names of the CSV export are internal identifiers and stay the same in every language.

## Tabs

| Tab | Contents |
|---|---|
| Summary (Zusammenfassung) | overview, battery condition, ageing, timer recommendation, drive, radio, warnings |
| Battery (Akku) | capacity, internal resistance, voltage at reference load, resting voltage, state of charge per flight |
| Load & flight profile (Belastung & Flugprofil) | throttle histogram, C-rate, energy per flight phase, peak power, g-forces, flight time vs. timer |
| Drive (Antrieb) | power vs. RPM curve, power demand at reference RPM, current sensor vs. ESC counter |
| Radio & onboard power (Funk & Bordnetz) | RSSI, VFR, receiver battery, receiver current and its spikes, transmitter battery |
| Single flight (Einzelflug) | time series in four views, detail report compared with the median of all flights |
| Table (Tabelle) | all metrics per flight |

### Single-flight view

- **Mouse wheel**: zoom around the cursor; **drag**: pan; **double-click**: whole flight.
- Buttons for take-off/landing (60 s each), zoom and pan; all charts stay time-aligned.
- **Current spike** (Stromspitze): jumps to a detected receiver current spike.
- The line above the charts shows all values at the time under the cursor.

## Export

Under **Data & settings → Export**: the table as CSV (semicolon separator, decimal comma – opens directly in a German or Spanish Excel) or report, table and all charts into a folder. Report texts, chart labels and file names are in the selected language.
