# Changelog

## Unreleased

- Measurement errors are recognised and kept out of the analysis: a stuck current sensor (current at its maximum for the whole flight), voltage dropouts, an impossible resting voltage after landing (below the voltage under load at the end of the flight, e.g. battery unplugged during the measurement), VFR outside 0–100 % and implausible internal resistance. They are listed under *Data quality* instead of being reported as deep discharge or voltage collapse, and no longer distort trends and start values.
- State of health, ageing trend and remaining-life forecast now come from one robust model per metric (Huber-weighted straight line over the flight number), so they no longer contradict each other and single start flights or outliers do not move them. The trend is shown with its 90 % range; without a significant ageing trend, with too few or too scattered values, or with an improving value (e.g. falling internal resistance) no forecast is made and the reason is given.
- The capacity estimate is corrected for its dependency on the depth of discharge and referred to the median depth of the analysed flights (new column *Capacity normalised*). The size of this dependency is estimated only from flights of the same day, so it cannot absorb the ageing trend when later flights go deeper.
- No ageing trend is shown unless it is significant and plausible: otherwise start and current value are the mean level of the period (dashed horizontal line). A rising capacity, or a capacity trend that contradicts the voltage at reference load, is reported as uncertain without forecast.
- Short flights (below 40 % depth of discharge) no longer enter the capacity and internal-resistance trends.
- The robust fit no longer drops values; low values at the end of the series that follow the trend are kept.
- SoH refers to the nominal capacity if one is entered (otherwise to the start value); the change against the start value of the selected period is shown as well.
- Hint when the capacity values form two separate groups (several batteries in the period).
- New period filter (*Data & settings → Period from/to*) to analyse e.g. only the flights of one battery.
- The battery charts draw the robust trend line (dashed mean level if the trend is not significant or uncertain) and the 80 % line relative to the nominal capacity.
- The window title and the new *About* box (*Data & settings*) show the version. Test builds made by GitHub Actions for a pull request or branch show a build tag such as `0.3.0+pr12.abc1234` and *TEST VERSION*; released versions do not.
- Every pull request gets a test EXE for acceptance testing, linked in a pull-request comment and in the run summary (see docs/acceptance-testing.md). Test builds never create a tag or a release.
- docs/releasing.md: the tag is no longer created via *Draft a new release* (that publishes a conflicting release); GitHub Desktop is described as the way without command line.

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
