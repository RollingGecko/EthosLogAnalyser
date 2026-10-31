# Changelog

Each entry is one short line in plain words: what you can now do or what looks different. Details are in the pull
requests and in `docs/`.

## Unreleased

## 1.0.0-beta.2

Second beta of 1.0.0. The program itself is unchanged; the release package and the notes are new.

### New

- **User guide** for the Windows EXE in English and German (PDF), with screenshots.
- **One download**: the release contains a ZIP with the EXE and both user guides; the EXE and the guides are also available on their own.

### Changed

- **Shorter release notes** that list only what changed for users.

## 1.0.0-beta.1

First beta of 1.0.0, for broader testing (marked *Pre-release*). Changes compared with 0.3.0:

### New

- **Flight recorder**: replays a flight in real time with an artificial horizon, cockpit gauges (altitude, vertical speed, drive, battery), the transmitter sticks and a small aircraft that follows attitude and sticks. Timeline, play/stop and speeds from 0.25× to 16×.
- **Stick mode 1–4** for the recorder (*Data & settings → Flight recorder*).
- **Position line in the charts**: the recorder position shows as a vertical line in every time chart; a click in a chart sets it.
- **Flight database**: logs are imported once into one database file (files or whole folders, duplicates are recognised). Your log files are never changed.
- **Logbook** as start page: totals, tables per aircraft, year and month, and a sortable flight list. Logs that are not flights can be switched on or off by a click.
- **Filter with several values** for aircraft, year and month, plus a date range, shared by logbook and statistics.
- **Notes and anomalies per flight**: a free-text note and automatic hints (e.g. unusually short flight, high internal resistance, receiver voltage dip) that you can acknowledge or extend with your own entries.
- **Several aircraft**: the model comes from the file name; battery settings are kept per aircraft, with a red hint until they are entered.
- **Better charts**: tooltip on every chart, enlarge a single chart by double-click, voltage per cell, an attitude view with the sticks, motor curve against RPM, times as min:s.

### Changed

- **Statistics** now come from the database, are ready right after the start and are marked *experimental*. They cover one aircraft at a time.
- A single flight opens by double-click in the logbook (no separate tab any more).
- **More reliable battery ageing**: one robust trend per value, no trend or forecast unless it is clear, measurement errors are recognised and left out, capacity is corrected for the depth of discharge.
- Tables and charts no longer cut off text at Windows display scaling of 125 % or 150 %.
- The window title and *About* show the version; test builds are clearly marked.

### Removed

- The folder analysis and the period filter (the database import and the filter replace them), the bar charts and *Group by* tree of the logbook.

### For developers

- Code map, working rules (`CLAUDE.md`) and a test EXE for every pull request.

## 0.3.0

- The user interface is available in German, English and Spanish. The language is chosen under *Data & settings → Language*, switched without restarting and without analysing the logs again, and remembered for the next start. Without a saved choice the app starts in the language of the operating system (English if it is not supported).
- Reports, charts, warnings, reasons for skipped files and exports (file names, text columns of the CSV table) follow the selected language. Dates are shown as dd/mm/yyyy in English and Spanish.
- Analysis results are language-neutral: spike causes, flags, warnings and the source of the end voltage are stored as codes or lazily translated messages and only turned into text when they are shown.
- Tests check that every user-facing text is translated in every catalog, that no translation is unused and that the placeholders match.
- Single flight tab: the view buttons have a row of their own, so the toolbar also fits with longer labels.
- Fixed: in charts with several series (e.g. internal resistance, receiver current) the explanation line overlapped the chart title.
- Releases: pushing a version tag `vX.Y.Z` runs the tests, builds the Windows EXE and publishes it as `EthosLogAnalyser-vX.Y.Z.exe` on GitHub Releases with this changelog section as release notes. The release is refused if tag, version and changelog do not match. See `docs/releasing.md`.

## 0.2.0

- Split the code into the Python package `ethosloganalyser`: `io` (reading), `analysis` (analysis), `report` (texts), `plots` (charts), `gui` (user interface). The analysis is unchanged – verified on 73 log files (35 flights) with identical tables, texts and charts.
- Installation via `pyproject.toml`; start with `ethosloganalyser` or `python -m ethosloganalyser`.
- Automated tests (pytest) for reading, single-flight analysis, receiver current spikes, cross-flight analysis, reports, charts and the GUI; they run on every push on GitHub under Linux and Windows.
- GitHub builds the Windows EXE on every push (`scripts/build_exe.bat`).
- Documentation in `docs/`: usage, methodology, Ethos log format. Documentation, code comments and docstrings are in English; the user interface stays German.
- Fixed: decimal commas in log values were no longer converted with pandas 3.
- Fixed: logs without a date column that run past midnight crashed with pandas 3.

## 0.1.0

- First version (`EthosLogAnalyser.py`).
