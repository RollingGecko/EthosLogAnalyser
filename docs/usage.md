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

## Window layout

The window has four areas, shown as tabs at the top:

| Area | Contents |
|---|---|
| Logbook (Logbuch) | start page: totals, tables per year and month, list of flights (see *Logbook* below) |
| Single flight (Einzelflug) | one flight from the flight database: time series in four views and the detail report |
| Statistics (Statistik) | pages over all flights of the analysed model: Summary, Battery, Load & flight profile, Drive, Radio & onboard power, Table (smaller tabs inside the area) |
| Data & settings (Daten & Einstellungen) | flight database, log folder, battery and analysis settings, language, export |

*Logbook* and *Single flight* show the flights of the flight database. *Statistics* still shows the result of the
folder analysis (*Analyse* under *Log data*) and will work on the database later.

The **status line** at the bottom shows the state of the flight database (flights, aircraft, first and last
flight, and how many logs are not counted as flights) in the areas *Logbook* and *Single flight*. In the
*Statistics* pages it shows the result of the analysis, as before.

## Workflow

1. Area **Data & settings** (Daten & Einstellungen): import the logs into the flight database (*Import folder …*) for the single flight, and choose the folder with the Ethos CSV logs for the logbook and statistics. Subfolders are included.
2. **Battery** (Akku):
   - **Cell chemistry** – LiPo, LiHV or Li-Ion. Selects the resting voltage → state of charge curve.
   - **Cell count** – 0 = detect automatically from the highest start voltage.
   - **Nominal capacity** – 0 = unknown; the capacity is then estimated from the flights. With a nominal capacity entered, state of charge, timer and the cell chemistry check become considerably more reliable.
3. **Analysis** (Auswertung):
   - **Min. flight duration** – shorter logs (ground tests, aborted flights) are skipped; default 120 s.
   - **Motor running from** – current above which the flight counts; default 1 A.
   - **Reserve at landing** – remaining charge the timer recommendation aims for; default 20 %.
   - **Voltage / current column** – only needed if automatic detection picks the wrong column; part of the column name is enough.
4. Click **Analyse** (Auswerten); the app shows *Statistics → Summary*. Settings are saved to `%USERPROFILE%\.akku_analyse.json`.

### Several aircraft in one folder

The model is taken from the log file name: the part before the time stamp, e.g. `Viper-Jet` from `Viper-Jet-2026-04-19-13-25-36.csv` (hyphens and digits in the name are fine, a leading `-` is ignored; files without a model part count as “(unknown)”).

- If the folder holds logs of **one** model, nothing changes.
- If it holds logs of **several** models, they are never mixed: every analysis (all tabs, summary, table, export) covers exactly one model. By default it is the model with the newest log. Under the folder row of *Log data* a selector **Model** (Modell) appears – choosing another model analyses that one. The status line and the summary name the analysed model; the summary also lists the other models in the folder.
- The **battery settings** (cell chemistry, cell count, nominal capacity) are remembered per model and loaded when the model changes. Settings from before this feature stay with the first model analysed; another model starts with the defaults.
- A model **without stored battery settings** – a new model, or the very first start without any battery settings – shows a red hint: at the top of the summary, in the status line (“Battery settings missing for this model”) and below the battery fields in *Data & settings*. The analysis still runs with LiPo, automatic cell count and unknown capacity, but this assumption does not count as a setting, so state of charge, ageing and remaining capacity may be wrong. The hint disappears as soon as you choose the cell chemistry (even if it is LiPo) or enter a nominal capacity for that model; until then it comes back after a restart. Models that are already set up and the settings taken over from before this feature show no hint.
- The **period filter** applies within the selected model.
- The CSV export has a column *Model* (Modell).

## Flight database

The section **Database** (Datenbank) at the top of *Data & settings* manages the flight database. The area
*Logbook* and *Single flight* show its flights; statistics follow in a later version (they still work on the
log folder for now):

- The line below the file name shows how many logs the database holds, how many of them are flights, how many
  aircraft and how large the file is.
- **New …**, **Open …**, **Save as …** (writes a copy; the open database stays the same) and **Empty …** (after
  a question; the log files themselves stay untouched). Every change is stored at once.
