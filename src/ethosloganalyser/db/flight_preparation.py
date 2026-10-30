# -*- coding: utf-8 -*-
"""Prepared per-flight values for the statistics, stored once per flight (table flight_preparation, schema 3).

The statistics and the single flight are built on the per-flight analysis (analysis/flight.analyse_frame) of the
stored time series of every flight. Repeating it for all flights at every program start took about 50 ms per
flight, so its result is now stored when a log is imported or calculated again (reanalysis.py) and only read back
at the start (gui/database_flights.prepare_aircraft).

What is stored per flight:

* the per-flight values (the row of the flight table without file name, path and date) as JSON,
* the time series that the cross-flight analysis and the statistics charts use (STATISTICS_SERIES_KEYS), each one
  encoded losslessly with series_codec, so the statistics are exactly the same as with a new analysis.

The other time series (voltage, altitude, receiver, sticks, ...) are only drawn on the single-flight page. Storing
them as well would more than double the size of the database, so the single flight works them out for the one
flight that is opened (analyse_stored_flight). The steady-state points of the motor curve depend only on RPM and
power and are worked out again when reading (well under a millisecond per flight).

Nothing here depends on the battery settings: the cross-flight part stays a quick calculation on demand
(gui/database_flights.aircraft_result).
"""

import dataclasses
import json
import struct
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..analysis.flight import analyse_frame
from ..analysis.motor_curve import steady_points
from ..config import Params
from . import flight_store
from .log_analysis import ANALYSIS_VERSION, analysis_params_to_json, metrics_from_json, metrics_to_json
from .series_codec import decode_series, encode_series

# Raise when what is stored changes (e.g. another time series is needed by the statistics): the prepared values of
# all flights are then worked out again in the background when the database is opened.
PREPARATION_VERSION = 1

# the time series the cross-flight analysis (analysis/fleet.py: timer from t, q and i; motor curve from rpm and p)
# and the statistics charts (plots/overview.py: gas_hist, rpm, p) read
STATISTICS_SERIES_KEYS = ("t", "i", "q", "p", "rpm", "gas_hist")

# a time series every complete per-flight analysis has, but the stored statistics series do not
_SINGLE_FLIGHT_ONLY_KEY = "u"

# "pfad" of a database flight inside an analysis result: there is no file, the key names the stored log
PATH_PREFIX = "db:"

# one entry of the series blob: length of the key (ASCII), length of the series_codec blob that follows the key
_ENTRY_HEADER = struct.Struct("<BI")

# SQL condition: the prepared values (alias "prepared") belong to the current analysis of the flight
_IS_CURRENT = ("(prepared.log_id IS NOT NULL AND prepared.preparation_version = ? "
               "AND prepared.analysis_version = flight.analysis_version "
               "AND prepared.analysis_params = flight.analysis_params)")


def flight_path(log_id):
    """The "pfad" of a database flight in an analysis result."""
    return f"{PATH_PREFIX}{log_id}"


# ---------------- analysis ----------------
def params_from_text(analysis_params_text):
    """The analysis settings of a flight as Params: the text stored with the flight (flight.analysis_params) on top
    of the defaults. The single-flight charts and the flight recorder work out their period with these."""
    return dataclasses.replace(Params(), **json.loads(analysis_params_text))


def analyse_stored_flight(frame, log_id, file_name, start_time, analysis_params_text):
    """Per-flight analysis of a stored flight from its time series (flight_store.load_log_frame).

    Returns (row, series) with all time series, as the single flight needs them, or None if the analysis gives no
    result. analysis_params_text are the settings stored with the flight (flight.analysis_params); the other
    settings do not change the per-flight result.
    """
    params = params_from_text(analysis_params_text)
    try:
        row, _reason = analyse_frame(frame, file_name, params, start_time=start_time)
    except Exception:                 # treated like "no result": one broken log must not stop the others
        return None
    if row is None:
        return None
    series = row.pop("_series")
    # the steady-state points for the overall motor curve depend only on this flight: worked out once here, so
    # the cross-flight analysis of a filter does not repeat them for every flight
    series["steady_points"] = steady_points(series["rpm"], series["p"])
    row["datei"] = file_name
    row["pfad"] = flight_path(log_id)
    return row, series


def has_all_series(series):
    """True for the series of a complete analysis, False for the stored statistics series of a flight."""
    return _SINGLE_FLIGHT_ONLY_KEY in series


# ---------------- encoding ----------------
def encode_statistics_series(series):
    """The statistics series of a flight (STATISTICS_SERIES_KEYS; missing ones are left out) as one blob."""
    entries = []
    for key in STATISTICS_SERIES_KEYS:
        values = series.get(key)
        if values is None:
            continue
        key_bytes = key.encode("ascii")
        encoded = encode_series(values)
        entries.append(_ENTRY_HEADER.pack(len(key_bytes), len(encoded)) + key_bytes + encoded)
    return b"".join(entries)


def decode_statistics_series(blob):
    """Series dict from encode_statistics_series (missing series as None) plus the steady-state points."""
    series = {key: None for key in STATISTICS_SERIES_KEYS}
    offset = 0
    while offset < len(blob):
        key_length, encoded_length = _ENTRY_HEADER.unpack_from(blob, offset)
        offset += _ENTRY_HEADER.size
        key = blob[offset:offset + key_length].decode("ascii")
        offset += key_length
        series[key] = decode_series(blob[offset:offset + encoded_length])
        offset += encoded_length
    series["steady_points"] = steady_points(series["rpm"], series["p"])
    return series


