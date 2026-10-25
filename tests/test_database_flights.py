# -*- coding: utf-8 -*-
"""Single flight from the flight database: flight list, views per flight, analysis equal to the folder analysis."""

import numpy as np
import pandas as pd
import pytest

from helpers import EXAMPLE_FILES, EXAMPLES, analyse_logs, ela, write_glider_log
from ethosloganalyser.db import FlightDatabase, flight_preparation, flight_store, import_paths
from ethosloganalyser.gui import database_flights
from ethosloganalyser.plots.flight import FLIGHT_VIEWS


@pytest.fixture(scope="module")
def database(tmp_path_factory):
    folder = tmp_path_factory.mktemp("flights")
    write_glider_log(folder, "Glider-2030-02-01-12-00-00.csv", airborne_s=600, start="2030-02-01 12:00:00")
    db = FlightDatabase(str(folder / "flights.db"))
    import_paths(db, [str(EXAMPLES), str(folder)], ela.Params())
    yield db
    db.close()


def test_stored_flights_are_listed_oldest_first_with_aircraft(database):
    flights = database_flights.stored_flights(database.connection)
    assert [flight.aircraft for flight in flights] == ["Viper-Jet"] * 3 + ["Glider"]
    assert [flight.start_time for flight in flights] == sorted(flight.start_time for flight in flights)
    viper, glider = flights[0], flights[-1]
    assert viper.has_metrics and viper.drawn_mah > 1000
    assert not glider.has_metrics and glider.drawn_mah is None
    assert database_flights.flight_choice_label(viper, "Viper-Jet").startswith("13.09.2026 13:56 | Viper-Jet | ")


def test_views_follow_the_sensors_of_the_log(database):
    flights = database_flights.stored_flights(database.connection)
    viper_roles = flight_store.sensor_roles_of(database.connection, flights[0].log_id)
    assert database_flights.available_views(viper_roles) == FLIGHT_VIEWS
    glider_roles = flight_store.sensor_roles_of(database.connection, flights[-1].log_id)
    assert "battery" not in database_flights.available_views(glider_roles)
    assert database_flights.available_views({"Time": "time"}) == []


def test_aircraft_result_equals_the_folder_analysis(database):
    params = ela.Params(chem="Li-Ion", cells=13, nominal_mah=9000)
    prepared = database_flights.prepare_aircraft(database.connection, "Viper-Jet")
    result = database_flights.aircraft_result(prepared, params, "Viper-Jet")
    folder = analyse_logs(EXAMPLE_FILES, params)
    pd.testing.assert_frame_equal(result.df.drop(columns=["pfad"]), folder.df.drop(columns=["pfad"]))
    for log_id, from_db, from_file in zip(prepared, result.df["pfad"], folder.df["pfad"]):
        assert from_db == database_flights.flight_path(log_id)
        # the statistics series are stored; the single flight adds all the others (complete_flight)
        statistics_series = result.series[from_db]
        all_series = database_flights.complete_flight(database.connection, log_id)[1]
        for key, values in folder.series[from_file].items():
            if isinstance(values, np.ndarray):
                assert np.array_equal(all_series[key], values, equal_nan=True), key
                if key in flight_preparation.STATISTICS_SERIES_KEYS:
                    assert np.array_equal(statistics_series[key], values, equal_nan=True), key
    assert result.meta["flags"] == folder.meta["flags"]


def test_preparation_can_be_cancelled(database):
    assert database_flights.prepare_aircraft(database.connection, "Viper-Jet", should_cancel=lambda: True) is None


def test_aircraft_without_battery_data_has_nothing_to_prepare(database):
    prepared = database_flights.prepare_aircraft(database.connection, "Glider")
    assert prepared == {}
    assert database_flights.aircraft_result(prepared, ela.Params(), "Glider").df.empty
