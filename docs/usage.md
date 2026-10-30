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

The window has three areas, shown as tabs at the top:

| Area | Contents |
|---|---|
| Logbook (Logbuch) | start page: totals, tables per aircraft, year and month, list of flights (see *Logbook* below); a double-click on a flight opens the **single flight** here (see *Single-flight view*) |
| Statistics (Statistik) | the filter and pages over the filtered flights of one aircraft: Summary, Battery, Load & flight profile, Drive, Radio & onboard power, Table (smaller tabs inside the area); see *Statistics* below |
| Data & settings (Daten & Einstellungen) | flight database, battery settings per aircraft, analysis settings, anomaly rules, language, export |

All areas show the flights of the flight database; there is no separate analysis of a log folder any more.

The **status line** at the top shows the state of the flight database (flights, aircraft, first and last flight,
and how many logs are not counted as flights). In *Statistics* it shows the flights of the filter instead:
“n of N flights of the database · aircraft · first – last flight · Filter: …”, and whether the battery settings
of the aircraft are missing.

## Workflow

1. Area **Data & settings** (Daten & Einstellungen): import the logs into the flight database (*Import folder …*, subfolders are included). Logbook, single flight and statistics follow at once.
2. **Battery** (Akku), per aircraft:
   - **Aircraft** (Flugzeug) – the aircraft of the database whose battery settings the fields show; by default the aircraft of the newest flight.
   - **Cell chemistry** – LiPo, LiHV or Li-Ion. Selects the resting voltage → state of charge curve.
   - **Cell count** – 0 = detect automatically from the highest start voltage.
   - **Nominal capacity** – 0 = unknown; the capacity is then estimated from the flights. With a nominal capacity entered, state of charge, timer and the cell chemistry check become considerably more reliable.
3. **Analysis** (Auswertung):
   - **Min. flight duration** – shorter logs (ground tests, aborted flights) are not counted as flights at the import; default 120 s.
   - **Motor running from** – current above which the flight counts; default 1 A.
   - **Reserve at landing** – remaining charge the timer recommendation aims for; default 20 %.
   - **Voltage / current column** – only needed if automatic detection picks the wrong column; part of the column name is enough.
Settings are saved to `%USERPROFILE%\.akku_analyse.json`. Settings from older versions (log folder, period
from/to, model selector) are ignored; the battery settings per model are kept.

### Several aircraft

The aircraft (model) is taken from the log file name: the part before the time stamp, e.g. `Viper-Jet` from `Viper-Jet-2026-04-19-13-25-36.csv` (hyphens and digits in the name are fine, a leading `-` is ignored; files without a model part count as “(unknown)”).

- Aircraft are never mixed in one analysis: the statistics always cover exactly one aircraft (see *Statistics*).
- The **battery settings** (cell chemistry, cell count, nominal capacity) are remembered per aircraft: choose the aircraft in the battery section, the fields show its settings. Settings from before aircraft existed stay with the first aircraft; another aircraft starts with the defaults.
- An aircraft **without stored battery settings** shows a red hint: at the top of the statistics summary, in the status line of the statistics (“Battery settings missing for this model”) and below the battery fields in *Data & settings*. The statistics still use LiPo, automatic cell count and unknown capacity, but this assumption does not count as a setting, so state of charge, ageing and remaining capacity may be wrong. The hint disappears as soon as you choose the cell chemistry (even if it is LiPo) or enter a nominal capacity for that aircraft; until then it comes back after a restart.
- The CSV export has a column *Model* (Modell).

## Flight database

The section **Database** (Datenbank) at the top of *Data & settings* manages the flight database. Logbook,
single flight and statistics show its flights:

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

The language is chosen under **Data & settings → Language** (Deutsch, English, Español). The window is rebuilt immediately in the new language; the filter, the selected flight, view and zoom are kept. The choice is saved together with the other settings and used at the next start. Without a saved choice, the app starts in the language of the operating system if it is supported, otherwise in English.

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
| Logbook → single flight (Einzelflug) | time series in four views, detail report compared with the median of all flights of the aircraft; opened by a double-click in the logbook |
| Logbook (Logbuch) | flights, flying days, total log duration, longest/shortest flight, total drawn charge; tables per aircraft, year and month; filter; sortable list of all flights, with a switch to correct whether a log is a flight |

### Working with charts

The same functions are available in every chart (built in one place, `plots/hover.py`, `plots/common.py` and `gui/charts.py`, so new charts get them automatically):

