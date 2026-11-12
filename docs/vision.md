# Vision

## Purpose
EthosLogAnalyser turns the flight logs of FrSky Ethos transmitters (CSV) into a flight logbook and into clear statements
about battery condition, drive and radio/onboard power. It is a hobby project of the owner (MIT licence), built first for
an electric jet (Viper-Jet) but meant for all of the owner's aircraft.

## Audience
The owner and other Ethos users. The app is presented in the RC-Network forum and in the Facebook group "Official FrSky
Ethos Group" (English); feedback comes through the forum thread and GitHub issues. UI languages: German, English, Spanish.

## Scope today (v1.0.0)
- **Flight database**: one file (SQLite). New / open / save as / empty; the last loaded database opens at start. Import of
  files and folders with duplicate elimination (SHA-256; same aircraft and start time with different content is reported as
  "possible duplicate"). Raw logs are kept in the database (LZMA), the original files are never changed.
- **One flight = one log file.** Not every aircraft has motor or flight battery data; the sensors present are detected.
  Flight detection uses the best available sensor; logs that are not flights are kept and marked.
- **Logbook** (start page): totals, tables per aircraft / year / month, sortable flight list, note and anomaly hints per
  flight; choosing a flight opens the single-flight view.
- **Anomalies** are relative to the other flights of the same aircraft (median comparison from five flights on) and to the
  flight itself; the only fixed limit is the optional receiver minimum voltage per aircraft.
- **Single flight**: tab *Charts* and tab *Flight recorder* (separate).
- **Statistics** (total / per aircraft / year / month) with a shared filter (aircraft, year, month, date range). The pages
  are the former analysis pages (summary, battery, load & flight profile, drive, radio & onboard power, table). Marked
  *experimental*. Battery selection is deliberately not part of it yet.

## Architecture (see `code-map.md`, `database.md`)
- `io/` parses Ethos CSV; `db/` imports, detects flights, stores data and prepared evaluation values; `analysis/` holds the
  pure evaluation logic; `recorder/` the pure logic of the flight recorder; `plots/` matplotlib figures; `gui/` Tkinter only.
- Aircraft-specific values (battery settings) are per aircraft; they currently live in the settings file of the computer
  (move into the database: board item TW-050).

## Principles
- **Performance**: no long waits. A single flight opens in under a second, filtering is below half a second, redraw per
  recorder row takes milliseconds. Prepared values are stored in the database so the statistics start quickly.
- **Small database file**: time series are stored compactly (scaled integers, delta coding, zlib); measure the size when
  storage changes.
- **Anomalies relative per aircraft**, no fixed global limits.
- **Several aircraft**: the model comes from the file name; never assume the number of servos, control surfaces, motors or
  battery sensors. Battery settings are per model.
- **Only what the log contains**: e.g. only the total receiver current exists, not one per servo. A diagnosis is never
  presented as fact, always as hint or estimate.
- Never invent Ethos API details; mark uncertain ones and let the owner test them.
- Raw logs stay out of project documents; example logs are in `examples/logs_2026` (the old logs of 2022-2025 are not in the project).
- Language: UI texts German in code with en/es translations; everything else in the repo English.
