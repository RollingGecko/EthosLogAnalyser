# -*- coding: utf-8 -*-
"""Prepared per-flight values for the statistics (db/flight_preparation.py, schema 3): stored at import and
recalculation, read instead of analysing again, worked out once for older databases."""

import shutil

import numpy as np
import pandas as pd
import pytest

from helpers import EXAMPLE_FILES, ela, write_ethos_csv, write_glider_log
from ethosloganalyser.db import FlightDatabase, annotations, flight_preparation, flight_store, import_paths, schema
from ethosloganalyser.db import log_analysis, reanalysis
from ethosloganalyser.gui import database_flights

LI_ION_13S = ela.Params(chem="Li-Ion", cells=13, nominal_mah=9000)


@pytest.fixture
def database(tmp_path):
    db = FlightDatabase(str(tmp_path / "flights.db"))
    import_paths(db, [str(path) for path in EXAMPLE_FILES], LI_ION_13S)
    yield db
    db.close()


def _new_analysis(connection, aircraft="Viper-Jet"):
    """{log_id: (row, series)} of a new analysis of the stored time series of every flight (the way before
    schema 3)."""
    analysed = {}
    for flight in flight_preparation.flights_of_aircraft(connection, aircraft):
        result = database_flights.complete_flight(connection, flight.log_id)
        if result is not None:
            analysed[flight.log_id] = result
    return analysed


def _assert_same_values(stored_row, stored_series, row, series):
    assert list(stored_row) == list(row)                          # same columns in the same order
    for key, value in row.items():
        if isinstance(value, float) and np.isnan(value):
            assert np.isnan(stored_row[key]), key
        else:
            assert stored_row[key] == value and type(stored_row[key]) is type(value), key
    for key in flight_preparation.STATISTICS_SERIES_KEYS:
        if series[key] is None:
            assert stored_series[key] is None, key
        else:
            assert np.array_equal(stored_series[key], series[key], equal_nan=True), key
    for stored_points, points in zip(stored_series["steady_points"], series["steady_points"]):
        assert np.array_equal(stored_points, points)


def _preparation_rows(connection):
    return {row[0]: row[1:] for row in connection.execute(
        "SELECT log_id, preparation_version, analysis_version, analysis_params, row, series FROM flight_preparation")}


def _motor_flight(folder, name):
    t = np.arange(0, 300, 0.25)
    current = np.where((t > 10) & (t < 280), 20 + 10 * np.sin(t / 7), 0.0)
    stamp = name[-23:-4]
    return write_ethos_csv(folder, name, t, 50 - 0.05 * current - 0.002 * t, current,
                           start=f"{stamp[:10]} {stamp[11:].replace('-', ':')}")


# ---------------- storing and reading ----------------
def test_import_stores_the_values_of_a_new_analysis(database):
    connection = database.connection
    assert flight_preparation.outdated_log_ids(connection) == []
    new_analysis = _new_analysis(connection)
    assert len(new_analysis) == 3
    prepared = database_flights.prepare_aircraft(connection, "Viper-Jet")
    assert list(prepared) == list(new_analysis)
    for log_id, (row, series) in new_analysis.items():
        stored_row, stored_series = prepared[log_id]
        _assert_same_values(stored_row, stored_series, row, series)
        assert not flight_preparation.has_all_series(stored_series) and flight_preparation.has_all_series(series)


def test_stored_values_are_read_without_analysing_again(database, monkeypatch):
    def no_analysis(*args, **kwargs):
        raise AssertionError("analysed again")

    monkeypatch.setattr(flight_preparation, "analyse_stored_flight", no_analysis)
    assert len(database_flights.prepare_aircraft(database.connection, "Viper-Jet")) == 3


def test_cross_flight_result_is_the_same_as_with_a_new_analysis(database):
    connection = database.connection
    from_stored = database_flights.aircraft_result(database_flights.prepare_aircraft(connection, "Viper-Jet"),
                                                   LI_ION_13S, "Viper-Jet")
    from_analysis = database_flights.aircraft_result(_new_analysis(connection), LI_ION_13S, "Viper-Jet")
    pd.testing.assert_frame_equal(from_stored.df, from_analysis.df)
    assert from_stored.meta["flags"] == from_analysis.meta["flags"]