- **Mouse-over**: a tooltip shows the data point nearest to the pointer – series name, x value (flight number and date, or the time) and y value with its unit. In stacked bars it shows the value of the segment.
- **Enlarge one chart**: a **double-click** into a chart, or **right-click → Enlarge this chart** (Dieses Diagramm vergrößern), opens just that chart in a window of its own that fills the screen – with its title, explanation line, axis labels, legend, helper lines (e.g. nominal capacity, 80 %), red circles, trend lines and secondary y axis. Example: in the *Load* tab, double-click *Peak C-rate per flight [C]*.
- **Enlarge the whole page**: the button *Enlarge whole page* (Ganze Seite vergrößern) in the toolbar below the charts, or the same entry in the right-click menu, opens all charts of the tab in one full-screen window. In that window a double-click on a chart (or right-click → *Enlarge this chart*) enlarges that chart on its own, as on the normal page.
- In both windows zoom, pan and save with the toolbar; the tooltip works there as well. **Esc** or *Close (Esc)* closes the window. While the toolbar's zoom or pan mode is active, double-click and right-click belong to that mode.
- **Time format**: all times are shown as min:s (`8:58`), from one hour on as h:min:s (`1:02:05`), rounded to whole seconds – in charts, tables, the summary and the timer.

### Single-flight view

The single flight has no tab of its own: it is opened from the logbook (a **double-click** on a row of the flight list) and replaces the logbook page; the *Logbook* tab stays highlighted. **‹ Logbook** (top left) returns to the logbook with its filter, sorting and list as they were. A log that is not counted as a flight cannot be opened (switch it to ☑ in the column *Flug* first). If you change the language or the database while a flight is open, it stays open. The page shows the flights of the flight database:

- **Flight** (Flug): every log marked as a flight, oldest first, as *date time | aircraft | duration | drawn mAh*. The newest flight is selected at the start; *‹ back* / *next ›* step through the list. **‹ Logbook** goes back to the logbook.
- The charts and details compare the flight with **all flights of the same aircraft** in the database, with the battery settings of that aircraft (*Data & settings → Battery*, kept per model). The filter of logbook and statistics does not apply here.
- When an aircraft is opened for the first time after the program start or an import, its flights are read from the database in the background (well under a second for some 150 flights, about 1.5 s for 1000). The aircraft of the newest flight is read right after the start. A flight then opens in well under a second.
- After updating from a version before the prepared values (flight database schema 2), the app works them out once when the database is opened: *Data & settings → Database* shows the progress (“Preparing the values for the statistics”), and the window can be used meanwhile. Until it is finished, single flight and statistics analyse the flights of an aircraft as before (a few seconds for some 30 flights; the line above the chart shows the progress) – the results are the same.
- Only the **views** for which the log has data are offered. A flight whose log has no voltage and current of the flight battery (e.g. a glider) is listed, but shows a note instead of the charts – the views need these values so far.
- Without flights in the database the page explains how to import logs.
- In the logbook a **double-click** on a flight opens it here (if it is in the database).
- Below the selection bar the page has two tabs: **Charts** (Diagramme) with the views described here, the buttons *Save image*, *Enlarge whole page* and *Hide details*, and below the charts the details, the note and the anomalies; and **Flight recorder** (Flugrekorder), see below. The selection bar (‹ Logbook, flight, ‹ back, next ›) belongs to both tabs.

#### Flight recorder

The tab *Flight recorder* plays the selected flight back in real time from the time series stored in the flight database. It does not need the prepared values of the aircraft, so it is there at once – also while “Flights are being prepared …” and for flights without battery data (e.g. a glider).