- **Import files …** and **Import folder …** (with all subfolders, e.g. the transmitter's SD card). The import
  runs in the background with a progress bar; afterwards the **import report** lists every file as *new*,
  *duplicate* (same content already in the database, also under another name – skipped), *possible duplicate*
  (same aircraft and start time, other content – imported and marked) or *unreadable* (with the reason). New
  logs are marked as flight or not a flight.
- Every log is imported, also ground logs and short motor tests; they are only marked as not a flight.
- At program start the database used last is opened. On the very first start the database
  `Documents\EthosLogAnalyser\flugbuch.db` is created and the app offers to import the log folder used so far.

Details (detection, storage, schema): [Flight database](database.md).

## Language

The language is chosen under **Data & settings → Language** (Deutsch, English, Español). The window is rebuilt immediately in the new language; an existing analysis result, the selected flight, view and zoom are kept, so the logs do not have to be analysed again. The choice is saved together with the other settings and used at the next start. Without a saved choice, the app starts in the language of the operating system if it is supported, otherwise in English.

The language applies to the whole user interface, the text reports, the charts and the exports (file names, the text columns of the CSV table). The column names of the CSV export are internal identifiers and stay the same in every language.

## Pages

| Page | Contents |
|---|---|
| Statistics → Summary (Zusammenfassung) | overview, battery condition, ageing, timer recommendation, drive, radio, warnings |
| Statistics → Battery (Akku) | capacity, internal resistance, voltage at reference load, resting voltage, state of charge per flight |
| Statistics → Load & flight profile (Belastung & Flugprofil) | throttle histogram, C-rate, energy per flight phase, peak power, g-forces, flight time vs. timer |
| Statistics → Drive (Antrieb) | power vs. RPM curve, power demand at reference RPM, current sensor vs. ESC counter |
| Statistics → Radio & onboard power (Funk & Bordnetz) | RSSI, VFR, receiver battery, receiver current and its spikes, transmitter battery |
| Statistics → Table (Tabelle) | all metrics per flight |
| Single flight (Einzelflug) | time series in four views, detail report compared with the median of all flights of the aircraft |
| Logbook (Logbuch) | flights, flying days, total log duration, longest/shortest flight, total drawn charge; tables and bar charts per year and month; tree to group by time or aircraft; filter; sortable list of flights, with a switch to correct whether a log is a flight |

### Working with charts

The same functions are available in every chart (built in one place, `plots/hover.py`, `plots/common.py` and `gui/charts.py`, so new charts get them automatically):

- **Mouse-over**: a tooltip shows the data point nearest to the pointer – series name, x value (flight number and date, or the time) and y value with its unit. In stacked bars it shows the value of the segment.
- **Enlarge one chart**: a **double-click** into a chart, or **right-click → Enlarge this chart** (Dieses Diagramm vergrößern), opens just that chart in a window of its own that fills the screen – with its title, explanation line, axis labels, legend, helper lines (e.g. nominal capacity, 80 %), red circles, trend lines and secondary y axis. Example: in the *Load* tab, double-click *Peak C-rate per flight [C]*.
- **Enlarge the whole page**: the button *Enlarge whole page* (Ganze Seite vergrößern) in the toolbar below the charts, or the same entry in the right-click menu, opens all charts of the tab in one full-screen window. In that window a double-click on a chart (or right-click → *Enlarge this chart*) enlarges that chart on its own, as on the normal page.
- In both windows zoom, pan and save with the toolbar; the tooltip works there as well. **Esc** or *Close (Esc)* closes the window. While the toolbar's zoom or pan mode is active, double-click and right-click belong to that mode.
- **Time format**: all times are shown as min:s (`8:58`), from one hour on as h:min:s (`1:02:05`), rounded to whole seconds – in charts, tables, the summary and the timer.

### Single-flight view

The area *Single flight* shows the flights of the flight database:

- **Flight** (Flug): every log marked as a flight, oldest first, as *date time | aircraft | duration | drawn mAh*. The newest flight is selected at the start; *‹ back* / *next ›* step through the list. **‹ Logbook** goes back to the logbook.
- The charts and details compare the flight with **all flights of the same aircraft** in the database, with the battery settings of that aircraft (*Data & settings → Battery*, kept per model). The period filter does not apply here.
- When an aircraft is opened for the first time after the program start or an import, its flights are prepared from the database in the background (a few seconds for some 30 flights; the line above the chart shows the progress). The aircraft of the newest flight is prepared right after the start. After that a flight opens in well under a second.
- Only the **views** for which the log has data are offered. A flight whose log has no voltage and current of the flight battery (e.g. a glider) is listed, but shows a note instead of the charts – the views need these values so far.
- Without flights in the database the page explains how to import logs.
- In the logbook a **double-click** on a flight opens it here (if it is in the database).


- **Mouse wheel**: zoom around the cursor; **drag**: pan; *Whole flight* (Ganzer Flug) resets the zoom.
- **Double-click** (or right-click → *Enlarge this chart*) opens only the chart under the mouse full screen, with the time window shown in the tab, the min:s time axis, tooltip and vertical crosshair. *Whole flight* in that window shows the whole flight again. *Enlarge whole page* (button above the charts) opens all charts of the view; there, too, a double-click enlarges one chart, keeping the time window of the page window.
- Buttons for take-off/landing (60 s each), zoom and pan; all charts stay time-aligned.
- **Current spike** (Stromspitze): jumps to a detected receiver current spike.
- **Battery voltage per cell**: the battery voltage (measured and estimated resting voltage) is shown as mean cell voltage, total voltage / cell count, with the limit under load and the minimum resting voltage of the selected cell chemistry. The cell count is the one of the analysis (*Cell count* setting, or detected from the start voltage). If it is unknown, the chart shows the total voltage and says so. The receiver voltage is not converted.
- **Attitude view** (Fluglage): roll angle with the aileron stick, pitch angle with the elevator stick (angle on the left axis in °, stick on the right axis in %, both centred on zero), throttle with the rudder stick, g-load and altitude. Stick values are the Ethos channel values QR, HR, SR scaled to ±100 % (±1024 = full deflection); throttle is 0–100 %. Channels that are missing in the log or not moved are left out and listed in a note.
- The line above the charts shows all values at the time under the cursor; a vertical line marks that time in all charts.

### Logbook

The area *Logbook* (Logbuch), the start page, gives an overview of your flying. It reads the **flight database**
(it works without the folder analysis) and shows the flights of all aircraft in it. From top to bottom:

1. **Filter bar** (see below) and the switch **Show non-flights**.
2. **Scope line**: how many of the flights of the database are shown (“33 of 33 flights of the database”), with *Filter active* when a filter is set. If some flights have no date or no log duration, a line below says how many; they are left out of the totals.
3. **Totals**: number of flights with first and last date, flying days (different calendar days with at least one flight), total log duration, longest and shortest flight (with flight number and date; with several aircraft in view also the aircraft) and the total drawn charge in Ah and mAh. The totals follow the **filter**, not the row selected in the tree.
4. **Per year** and **per month** tables (flights, log duration, flying days, drawn mAh) and two bar charts: flights per month and log duration per month (only months with flights). The charts have the usual tooltip, double-click to enlarge and *Enlarge whole page*.
5. **Group by** (Gruppieren nach) and the **flights**, side by side:
   - The tree can be grouped **by time** (year → month → aircraft) or **by aircraft** (aircraft → year → month). Every row shows the number of flights and the flight time; the last row (*Total*) is the sum of everything shown. A click on a row restricts only the **flight list** to the flights of that row; the totals, tables and charts stay as they are. A click on the *Total* row shows all flights again.
   - The list has the columns flight number, aircraft, date, time, log duration, drawn mAh, *Flight* (Flug) and a warning column. A click on a column heading sorts by that column, a second click reverses the order (▲/▼); empty values stay at the end. A double-click on a row opens the flight in *Single flight*.

**Flight numbers** count per aircraft: *Flug 5* is the fifth flight of that aircraft, oldest first, and only logs counted as flights get a number. Two aircraft can therefore both have a flight 1.

**Log duration** is the time from *motor armed* to *motor disarmed* in the log (column `dauer_s`), not the pure airborne time. For an aircraft without a motor the duration detected for the flight is used. The **drawn charge** follows the same rule as *Total drawn* in the summary: flights whose battery values are invalid (measurement errors) are not counted; the line says how many were left out.

#### Filter

The filter bar offers **aircraft**, **year**, **month** and a date range **from / to** (dd.mm.yyyy; the end day is included; an entry that is not a date turns red and is ignored; an empty field means no limit). *Reset* removes all restrictions. The filter acts on the whole logbook: totals, tables, charts, tree and list. It is one shared setting (`gui/flight_filter.py`), so the statistics will show and change the same filter later. The *Period from/to* filter under *Data & settings* is a separate setting for the statistics and does not change the logbook.

#### Non-flights and corrections

Logs that were not detected as a flight (ground tests, short motor runs) are hidden. **Show non-flights** lists them too, in grey and without a flight number; they never count in the totals. The column **Flug** shows ☑ for a flight and ☐ for a log that is not one. A click on the symbol switches it: a ☐ becomes a flight, a ☑ no longer counts. The decision is stored in the database (`is_flight_manual`) and survives a new import; switching a log back to what the detection said removes the manual decision. Totals, tree, the single-flight list and the status line follow at once. A log that is not a flight cannot be opened as a single flight; the app says so.

A **⚠** in the last column marks a *possible duplicate*: another log of the same aircraft has the same start time but a different content. Hover over the symbol for the explanation. Both logs stay in the database; if one of them is really a copy, switch it to “not a flight”.

## Export

Under **Data & settings → Export**: the table as CSV (semicolon separator, decimal comma – opens directly in a German or Spanish Excel) or report, table and all charts into a folder. Durations stay in seconds in the CSV (columns `…_s`, e.g. `dauer_s`), each followed by the same value as min:s text (`…_mmss`, e.g. `dauer_mmss`). Report texts, chart labels and file names are in the selected language.
