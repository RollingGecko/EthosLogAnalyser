# Changelog

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
