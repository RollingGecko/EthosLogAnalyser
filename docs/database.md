# Flight database

With the rebuild of the app (v2), all imported logs are kept in one flight database. This page describes the file, the
import, the duplicate and flight detection and the schema. The code is in `src/ethosloganalyser/db/`.

The database is filled and managed on the page *Data & settings → Database*. The area *Single flight* reads its
flights from it (`gui/database_flights.py`: the stored time series of all flights of an aircraft are analysed
again with `analysis/flight.py` and combined with `analysis.fleet.analyse_flights`, which gives exactly the
result of the folder analysis). Logbook and statistics move to the database in the next steps.

## The file

- One SQLite file, by default `Documents\EthosLogAnalyser\flugbuch.db` (the real Documents folder, also when
  Windows has moved it, e.g. into OneDrive).
- At program start the database opened last is opened again (setting `database`). If it is missing, the
  default database is used and the user is told. On the very first start the default database is created and,
  if a log folder was used before, the app offers to import it.
- **New** creates an empty database (an existing file at that place is replaced after the usual question of
  the file dialog). **Open** opens another one. **Save as** writes a copy; the open database stays the same –
  SQLite stores every change at once, so there is nothing else to save. **Empty** deletes all logs and flights
  (after a question) and shrinks the file (`VACUUM`); the log files on disk are not touched.
- A file is recognised as a flight database by `PRAGMA application_id` (`0x454C4131`, "ELA1"); the schema version
  is `PRAGMA user_version`. Older versions are upgraded on opening (`schema.MIGRATIONS`), newer ones are refused.

## Import

- **Import files** takes single CSV files, **Import folder** a folder with all its subfolders (e.g. the SD card of
  the transmitter). The import runs in the background with a progress bar; the window stays usable.
- The log files are only read. Their complete content is stored in the database (lzma), so a later analysis
  change can be calculated again without the files.
- Every file ends up in exactly one group of the **import report**:
  - **new** – imported (the report says whether it is a flight),
  - **duplicate** – the same content (SHA-256) is already in the database, whatever the file name or folder;
    skipped,
  - **possible duplicate** – other content, but the same aircraft and start time as a stored log; imported and
    marked (`flight.possible_duplicate`),
  - **unreadable** – not a CSV log or no time column; not imported, with the reason.
- The aircraft is the model name from the file name (the part before the time stamp, as before). The start time
  comes from the time stamp in the file name.

## One flight per log, flight detection

Every log is imported; one log is one flight or, if it is not a flight, one log marked as such
(`flight.is_flight = 0`, a later manual decision goes to `is_flight_manual`). The decision uses the best sensor
the log has (`flight_detection.py`):

1. **Motor current** – when the current sensor shows the motor running at all: the rule of the analysis so far
   (motor running for at least *Min. flight duration*). The duration is the motor-running time as before.
2. **Altitude** – more than 15 m above the start level for at least the minimum flight duration. Ground logs of
   the Viper reach up to about 10 m of sensor drift.
3. **Vertical speed** (vario, when there is no altitude) – climbing or sinking faster than 1.5 m/s over at least
   the minimum flight duration.
4. **Radio link** – receiver signal (RSSI) present for at least the minimum flight duration. A log without any
   receiver telemetry (receiver off; only transmitter values) is not a flight.

Barometric values are smoothed with a rolling median of 5 samples against single spikes. With
`examples/logs_2026` the import finds the same 33 flights as the folder analysis.

## What is stored per flight

- **Metrics**: the per-flight result of the existing analysis (`analysis/flight.py`, the columns of the flight
  table that do not depend on other flights) as compact JSON in `flight.metrics`; values the log cannot provide
  are empty. Cross-flight values (cell count, state of charge, capacity trend, …) depend on all flights of an
  aircraft and on the battery settings; they are calculated when they are shown.
- **Analysis version** (`flight.analysis_version`, `log_analysis.ANALYSIS_VERSION`) and the analysis settings
  used (`flight.analysis_params`). When the version is raised, flights with an older version are calculated
  again from the stored raw log in the background when the database is opened (`reanalysis.py`).
- **Sensors**: every column of the log that holds values, with its **role** (battery voltage, motor current,
  altitude, RSSI, …; `sensor_roles.py`). The roles are found from today's Ethos column names; columns without a
  known role are stored anyway. There is no user interface for the roles yet.
- **Time series** of every sensor at full resolution, plus the time axis (seconds since the start).

## Size

- Raw log: lzma (preset 6).
- Time series (`series_codec.py`): values are stored as integers scaled by 10^decimals (the smallest number of
  decimals that represents every value exactly, at most 6), as differences between neighbours in the smallest
  integer type that fits, compressed with zlib. Missing values (Ethos writes every sensor in its own rows) are a
  bit mask. Values that need more decimals are stored as float64. The encoding is lossless: reading the series
  back gives exactly the values of the CSV, and analysing them again gives the stored metrics.
- `examples/logs_2026` (71 files, 18.7 MB): database 5.0 MB – raw logs 2.6 MB, time series 1.8 MB, metrics
  0.04 MB.

## Performance

Measured with `examples/logs_2026` (71 logs):

| What | Time |
|---|---|
| Open the database and count logs/flights | about 1 ms |
| Program start with this database (window included) | about 1 s |
| Read one flight's time series back | about 10 ms |
| Import of the folder (background) | about 17 s; the window is never blocked for more than about 0.2 s |

## Schema (version 1)

| Table | Content |
|---|---|
| `aircraft` | `id`, `name` (model name from the file name, `""` = none) |
| `log_file` | `id`, `sha256` (unique), `original_name`, `source_path`, `size_bytes`, `imported_at` |
| `log_raw` | `log_id`, `data` (lzma-compressed file content); a table of its own so that queries never read it |
| `flight` | `id`, `log_id` (unique), `aircraft_id`, `start_time` (ISO text), `duration_s`, `log_duration_s`, `is_flight`, `is_flight_manual`, `detection_method`, `possible_duplicate`, `analysis_version`, `analysis_params` (JSON), `metrics` (JSON), `skip_reason` (JSON message: why the analysis found no flight) |
| `sensor` | `id`, `log_id`, `position` (column in the file, 0 = time axis), `column_name`, `role`, `sample_count` |
| `series` | `sensor_id`, `data` (encoded time series) |

Indexes: `flight (aircraft_id, start_time)` and `flight (start_time)` for the logbook and the filters.
Notes and anomalies get their own tables in a later schema version (WP-18).
