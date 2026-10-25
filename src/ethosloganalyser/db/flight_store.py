# -*- coding: utf-8 -*-
"""Writing logs and flights into the database and reading them back."""

import json
import lzma
from datetime import datetime

import pandas as pd

from .log_analysis import ANALYSIS_VERSION, message_to_json, metrics_to_json
from .series_codec import decode_series

START_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
LZMA_PRESET = 6


def start_time_text(start_time):
    """How a start time is stored (sortable ISO text, seconds)."""
    return start_time.strftime(START_TIME_FORMAT)


def parse_start_time(text):
    return datetime.strptime(text, START_TIME_FORMAT)


def aircraft_id(connection, name):
    """Id of the aircraft with this model name; the aircraft is created if it is new."""
    row = connection.execute("SELECT id FROM aircraft WHERE name = ?", (name,)).fetchone()
    if row is not None:
        return row[0]
    return connection.execute("INSERT INTO aircraft (name) VALUES (?)", (name,)).lastrowid


def find_log_by_hash(connection, sha256):
    """(log id, original file name) of an already imported log with this content, or None."""
    return connection.execute("SELECT id, original_name FROM log_file WHERE sha256 = ?", (sha256,)).fetchone()


def find_flight_at(connection, aircraft, start_time):
    """Original file name of a log of the same aircraft with the same start time, or None."""
    row = connection.execute(
        "SELECT log_file.original_name FROM flight JOIN log_file ON log_file.id = flight.log_id "
        "WHERE flight.aircraft_id = ? AND flight.start_time = ? LIMIT 1",
        (aircraft, start_time_text(start_time))).fetchone()
    return row[0] if row else None


def _insert_sensors(connection, log_id, sensors):
    for sensor in sensors:
        sensor_id = connection.execute(
            "INSERT INTO sensor (log_id, position, column_name, role, sample_count) VALUES (?, ?, ?, ?, ?)",
            (log_id, sensor.position, sensor.column_name, sensor.role, sensor.sample_count)).lastrowid
        connection.execute("INSERT INTO series (sensor_id, data) VALUES (?, ?)", (sensor_id, sensor.encoded))


def _flight_values(analysed):
    detection = analysed.detection
    return (detection.duration_s, analysed.log_duration_s, int(detection.is_flight), detection.method,
            ANALYSIS_VERSION, json.dumps(analysed.analysis_params, sort_keys=True),
            metrics_to_json(analysed.metrics), message_to_json(analysed.skip_reason))


def insert_log(connection, *, sha256, original_name, source_path, content, model, analysed,
               possible_duplicate):
    """Stores a new log with its raw content, flight, sensors and time series (inside the caller's
    transaction). Returns the new log id."""
    log_id = connection.execute(
        "INSERT INTO log_file (sha256, original_name, source_path, size_bytes, imported_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (sha256, original_name, source_path, len(content),
         datetime.now().strftime(START_TIME_FORMAT))).lastrowid
    connection.execute("INSERT INTO log_raw (log_id, data) VALUES (?, ?)",
                       (log_id, lzma.compress(content, preset=LZMA_PRESET)))
    connection.execute(
        "INSERT INTO flight (log_id, aircraft_id, start_time, duration_s, log_duration_s, is_flight, "
        "detection_method, analysis_version, analysis_params, metrics, skip_reason, possible_duplicate) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (log_id, aircraft_id(connection, model), start_time_text(analysed.start_time))
        + _flight_values(analysed) + (int(possible_duplicate),))
    _insert_sensors(connection, log_id, analysed.sensors)
    return log_id


def replace_analysis(connection, log_id, analysed):
    """Stores a new analysis of an existing log (after an analysis change). A flight/non-flight decision
    made by hand (is_flight_manual) is kept."""
    connection.execute(
        "UPDATE flight SET duration_s = ?, log_duration_s = ?, is_flight = ?, detection_method = ?, "
        "analysis_version = ?, analysis_params = ?, metrics = ?, skip_reason = ? WHERE log_id = ?",
        _flight_values(analysed) + (log_id,))
    connection.execute("DELETE FROM sensor WHERE log_id = ?", (log_id,))
    _insert_sensors(connection, log_id, analysed.sensors)


def raw_content(connection, log_id):
    """The original file content of a log (bytes)."""
    row = connection.execute("SELECT data FROM log_raw WHERE log_id = ?", (log_id,)).fetchone()
    return lzma.decompress(row[0])


def load_log_frame(connection, log_id):
    """The stored time series of a log as a DataFrame: column "Time" (seconds since the start) followed by
    the sensor columns in the order of the original file. Values missing in a row are NaN, as in the log."""
    rows = connection.execute(
        "SELECT sensor.column_name, series.data FROM sensor JOIN series ON series.sensor_id = sensor.id "
        "WHERE sensor.log_id = ? ORDER BY sensor.position", (log_id,)).fetchall()
    return pd.DataFrame({name: decode_series(blob) for name, blob in rows})


def sensor_roles_of(connection, log_id):
    """{column name: role} of the stored sensors of a log."""
    return dict(connection.execute("SELECT column_name, role FROM sensor WHERE log_id = ? ORDER BY position",
                                   (log_id,)).fetchall())


def flight_rows(connection):
    """All flights with their stored columns (for checks and later views), ordered by start time."""
    return pd.read_sql_query(
        "SELECT flight.*, aircraft.name AS aircraft, log_file.original_name FROM flight "
        "JOIN aircraft ON aircraft.id = flight.aircraft_id JOIN log_file ON log_file.id = flight.log_id "
        "ORDER BY flight.start_time, log_file.original_name", connection)
