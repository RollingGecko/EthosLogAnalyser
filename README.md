# EthosLogAnalyser

[![Tests](https://github.com/RollingGecko/EthosLogAnalyser/actions/workflows/tests.yml/badge.svg)](https://github.com/RollingGecko/EthosLogAnalyser/actions/workflows/tests.yml)

Desktop app (Python/Tkinter) for analysing **FrSky Ethos flight logs** (CSV), focusing on battery condition, drive and radio/onboard power. Built for an electric jet (Viper-Jet), but works with any Ethos log that contains flight battery voltage and current. The user interface is available in **German, English and Spanish**; the language can be switched in the app and is remembered.

All logs are imported into one **flight database** (a file; duplicates are recognised, the log files stay
untouched). From it the app shows a **logbook** (totals, tables per aircraft, year and month, flight list with notes and anomaly
hints), every **single flight** (opened from the logbook) and the **statistics** of one aircraft – with one filter (aircraft, year, month – each with
several values to tick – and a date range) shared by logbook and statistics.

## What it analyses

- **Battery:** internal resistance, voltage at reference load, estimated capacity, state of health (SoH), ageing trend and remaining life forecast, timer recommendation. State of charge at landing by coulomb counting, cross-checked against the resting voltage.
- **Load & flight profile:** C-rate, power, throttle histogram, flight phases, energy per phase, g-forces.
- **Drive:** power vs. RPM curve, current sensor plausibility against the ESC counter.
- **Radio & onboard power:** RSSI, VFR, receiver and transmitter battery, receiver current spikes classified by cause (switch, manoeuvre, take-off/landing or no apparent cause).
- **Single flight:** time series with zoom and crosshair, detail report compared with the median of all flights, note and anomalies per flight.
- **Flight recorder** (tab of the single flight): plays the flight back in real time with an artificial horizon, cockpit gauges, a radio with the stick positions (stick mode 1–4 selectable), an aircraft that turns with the attitude and moves its control surfaces with the sticks, and a timeline (play/stop, speed, drag to any moment). Its position shows as a vertical line in the time charts, and a click in a chart sets it.
- **Statistics** (still experimental): the pages above over the filtered flights of one aircraft.

## Download

The Windows EXE is attached to each release under [Releases](https://github.com/RollingGecko/EthosLogAnalyser/releases): download `EthosLogAnalyser-vX.Y.Z.exe` and start it – no Python needed. Windows SmartScreen may warn because the EXE is not signed (*More info → Run anyway*).

## Quick start (from source)

```bat
git clone https://github.com/RollingGecko/EthosLogAnalyser.git
cd EthosLogAnalyser
python -m venv .venv
.venv\Scripts\activate
pip install -e .
ethosloganalyser
```

Three real flight logs to try are in `examples/logs/` (*Data & settings → Database → Import folder …*). `scripts\build_exe.bat` builds the Windows EXE; GitHub also builds it on every push (Actions → Artifacts) and publishes it with every release.

## Documentation

- **User guide** for the Windows EXE, with screenshots: [English](docs/user-guide_en.pdf) ([Markdown](docs/user-guide_en.md)) · [Deutsch](docs/user-guide_de.pdf) ([Markdown](docs/user-guide_de.md))
- [Usage](docs/usage.md) – installation, import, logbook, single flight, statistics with the filter, settings, export
- [Methodology](docs/methodology.md) – how internal resistance, state of charge, capacity, timer and spikes are computed
- [Ethos log format](docs/ethos-log-format.md) – which columns the app expects
- [Flight database](docs/database.md) – import, duplicate and flight detection, storage and schema
- [Code map](docs/code-map.md) – every Python file: purpose, names other files use, dependencies, and where to look for typical changes
- [Translations](docs/translations.md) – how the user interface is translated and how to add or improve a language
- [Acceptance testing a pull request](docs/acceptance-testing.md) – test EXE of a pull request before merging
- [Releasing](docs/releasing.md) – how a new version is published

## Project layout

```
src/ethosloganalyser/
  config.py       cell chemistry, parameters, saved settings
  i18n.py         translation of all user-facing texts
  locales/        translation catalogs (en, es)
  io/             reading Ethos CSV logs
  db/             flight database: import, duplicates, flight detection, notes and anomalies
  analysis/       single flight, receiver current spikes, cross-flight analysis, anomaly rules, assessment
  report/         text reports
  plots/          charts (usable without the GUI)
  gui/            Tkinter user interface
tests/            pytest tests
docs/             documentation
examples/logs/    example logs
ethos/            Lua scripts for the transmitter
scripts/          Windows EXE build, release check
```

## Development

```bat
pip install -e ".[test]"
python -m pytest
```

Tests run automatically on every push and pull request under Linux and Windows. Documentation, code comments, docstrings, test names and commit messages are in English. User-facing texts are written in German in the code and translated via `locales/` (see [Translations](docs/translations.md)).

## License

MIT – see [LICENSE](LICENSE).
