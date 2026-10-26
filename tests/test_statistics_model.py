# -*- coding: utf-8 -*-
"""Statistics from the flight database (gui/statistics_model.py): filter, one aircraft per analysis, states."""

from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

from helpers import EXAMPLE_FILES, analyse_logs, ela, write_glider_log
from ethosloganalyser.analysis.periods import FlightFilter
from ethosloganalyser.db import FlightDatabase, import_paths
from ethosloganalyser.gui import database_flights
from ethosloganalyser.gui.flight_filter import FilterState
from ethosloganalyser.gui.statistics_model import (EMPTY_DATABASE, EXPERIMENTAL_NOTICE, FAILED, NO_BATTERY_DATA,
                                                   NO_MATCH, PREPARING, READY, SEVERAL_AIRCRAFT, StatisticsModel,
                                                   filter_description)
from ethosloganalyser.gui.statistics_page import report_lines
from ethosloganalyser.i18n import set_language

LI_ION_13S = ela.Params(chem="Li-Ion", cells=13, nominal_mah=9000)


class FakeCache:
    """What StatisticsModel needs of the FlightCache: the flights, prepared aircraft, preparing on request."""

    def __init__(self, connection):
        self.connection = connection
        self.flights = database_flights.stored_flights(connection)
        self.generation = 1
        self.prepared, self.failed, self.requested = {}, set(), []

    def prepare(self, aircraft):
        self.requested.append(aircraft)

    def finish(self, aircraft):
        self.prepared[aircraft] = database_flights.prepare_aircraft(self.connection, aircraft)


@pytest.fixture(scope="module")
def database(tmp_path_factory):
    folder = tmp_path_factory.mktemp("statistics")
    write_glider_log(folder, "Glider-2026-06-01-14-00-00.csv", airborne_s=600)
    db = FlightDatabase(str(folder / "flights.db"))
    import_paths(db, [str(path) for path in EXAMPLE_FILES] + [str(folder)], LI_ION_13S)
    yield db
    db.close()


@pytest.fixture
def model(database):
    cache = FakeCache(database.connection)
    state = FilterState()
    statistics = StatisticsModel(cache, state, lambda aircraft: LI_ION_13S)
    statistics.state, statistics.fake_cache = state, cache
    return statistics


def test_several_chosen_aircraft_ask_for_one_but_one_chosen_aircraft_is_analysed(model):
    model.state.set(aircraft={"Glider", "Viper-Jet"})                 # both chosen (here: every aircraft)
    assert model.view().state == SEVERAL_AIRCRAFT
    model.state.set(aircraft=frozenset())                             # nothing chosen: no flight, no error
    view = model.view()
    assert view.state == NO_MATCH and view.n_flights == 0 and view.n_total == 4 and view.message == \
        "Kein Flug passt zum Filter."
    model.state.set(aircraft={"Glider"}, year={2020, 2026})           # one aircraft within several years
    assert model.view().aircraft_names == ("Glider",)


def test_several_aircraft_ask_for_one(model):
    view = model.view()
    assert view.state == SEVERAL_AIRCRAFT and view.aircraft_names == ("Glider", "Viper-Jet")
    assert view.n_flights == view.n_total == 4
    set_language("de")
    assert view.message.startswith("Bitte im Filter ein Flugzeug wählen") and "Glider, Viper-Jet" in view.message


def test_an_aircraft_is_prepared_then_analysed_like_its_log_files(model):
    model.state.set(aircraft="Viper-Jet")
    assert model.view(prepare=False).state == PREPARING and model.fake_cache.requested == []
    assert model.view().state == PREPARING and model.fake_cache.requested == ["Viper-Jet"]
    model.fake_cache.finish("Viper-Jet")
    view = model.view()
    assert view.state == READY and view.message == "" and view.n_flights == 3
    expected = analyse_logs(EXAMPLE_FILES, LI_ION_13S)
    pd.testing.assert_frame_equal(expected.df.drop(columns=["pfad"]), view.result.df.drop(columns=["pfad"]))
    assert model.view().result is view.result                       # nothing changed: not calculated again