def test_statistics_series_round_trip():
    series = {"t": np.arange(0, 10, 0.25), "i": np.linspace(0, 30, 40) / 3, "q": np.cumsum(np.full(40, 1 / 3)),
              "p": np.full(40, np.nan), "rpm": None, "gas_hist": np.array([0.5, 0.25, 0.0])}
    decoded = flight_preparation.decode_statistics_series(flight_preparation.encode_statistics_series(series))
    for key, values in series.items():
        if values is None:
            assert decoded[key] is None
        else:
            assert np.array_equal(decoded[key], values, equal_nan=True), key
    assert [len(points) for points in decoded["steady_points"]] == [0, 0]


# ---------------- keeping them up to date ----------------
def test_missing_values_fall_back_to_the_analysis_and_are_worked_out_once(database):
    connection = database.connection
    expected = database_flights.prepare_aircraft(connection, "Viper-Jet")
    with connection:
        connection.execute("DELETE FROM flight_preparation")
    log_ids = flight_preparation.outdated_log_ids(connection)
    assert log_ids == list(expected)
    fallback = database_flights.prepare_aircraft(connection, "Viper-Jet")
    for log_id, (row, series) in fallback.items():
        assert flight_preparation.has_all_series(series)
        _assert_same_values(expected[log_id][0], expected[log_id][1], row, series)
    progress = []
    assert flight_preparation.prepare_outdated(connection, progress=lambda *state: progress.append(state)) == 3
    assert progress[-1] == (3, 3)
    assert flight_preparation.outdated_log_ids(connection) == []
    assert flight_preparation.prepare_outdated(connection) == 0


def test_working_out_can_be_cancelled_and_continued(database):
    connection = database.connection
    with connection:
        connection.execute("DELETE FROM flight_preparation")
    calls = []
    assert flight_preparation.prepare_outdated(connection, progress=lambda *state: calls.append(state),
                                               should_cancel=lambda: len(calls) >= 1) == 1
    assert len(flight_preparation.outdated_log_ids(connection)) == 2
    assert flight_preparation.prepare_outdated(connection) == 2


def test_a_new_import_adds_only_the_values_of_the_new_log(database, tmp_path):
    connection = database.connection
    before = _preparation_rows(connection)
    import_paths(database, [str(_motor_flight(tmp_path, "Synth-2026-05-01-12-00-00.csv"))], LI_ION_13S)
    after = _preparation_rows(connection)
    assert {log_id: after[log_id] for log_id in before} == before
    (new_log_id,) = set(after) - set(before)
    assert after[new_log_id][3] is not None                       # the synthetic flight has a result


def test_a_log_without_metrics_gets_no_values(database, tmp_path):
    import_paths(database, [str(write_glider_log(tmp_path, "Glider-2026-06-01-14-00-00.csv", airborne_s=600))],
                 LI_ION_13S)
    connection = database.connection
    glider = connection.execute("SELECT log_id FROM flight JOIN aircraft ON aircraft.id = aircraft_id "
                                "WHERE aircraft.name = 'Glider'").fetchone()[0]
    assert glider not in _preparation_rows(connection)
    assert flight_preparation.outdated_log_ids(connection) == []


def test_switching_between_flight_and_no_flight_keeps_the_values(database):
    connection = database.connection
    before = _preparation_rows(connection)
    log_id = next(iter(before))
    flight_store.set_flight_manual(connection, log_id, 0)
    assert _preparation_rows(connection) == before
    assert log_id not in database_flights.prepare_aircraft(connection, "Viper-Jet")
    flight_store.set_flight_manual(connection, log_id, None)
    assert log_id in database_flights.prepare_aircraft(connection, "Viper-Jet")