- **Artificial horizon** in the middle: blue sky, brown ground, a horizon line that turns with the bank and moves with the pitch, a pitch ladder every 10°, the bank scale at the top with a pointer that turns with the horizon, the fixed aircraft symbol and the digits *Bank 23° · Pitch −4°* (bank positive = right wing down, pitch positive = nose up). Inverted flight and a roll across ±180° are shown as they are. The attitude comes only from the attitude sensor (columns `R.angle` and `P.angle`), never from the sticks; if only one of them is in the log, the other counts as 0; without both, the horizon is hidden and the gauges take its place. If the newest value is older than 2 s, the horizon turns grey and says *no attitude data*.
- **Cockpit gauges** left and right of the horizon, in this order: **Altitude** (top left), **Vertical speed** (top right), **Drive** (bottom left) and **Battery** (bottom right). Dark dials with white scales and pointers in the colour of the aircraft symbol, like the horizon. Each gauge shows the first column of its sensor (as the analysis does; for the RPM “ESC RPM” is preferred).
  - *Altitude*: round dial relative to the start (0 m = median of the first values, as in the charts), number *132 m*.
  - *Vertical speed*: round dial with 0 at 9 o'clock, climbing turns the pointer up, sinking down; number with sign *+2.4 m/s*. Only from a vario sensor (`VSpeed`); it is never worked out from the altitude.
  - *Drive*: RPM as a round dial (labels in thousands, *×1000*) with the number *84 000 rpm*, and the throttle as a bar 0–100 % below it (*Throttle 45 %*, the same conversion as the analysis: (value + 1024) / 2048).
  - *Battery*: motor current as a round dial with the number *63 A*, and the battery voltage as a bar between the lowest and highest voltage of the flight with the number *48.6 V*; with the voltage per cell (*· 3.74 V/cell*) if the battery settings of the aircraft have a cell count (*Data & settings*). Readings of 0 V (sensor not ready) and single short drops do not stretch the bar.
  - **Scales per flight**: the end of each scale is a “nice” value just above the largest value of the flight (e.g. 250 m, 120 A, 120 000 rpm; vertical speed ±5, ±10 or ±20 m/s), so small and large models use the whole dial. A pointer stops at the end of its scale.
  - **Missing sensors**: a gauge without any of its sensors is not shown and the others move up (e.g. a glider shows only altitude and vertical speed); if one of two sensors is missing (e.g. no current sensor), the gauge shows only the other one.
  - **Gaps**: if the newest value of a sensor is older than 2 s, its gauge shows *—* and a grey pointer; the gauge stays in its place.
- **Provisional sign convention** (to be checked with a known manoeuvre, ticket TW-053): in the Viper-Jet logs a positive `P.angle` goes with losing height, so it is shown as nose down; a positive `R.angle` is shown as right wing down.
- **No interpolation**: at every moment the last log row holds (about one row every 0.27 s). The picture therefore changes about 3.7 times per second at 1×; for details use 0.25× or step row by row.
- **Timeline** at the bottom, over the full width: a click jumps, dragging moves the position (also while the flight plays; it plays on when you let go). The green band below the track marks where telemetry is there, so gaps within the flight show. The time *3:12 / 8:58* is log time.
- **Buttons**: *▶ Play* / *■ Stop*, ⏮ first row, ◀ / ▶ one log row back / forward, ⏭ end; **Speed** in fixed steps 0.25×, 0.5×, 1×, 2×, 4×, 8×, 16× (default 1×; at high speeds rows are skipped).
- **Keys** while the tab is shown (click into the recorder first): space play/stop, ←/→ one row, Shift+←/→ 10 s, Home/End.
- **End of the playback**: the recorder ends with the flight, i.e. with the last log row that still has telemetry (any sensor of the aircraft; sticks, switches and the transmitter battery do not count). Some logs run on for minutes after the landing without telemetry; that part is not shown. Play at the end starts again from the beginning.
- The playback stops when you choose another flight (it starts at 0), the tab *Charts*, *‹ Logbook* or another area. A language switch keeps the tab, the position and the speed.
- The layout follows the window size: in a smaller window the horizon moves to the left and the gauges form a 2 × 2 grid next to it; in a very small one the horizon remains with a column of numbers (altitude, vertical speed, RPM, throttle, voltage, current) instead of the gauges. Sizes follow the font, and the numbers get smaller rather than being cut off, so they fit at a Windows display scaling of 125 % and 150 %. Further instruments (transmitter sticks, aircraft) follow in later versions.
- If a log has no data for any instrument, a note says so; the timeline works anyway.


- **Mouse wheel**: zoom around the cursor; **drag**: pan; *Whole flight* (Ganzer Flug) resets the zoom.
- **Double-click** (or right-click → *Enlarge this chart*) opens only the chart under the mouse full screen, with the time window shown in the tab, the min:s time axis, tooltip and vertical crosshair. *Whole flight* in that window shows the whole flight again. *Enlarge whole page* (button above the charts) opens all charts of the view; there, too, a double-click enlarges one chart, keeping the time window of the page window.
- Buttons for take-off/landing (60 s each), zoom and pan; all charts stay time-aligned.
- **Current spike** (Stromspitze): jumps to a detected receiver current spike.
- **Battery voltage per cell**: the battery voltage (measured and estimated resting voltage) is shown as mean cell voltage, total voltage / cell count, with the limit under load and the minimum resting voltage of the selected cell chemistry. The cell count is the one of the analysis (*Cell count* setting, or detected from the start voltage). If it is unknown, the chart shows the total voltage and says so. The receiver voltage is not converted.
- **Attitude view** (Fluglage): roll angle with the aileron stick, pitch angle with the elevator stick (angle on the left axis in °, stick on the right axis in %, both centred on zero), throttle with the rudder stick, g-load and altitude. Stick values are the Ethos channel values QR, HR, SR scaled to ±100 % (±1024 = full deflection); throttle is 0–100 %. Channels that are missing in the log or not moved are left out and listed in a note.
- The line above the charts shows all values at the time under the cursor; a vertical line marks that time in all charts.