def test_one_aircraft_in_the_filter_needs_no_choice(model):
    model.fake_cache.finish("Viper-Jet")
    model.state.set(date_from=date(2026, 9, 1))                     # only Viper-Jet flights after the glider
    view = model.view()
    assert view.state == READY and view.aircraft == "Viper-Jet" and view.n_flights == 3


def test_the_filter_selects_the_flights_of_the_analysis(model):
    model.fake_cache.finish("Viper-Jet")
    model.state.set(aircraft="Viper-Jet", month=10)
    view = model.view()
    assert view.n_flights == 1 and list(view.result.df["Flug"]) == [1]       # numbered within the filter
    assert view.result.df["datum"].iloc[0].month == 10
    expected = analyse_logs([path for path in EXAMPLE_FILES if "-10-" in path.name], LI_ION_13S)
    pd.testing.assert_frame_equal(expected.df.drop(columns=["pfad"]), view.result.df.drop(columns=["pfad"]))


def test_no_flight_in_the_filter_and_an_empty_database(model, tmp_path):
    model.state.set(year=2020)
    assert model.view().state == NO_MATCH
    empty = FlightDatabase(str(tmp_path / "empty.db"))
    statistics = StatisticsModel(FakeCache(empty.connection), FilterState(), lambda aircraft: LI_ION_13S)
    assert statistics.view().state == EMPTY_DATABASE
    empty.close()


def test_an_aircraft_without_battery_data_gets_a_hint(model):
    model.state.set(aircraft="Glider")
    view = model.view()
    assert view.state == NO_BATTERY_DATA and model.fake_cache.requested == []
    assert "Glider" in view.message


def test_a_failed_preparation_is_said(model):
    model.state.set(aircraft="Viper-Jet")
    model.fake_cache.failed.add("Viper-Jet")
    assert model.view().state == FAILED


def test_new_battery_settings_calculate_the_analysis_again(model):
    model.fake_cache.finish("Viper-Jet")
    model.state.set(aircraft="Viper-Jet")
    first = model.view().result
    model.params_for = lambda aircraft: ela.Params(chem="Li-Ion", cells=13, nominal_mah=8000)
    second = model.view()
    assert second.result is not first and second.params.nominal_mah == 8000


def test_filter_description_and_report_lines(model):
    set_language("de")
    assert filter_description(FlightFilter()) == ""
    assert filter_description(FlightFilter(aircraft="Jet", year=2026, month=6)) == "2026, Monat 06"
    assert filter_description(FlightFilter(date_from=date(2026, 5, 1))) == "01.05.2026 – …"
    assert filter_description(FlightFilter(year={2025, 2024}, month={7, 6})) == "2024, 2025, Monate 06, 07"
    assert filter_description(FlightFilter(year={2023, 2024, 2025}, month={1, 2, 3})) == "3 Jahre, 3 Monate"
    assert filter_description(FlightFilter(year=frozenset(), month=frozenset())) == "keine Jahre, keine Monate"
    assert filter_description(FlightFilter(aircraft={"Jet", "Glider"})) == ""      # aircraft are named elsewhere
    set_language("en")
    assert filter_description(FlightFilter(year={2024, 2025}, month={6, 7})) == "2024, 2025, months 06, 07"
    assert filter_description(FlightFilter(year={2022, 2023, 2024})) == "3 years"
    set_language("es")
    assert filter_description(FlightFilter(month={6, 7, 8})) == "3 meses"
    set_language("de")
    model.state.set(aircraft="Glider")
    lines = report_lines(model.view(), filter_text="2026")
    assert lines[0] == ("notice", EXPERIMENTAL_NOTICE) and lines[1] == ("info", "Filter: 2026")
    model.fake_cache.finish("Viper-Jet")
    model.state.set(aircraft="Viper-Jet")
    lines = report_lines(model.view(), battery_hint="hint")
    assert lines[0][0] == "notice" and lines[1] == ("bad", "hint") and ("h", "ÜBERSICHT") in lines
    for language in ("en", "es"):
        set_language(language)
        assert report_lines(model.view())[0][1] != EXPERIMENTAL_NOTICE
    set_language("de")