def test_a_raised_analysis_version_works_out_the_values_again(database, monkeypatch):
    connection = database.connection
    newer = log_analysis.ANALYSIS_VERSION + 1
    for module in (log_analysis, flight_store, reanalysis, flight_preparation):
        monkeypatch.setattr(module, "ANALYSIS_VERSION", newer)
    log_ids = reanalysis.outdated_log_ids(connection)
    assert len(log_ids) == 3
    # the stored values still belong to the stored (old) analysis of the flights; the recalculation renews both
    assert reanalysis.reanalyse_outdated(database, ela.Params()) == 3
    assert flight_preparation.outdated_log_ids(connection) == []
    assert {row[1] for row in _preparation_rows(connection).values()} == {newer}


def test_a_changed_analysis_setting_makes_the_values_outdated(database):
    connection = database.connection
    log_id = next(iter(_preparation_rows(connection)))
    params_text = log_analysis.analysis_params_to_json(dict(log_analysis.analysis_params_of(ela.Params()),
                                                            min_flight_s=10000))
    with connection:
        connection.execute("UPDATE flight SET analysis_params = ? WHERE log_id = ?", (params_text, log_id))
    assert flight_preparation.outdated_log_ids(connection) == [log_id]
    flight_preparation.prepare_outdated(connection)
    stored = _preparation_rows(connection)[log_id]
    assert stored[2] == params_text and stored[3] is None          # far too short for this setting: no result
    assert log_id not in database_flights.prepare_aircraft(connection, "Viper-Jet")


def test_a_raised_preparation_version_works_out_all_values_again(database, monkeypatch):
    monkeypatch.setattr(flight_preparation, "PREPARATION_VERSION", flight_preparation.PREPARATION_VERSION + 1)
    assert len(flight_preparation.outdated_log_ids(database.connection)) == 3


def test_clear_removes_the_values(database):
    database.clear()
    assert _preparation_rows(database.connection) == {}


# ---------------- migration ----------------
def test_a_version_2_database_is_migrated_and_worked_out_once(database, tmp_path):
    """A database of schema version 2 (without the table) keeps its flights, notes and anomalies; the values are
    worked out once and then read."""
    connection = database.connection
    expected = database_flights.prepare_aircraft(connection, "Viper-Jet")
    log_id = next(iter(expected))
    annotations.set_note(connection, log_id, "before the update")
    with connection:
        connection.execute("DROP TABLE flight_preparation")
        connection.execute("PRAGMA user_version = 2")
    database.close()
    path = tmp_path / "version2.db"
    shutil.copy(database.path, path)

    migrated = FlightDatabase(str(path))
    connection = migrated.connection
    assert connection.execute("PRAGMA user_version").fetchone()[0] == schema.SCHEMA_VERSION == 3
    assert migrated.stats().flight_count == 3
    assert annotations.note_of(connection, log_id) == "before the update"
    assert flight_preparation.outdated_log_ids(connection) == list(expected)
    assert flight_preparation.prepare_outdated(connection) == 3
    migrated.close()

    again = FlightDatabase(str(path))
    assert flight_preparation.outdated_log_ids(again.connection) == []
    for log_id_read, (row, series) in database_flights.prepare_aircraft(again.connection, "Viper-Jet").items():
        _assert_same_values(row, series, *expected[log_id_read])
    again.close()


# ---------------- single flight ----------------
def test_the_single_flight_adds_all_series_of_the_flight_it_shows(database):
    from types import SimpleNamespace
    from ethosloganalyser.gui.flight_cache import FlightCache

    controller = SimpleNamespace(database=database, generation=1, path=database.path)
    cache = FlightCache(root=None, database=controller, params_for=lambda aircraft: LI_ION_13S)
    cache.refresh()
    cache.prepared["Viper-Jet"] = database_flights.prepare_aircraft(database.connection, "Viper-Jet")
    statistics_table = cache.result("Viper-Jet")[0].df.copy()
    shown, other = cache.flights[0].log_id, cache.flights[1].log_id
    result, params = cache.result_with_all_series("Viper-Jet", shown)
    assert params == LI_ION_13S
    assert flight_preparation.has_all_series(result.series[database_flights.flight_path(shown)])
    assert not flight_preparation.has_all_series(result.series[database_flights.flight_path(other)])
    assert flight_preparation.has_all_series(cache.prepared["Viper-Jet"][shown][1])
    pd.testing.assert_frame_equal(result.df, statistics_table)