### Statistics

The area *Statistics* (Statistik) shows the flights of the flight database that pass the **filter**, without any
button to start an analysis:

- The **filter bar** at the top is the same filter as in the logbook (aircraft, year, month, from / to): a change
  here is seen in the logbook at once and the other way round. Logs that are not flights never count.
- **One aircraft at a time**: if the filtered flights belong to several aircraft – because several are ticked in
  the filter or because it is set to *all* – the statistics say “Please choose an aircraft in the filter” instead of
  mixing them (the logbook does show several aircraft). With only one aircraft in the filtered flights nothing
  needs to be chosen. With nothing ticked there are no flights and the statistics say that no flight matches.
- The **Summary** starts with the notice that this area is still experimental (also in the exported report),
  followed by the filter (if set) and the battery hint (if the battery settings of the aircraft are missing).
- Flights are numbered within the filter (flight 1 is the oldest flight of the filter), as the cross-flight
  values (cell count, trends, timer) are calculated from exactly these flights.
- The flights of an aircraft are read once in the background from the values stored with every flight (about
  0.05 s for 33 flights, 1.5 s for 1000; the statistics are ready about 1.7 s after the program start with
  `examples/logs_2026`); until then every page says so. Afterwards a filter change takes a fraction of a second; only
  the page that is shown is drawn again, the others when you open them.
- Flights without battery voltage and current (e.g. a glider) get a hint instead of the pages.
- **Export** (*Data & settings → Export*): the table as CSV and *Report + all charts* use the statistics of the
  current filter.

### Logbook

The area *Logbook* (Logbuch), the start page, gives an overview of your flying. It reads the **flight database**
and shows the flights of all aircraft in it. From top to bottom:

1. **Filter bar** (see below) and the switches **only with note or anomaly** and **Show non-flights**.
2. **Scope line**: how many of the flights of the database are shown (“33 of 33 flights of the database”), with *Filter active* when a filter is set. If some flights have no date or no log duration, a line below says how many; they are left out of the totals.
3. **Totals**: number of flights with first and last date, flying days (different calendar days with at least one flight), total log duration, longest and shortest flight (with flight number and date; with several aircraft in view also the aircraft) and the total drawn charge in Ah and mAh. The totals follow the **filter**.
4. **Three small tables side by side**, all following the filter and calculated the same way as the totals:
   - **Per aircraft** (Je Flugzeug): aircraft, flights, flying days, log duration and drawn mAh, with a **sum row** (*Summe*) at the end that repeats the totals above. Flying days are counted per aircraft; in the sum row they are the different calendar days of all aircraft, so the days of two aircraft that flew on the same day count once.
   - **Per year** and **per month**: flights, log duration, flying days and drawn mAh.
5. The **flights**: the list of all flights that pass the filter, below the tables, with all the space that is left. It has the columns flight number, aircraft, date, time, log duration, drawn mAh, *Flight* (Flug) and a narrow hint column (see *Notes and anomalies*). A click on a column heading sorts by that column, a second click reverses the order (▲/▼); empty values stay at the end. A double-click on a row opens the flight in *Single flight*.

Column widths and the row height of the tables follow the font, so headings and values are shown completely at any Windows display scaling (100 %, 125 %, 150 % …) – in the logbook, in the table of the statistics, in the selection of the single flight and in the import report. At a high scaling on a small screen the three tables need the width of the window; make the window wider if the right-hand table is cut off at the window edge.

**Flight numbers** count per aircraft: *Flug 5* is the fifth flight of that aircraft, oldest first, and only logs counted as flights get a number. Two aircraft can therefore both have a flight 1.

**Log duration** is the time from *motor armed* to *motor disarmed* in the log (column `dauer_s`), not the pure airborne time. For an aircraft without a motor the duration detected for the flight is used. The **drawn charge** follows the same rule as *Total drawn* in the summary: flights whose battery values are invalid (measurement errors) are not counted; the line says how many were left out.

#### Filter

