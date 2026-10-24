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

The result is `dist\EthosLogAnalyser.exe`. GitHub also builds a test EXE on every push and pull request; it shows *TEST VERSION* and a build tag (see [Acceptance testing a pull request](acceptance-testing.md)). Released versions are attached to the [releases](https://github.com/RollingGecko/EthosLogAnalyser/releases) (see [Releasing](releasing.md)).

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
   - **Period from / to** (Zeitraum von / bis) – only flights on these days (both inclusive); empty = no limit.
4. Click **Analyse** (Auswerten). Settings are saved to `%USERPROFILE%\.akku_analyse.json`.

### Year and month

After the first analysis, the row under the folder (box *Log data*) shows two drop-downs, **Year** (Jahr) and **Month** (Monat). They are a quick way to fill in *Period from / to*:

- **Year**: *all years* clears both fields; a year sets 1 January to 31 December of that year.
- **Month** (active once a year is chosen): *whole year*, or one month, which sets its first and last day.
- Choosing an entry analyses again at once. All tabs follow, exactly as if the dates had been typed in.
- Only years and months with flights of the selected model are offered (newest year first). They come from the last analysis without a period filter; before that, the dates in the log file names of the model stand in.
- Dates typed in by hand that are not exactly a year or a month show *custom period* (eigener Zeitraum).

### Several aircraft in one folder

The model is taken from the log file name: the part before the time stamp, e.g. `Viper-Jet` from `Viper-Jet-2026-04-19-13-25-36.csv` (hyphens and digits in the name are fine, a leading `-` is ignored; files without a model part count as “(unknown)”).

- If the folder holds logs of **one** model, nothing changes.
- If it holds logs of **several** models, they are never mixed: every analysis (all tabs, summary, table, export) covers exactly one model. By default it is the model with the newest log. Under the folder row of *Log data* a selector **Model** (Modell) appears – choosing another model analyses that one. The status line and the summary name the analysed model; the summary also lists the other models in the folder.
- The **battery settings** (cell chemistry, cell count, nominal capacity) are remembered per model and loaded when the model changes. Settings from before this feature stay with the first model analysed; another model starts with the defaults.
- A model **without stored battery settings** – a new model, or the very first start without any battery settings – shows a red hint: at the top of the summary, in the status line (“Battery settings missing for this model”) and below the battery fields in *Data & settings*. The analysis still runs with LiPo, automatic cell count and unknown capacity, but this assumption does not count as a setting, so state of charge, ageing and remaining capacity may be wrong. The hint disappears as soon as you choose the cell chemistry (even if it is LiPo) or enter a nominal capacity for that model; until then it comes back after a restart. Models that are already set up and the settings taken over from before this feature show no hint.
- The **period filter** applies within the selected model.
- The CSV export has a column *Model* (Modell).

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
| Logbook (Logbuch) | flights, flying days, total log duration, longest/shortest flight, total drawn charge; tables and bar charts per year and month; sortable list of flights |

### Working with charts

The same functions are available in every chart (built in one place, `plots/hover.py`, `plots/common.py` and `gui/app.py`, so new charts get them automatically):

- **Mouse-over**: a tooltip shows the data point nearest to the pointer – series name, x value (flight number and date, or the time) and y value with its unit. In stacked bars it shows the value of the segment.
- **Enlarge one chart**: a **double-click** into a chart, or **right-click → Enlarge this chart** (Dieses Diagramm vergrößern), opens just that chart in a window of its own that fills the screen – with its title, explanation line, axis labels, legend, helper lines (e.g. nominal capacity, 80 %), red circles, trend lines and secondary y axis. Example: in the *Load* tab, double-click *Peak C-rate per flight [C]*.
- **Enlarge the whole page**: the button *Enlarge whole page* (Ganze Seite vergrößern) in the toolbar below the charts, or the same entry in the right-click menu, opens all charts of the tab in one full-screen window. In that window a double-click on a chart (or right-click → *Enlarge this chart*) enlarges that chart on its own, as on the normal page.
- In both windows zoom, pan and save with the toolbar; the tooltip works there as well. **Esc** or *Close (Esc)* closes the window. While the toolbar's zoom or pan mode is active, double-click and right-click belong to that mode.
- **Time format**: all times are shown as min:s (`8:58`), from one hour on as h:min:s (`1:02:05`), rounded to whole seconds – in charts, tables, the summary and the timer.

### Single-flight view


- **Mouse wheel**: zoom around the cursor; **drag**: pan; *Whole flight* (Ganzer Flug) resets the zoom.
- **Double-click** (or right-click → *Enlarge this chart*) opens only the chart under the mouse full screen, with the time window shown in the tab, the min:s time axis, tooltip and vertical crosshair. *Whole flight* in that window shows the whole flight again. *Enlarge whole page* (button above the charts) opens all charts of the view; there, too, a double-click enlarges one chart, keeping the time window of the page window.
- Buttons for take-off/landing (60 s each), zoom and pan; all charts stay time-aligned.
- **Current spike** (Stromspitze): jumps to a detected receiver current spike.
- **Battery voltage per cell**: the battery voltage (measured and estimated resting voltage) is shown as mean cell voltage, total voltage / cell count, with the limit under load and the minimum resting voltage of the selected cell chemistry. The cell count is the one of the analysis (*Cell count* setting, or detected from the start voltage). If it is unknown, the chart shows the total voltage and says so. The receiver voltage is not converted.
- **Attitude view** (Fluglage): roll angle with the aileron stick, pitch angle with the elevator stick (angle on the left axis in °, stick on the right axis in %, both centred on zero), throttle with the rudder stick, g-load and altitude. Stick values are the Ethos channel values QR, HR, SR scaled to ±100 % (±1024 = full deflection); throttle is 0–100 %. Channels that are missing in the log or not moved are left out and listed in a note.
- The line above the charts shows all values at the time under the cursor; a vertical line marks that time in all charts.

### Logbook

The tab *Logbook* (Logbuch), the last tab, gives an overview of your flying. It covers the same flights as all other tabs: the selected model (see *Several aircraft in one folder*) within the period filter. From top to bottom:

1. **Scope line**: model and period (“all flights” without a period filter). If some flights have no date or no log duration, a line below says how many; they are left out of all totals.
2. **Totals**: number of flights with first and last date, flying days (different calendar days with at least one flight), total log duration, longest and shortest flight (with flight number and date) and the total drawn charge in Ah and mAh.
3. **Per year** and **per month** tables (flights, log duration, flying days, drawn mAh) and two bar charts: flights per month and log duration per month (only months with flights). The charts have the usual tooltip, double-click to enlarge and *Enlarge whole page*.
4. **Flights**: flight number, date, time, log duration and drawn mAh. A click on a column heading sorts by that column, a second click reverses the order (▲/▼); empty values stay at the end.

**Log duration** is the time from *motor armed* to *motor disarmed* in the log (column `dauer_s`), not the pure airborne time. The **drawn charge** follows the same rule as *Total drawn* in the summary: flights whose battery values are invalid (measurement errors) are not counted; the line says how many were left out. The totals are computed in `analysis/logbook.py` from the flight table.

## Export

Under **Data & settings → Export**: the table as CSV (semicolon separator, decimal comma – opens directly in a German or Spanish Excel) or report, table and all charts into a folder. Durations stay in seconds in the CSV (columns `…_s`, e.g. `dauer_s`), each followed by the same value as min:s text (`…_mmss`, e.g. `dauer_mmss`). Report texts, chart labels and file names are in the selected language.
