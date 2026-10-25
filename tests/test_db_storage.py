# -*- coding: utf-8 -*-
"""Flight database: schema, opening, save as, emptying, and the lossless time series codec."""

import sqlite3

import numpy as np
import pytest

from ethosloganalyser.db import DatabaseError, FlightDatabase, schema
from ethosloganalyser.db.series_codec import FLOAT_STORAGE, decimals_needed, decode_series, encode_series


def test_new_database_has_schema_and_is_recognised(tmp_path):
    path = tmp_path / "sub" / "flights.db"
    database = FlightDatabase(str(path))
    tables = {row[0] for row in database.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"aircraft", "log_file", "log_raw", "flight", "sensor", "series"} <= tables
    database.close()

    reopened = FlightDatabase(str(path))
    assert reopened.connection.execute("PRAGMA user_version").fetchone()[0] == schema.SCHEMA_VERSION
    assert reopened.stats().log_count == 0
    reopened.close()


def test_foreign_sqlite_file_is_refused(tmp_path):
    path = tmp_path / "other.db"
    connection = sqlite3.connect(str(path))
    connection.execute("CREATE TABLE something (x)")
    connection.commit()
    connection.close()
    with pytest.raises(DatabaseError):
        FlightDatabase(str(path))


def test_text_file_is_refused(tmp_path):
    path = tmp_path / "notes.db"
    path.write_text("this is not a database " * 100, encoding="utf-8")
    with pytest.raises(DatabaseError):
        FlightDatabase(str(path))


def test_newer_schema_version_is_refused(tmp_path):
    path = tmp_path / "future.db"
    database = FlightDatabase(str(path))
    database.connection.execute(f"PRAGMA user_version = {schema.SCHEMA_VERSION + 1}")
    database.close()
    with pytest.raises(DatabaseError):
        FlightDatabase(str(path))


def test_create_new_replaces_the_file(tmp_path):
    path = tmp_path / "flights.db"
    database = FlightDatabase(str(path))
    database.connection.execute("INSERT INTO aircraft (name) VALUES ('Old')")
    database.connection.commit()
    database.close()
    fresh = FlightDatabase.create_new(str(path))
    assert fresh.connection.execute("SELECT count(*) FROM aircraft").fetchone()[0] == 0
    fresh.close()


def test_save_as_writes_a_copy_and_keeps_the_open_database(tmp_path):
    database = FlightDatabase(str(tmp_path / "flights.db"))
    database.connection.execute("INSERT INTO aircraft (name) VALUES ('Viper')")
    database.connection.commit()
    copy_path = tmp_path / "copy.db"
    database.save_as(str(copy_path))
    assert database.path == str(tmp_path / "flights.db")
    copy = FlightDatabase(str(copy_path))
    assert copy.connection.execute("SELECT name FROM aircraft").fetchall() == [("Viper",)]
    copy.close()
    database.close()


@pytest.mark.parametrize("values", [
    [54.63, 54.6, np.nan, 54.58, 12.0, -3.5],                 # Ethos voltages with gaps
    [0, 1, 0, -1, 1, 1, 0],                                  # switch
    [-1024, 1024, 0, 512],                                   # stick
    np.round(np.linspace(0, 951.7, 3000), 3),                # time axis in ms resolution
    [52.520008, 13.404954, np.nan],                          # GPS coordinates
    [1 / 3, np.pi, 2.0 ** 0.5],                              # more than 6 decimals: stored as float
    [np.nan, np.nan],                                        # only missing values
    [],                                                      # empty
    [1e300, -1e300],                                         # too large for scaled integers
    [np.inf, 1.0],                                           # infinity
    [100000, -100000, 5e9, -5e9, 7],                         # large jumps (wide integer type)
])
def test_series_round_trip_is_lossless(values):
    values = np.asarray(values, dtype=float)
    decoded = decode_series(encode_series(values))
    assert decoded.shape == values.shape
    assert np.array_equal(decoded, values, equal_nan=True)


def test_series_are_compact():
    t = np.round(np.arange(0, 600, 0.25), 2)
    voltage = np.round(50 - 0.01 * t + 0.02 * np.sin(t), 2)
    assert len(encode_series(voltage)) < voltage.nbytes / 10


def test_decimals_needed():
    assert decimals_needed(np.array([1.0, 2.0])) == 0
    assert decimals_needed(np.array([54.63, 1.5])) == 2
    assert decimals_needed(np.array([1 / 3])) == FLOAT_STORAGE