def row_from_stored(row_text, log_id, file_name, start_time):
    """The row of a flight from the stored JSON, with file name, path and date in the same order as the analysis
    gives them (the order of the columns of the flight table)."""
    row = {"datei": file_name, "pfad": flight_path(log_id), "datum": start_time}
    row.update(metrics_from_json(row_text))
    return row


# ---------------- storing ----------------
def store_preparation(connection, log_id, analysis_version, analysis_params_text, prepared):
    """Stores the prepared values of a flight (inside the caller's transaction). prepared: (row, series) from
    analyse_stored_flight, or None if the analysis gave no result (stored as such, so it is not tried again)."""
    row_text = series_blob = None
    if prepared is not None:
        row, series = prepared
        row_text, series_blob = metrics_to_json(row), encode_statistics_series(series)
    connection.execute(
        "INSERT OR REPLACE INTO flight_preparation (log_id, preparation_version, analysis_version, analysis_params, "
        "row, series) VALUES (?, ?, ?, ?, ?, ?)",
        (log_id, PREPARATION_VERSION, analysis_version, analysis_params_text, row_text, series_blob))


def store_for_new_analysis(connection, log_id, file_name, analysed):
    """Works out and stores the prepared values of a log that was just imported or calculated again
    (log_analysis.AnalysedLog), from its time series as they are stored. Logs without metrics get none."""
    if analysed.metrics is None:
        connection.execute("DELETE FROM flight_preparation WHERE log_id = ?", (log_id,))
        return
    frame = flight_store.frame_from_encoded_series(
        (sensor.column_name, sensor.encoded) for sensor in analysed.sensors)
    params_text = analysis_params_to_json(analysed.analysis_params)
    prepared = analyse_stored_flight(frame, log_id, file_name, analysed.start_time, params_text)
    store_preparation(connection, log_id, ANALYSIS_VERSION, params_text, prepared)


# ---------------- outdated values ----------------
def outdated_log_ids(connection):
    """Flights with metrics whose prepared values are missing (e.g. after the update to schema version 3) or
    belong to another analysis, oldest first."""
    return [row[0] for row in connection.execute(
        "SELECT flight.log_id FROM flight LEFT JOIN flight_preparation AS prepared ON prepared.log_id = flight.log_id "
        f"WHERE flight.metrics IS NOT NULL AND NOT {_IS_CURRENT} ORDER BY flight.start_time",
        (PREPARATION_VERSION,))]


def prepare_stored_flight(connection, log_id):
    """Works out the prepared values of one stored flight from its stored time series and stores them."""
    file_name, start_text, analysis_version, params_text = connection.execute(
        "SELECT log_file.original_name, flight.start_time, flight.analysis_version, flight.analysis_params "
        "FROM flight JOIN log_file ON log_file.id = flight.log_id WHERE flight.log_id = ?", (log_id,)).fetchone()
    prepared = analyse_stored_flight(flight_store.load_log_frame(connection, log_id), log_id, file_name,
                                     flight_store.parse_start_time(start_text), params_text)
    with connection:
        store_preparation(connection, log_id, analysis_version, params_text, prepared)


def prepare_outdated(connection, progress=None, should_cancel=None):
    """Works out the missing or outdated prepared values of all flights. Returns the number of flights done.

    progress(done, total) is called after every flight; should_cancel() is checked before every flight - the
    flights done until then keep their values, the others are done the next time.
    """
    log_ids = outdated_log_ids(connection)
    done = 0
    for log_id in log_ids:
        if should_cancel is not None and should_cancel():
            break
        prepare_stored_flight(connection, log_id)
        done += 1
        if progress is not None:
            progress(done, len(log_ids))
    return done


# ---------------- reading ----------------
@dataclass
class StoredFlightPreparation:
    """A flight of an aircraft with its prepared values as stored (row_text/series_blob only if is_current)."""
    log_id: int
    file_name: str
    start_time: datetime
    analysis_params_text: str
    is_current: bool
    row_text: Optional[str]
    series_blob: Optional[bytes]

    def prepared(self):
        """(row, statistics series) from the stored values, or None if the analysis gave no result."""
        if self.row_text is None:
            return None
        return (row_from_stored(self.row_text, self.log_id, self.file_name, self.start_time),
                decode_statistics_series(self.series_blob))


def flights_of_aircraft(connection, aircraft):
    """The flights of an aircraft that have metrics (oldest first) with their stored prepared values."""
    rows = connection.execute(
        "SELECT flight.log_id, log_file.original_name, flight.start_time, flight.analysis_params, "
        f"{_IS_CURRENT}, prepared.row, prepared.series FROM flight "
        "JOIN aircraft ON aircraft.id = flight.aircraft_id JOIN log_file ON log_file.id = flight.log_id "
        "LEFT JOIN flight_preparation AS prepared ON prepared.log_id = flight.log_id "
        "WHERE aircraft.name = ? AND coalesce(flight.is_flight_manual, flight.is_flight) = 1 "
        "AND flight.metrics IS NOT NULL ORDER BY flight.start_time", (PREPARATION_VERSION, aircraft)).fetchall()
    return [StoredFlightPreparation(log_id=log_id, file_name=file_name,
                                    start_time=flight_store.parse_start_time(start_text),
                                    analysis_params_text=params_text, is_current=bool(is_current),
                                    row_text=row_text if is_current else None,
                                    series_blob=series_blob if is_current else None)
            for log_id, file_name, start_text, params_text, is_current, row_text, series_blob in rows]
