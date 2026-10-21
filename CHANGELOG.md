# Changelog

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