The filter bar offers **aircraft**, **year**, **month** and a date range **from / to** (dd.mm.yyyy; the end day is included; an entry that is not a date turns red and is ignored; an empty field means no limit). *Reset* removes all restrictions. The filter acts on the whole logbook: totals, tables and list. It is one shared setting (`gui/flight_filter.py`): the statistics show and change the same filter.

**Several values per field.** Aircraft, year and month are lists of check buttons: a click on the field opens the list, a click on a value ticks or unticks it, and the list stays open until you click outside of it or press Esc (Tab moves between the values, the space bar ticks one). **Select all** and **Deselect all** at the top tick everything or nothing. The field shows what is ticked: *all*, e.g. *2024, 2025*, or – if the names do not fit – *3 of 5*; with nothing ticked it says *none*.

- Within one field the values are alternatives: years 2024 and 2025 show the flights of 2024 *or* 2025. Between the fields all conditions must hold: aircraft *and* year *and* month *and* from / to.
- Year and month are combined separately: years 2024 and 2025 with months 06 and 07 show June and July of **both** years (not single pairs such as “06/2024 and 07/2025”).
- With everything ticked the filter does not restrict anything (*all*); a new aircraft or year that appears after an import is then included automatically. If you have narrowed the selection, new values stay unticked until you tick them. When an aircraft or year disappears from the database it is removed from the selection.
- With nothing ticked no flight is shown (“0 of N flights of the database”, no error); *Select all* brings them back.
- The scope line, the status line and the statistics summary name the selection (*Filter: 2024, 2025, months 06, 07*; for more than two values only the number: *3 years*).

#### Non-flights and corrections

Logs that were not detected as a flight (ground tests, short motor runs) are hidden. **Show non-flights** lists them too, in grey and without a flight number; they never count in the totals. The column **Flug** shows ☑ for a flight and ☐ for a log that is not one. A click on the symbol switches it: a ☐ becomes a flight, a ☑ no longer counts. The decision is stored in the database (`is_flight_manual`) and survives a new import; switching a log back to what the detection said removes the manual decision. Totals, tables, the single-flight list and the status line follow at once. A log that is not a flight cannot be opened as a single flight; the app says so.

A **⚠** in the last column marks a *possible duplicate*: another log of the same aircraft has the same start time but a different content. Hover over the symbol for the explanation. Both logs stay in the database; if one of them is really a copy, switch it to “not a flight”.

### Notes and anomalies

Every flight can have a **note** (free text) and **anomalies**: hints found automatically by rules and entries of
your own, each with a level *Info*, *Warning* or *Critical*. They are hints, never a diagnosis.

- **Single flight**: below the charts, next to the details, the section *Note and anomalies*. Type the note and
  click *Save note* – it is also saved when you choose another flight or leave the page. The list shows the
  anomalies of the flight, most severe first, with level, status (*open* / *acknowledged*) and origin (*automatic* /
  *own entry*); the full text of the selected one is shown below the list. *Acknowledge / reopen* marks the
  selected anomaly as dealt with (or open again). *Own entry …* adds an entry with your text and level; *Delete
  entry* deletes the selected own entry (automatic ones can only be acknowledged). *Hide details* hides this
  section together with the details.
- **Logbook**: the hint column of the flight list shows ✎ for a note and the highest level of the anomalies that
  are still open (ℹ info, ⚠ warning, ‼ critical), followed by ⚠ for a possible duplicate. Hover over the column to
  read the texts below the list. **only with note or anomaly** lists only flights that have a note or an open
  anomaly. Sorting by the hint column puts the most severe open anomalies first (click twice).
- **Data & settings → Anomalies**: every rule can be switched off and its value changed; the receiver minimum
  voltage is set per aircraft (choose the aircraft, enter the voltage, empty = off). Changes take effect a moment
  later; all flights are judged again in the background (under a second). The line below says how many automatic
  hints were found.

The rules and their standard values are described in docs/methodology.md (*Anomalies per flight*). The limits of
the cell chemistry are only checked once the battery settings of the aircraft have been chosen. An acknowledgement
stays after every recalculation; only if the value behind it changes clearly (more than 20 %) is the anomaly open
again. After an import or after switching a log between flight and no flight, the anomalies are updated
automatically.

## Export

Under **Data & settings → Export**: the table of the statistics (the filtered flights of one aircraft) as CSV (semicolon separator, decimal comma – opens directly in a German or Spanish Excel) or report, table and all charts into a folder. Durations stay in seconds in the CSV (columns `…_s`, e.g. `dauer_s`), each followed by the same value as min:s text (`…_mmss`, e.g. `dauer_mmss`). Report texts, chart labels and file names are in the selected language.
