# -*- coding: utf-8 -*-
"""The logbook flight table from the database: numbering per aircraft, the flight decision, battery validity,
the manual flight switch and the model behind the logbook page."""

import json
import shutil
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from helpers import EXAMPLE_FILES, EXAMPLES, analyse_logs, ela, write_glider_log
from ethosloganalyser.analysis.logbook import logbook
from ethosloganalyser.analysis.periods import FlightFilter
from ethosloganalyser.config import Params
from ethosloganalyser.db import FlightDatabase, flight_store, import_paths
from ethosloganalyser.db.logbook_table import (battery_valid, build_logbook_table, empty_logbook_table,
                                               manual_value_after_switch, metric_columns)
from ethosloganalyser.gui.logbook_flight_list import CHECKED, DUPLICATE_SYMBOL, UNCHECKED, list_row
from ethosloganalyser.gui.logbook_model import LogbookModel

LI_ION_13S = Params(cells=13, chem="Li-Ion", nominal_mah=9000)


def _metrics(drawn=1000.0, mean_a=20.0, max_a=40.0, min_v=44.0, start_v=54.6):
    return json.dumps({"entnommen_mAh": drawn, "I_mittel_A": mean_a, "I_max_A": max_a, "U_min_V": min_v,
                       "U_ruhe_start_V": start_v, "U_start_V": start_v - 0.2, "dauer_s": 500.0})


def _rows(*entries):
    """Rows as flight_store.logbook_rows gives them; entries are dicts that override the defaults."""
    defaults = dict(aircraft="Viper", start_time="2026-05-01T10:00:00", duration_s=500.0, log_duration_s=900.0,
                    is_flight=1, is_flight_manual=None, possible_duplicate=0, metrics=_metrics())
    rows = []
    for number, entry in enumerate(entries, start=1):
        row = {**defaults, **entry}
        row.setdefault("log_id", number)
        row.setdefault("original_name", f"{row['aircraft']}-{row['start_time']}.csv")
        rows.append(row)
    return pd.DataFrame(rows)


def _table(*entries, params=LI_ION_13S):
    return build_logbook_table(_rows(*entries), lambda aircraft: params)


# ---------------- numbering and the flight decision ----------------
def test_flights_are_numbered_per_aircraft_by_start_time():
    table = _table(dict(aircraft="Viper", start_time="2026-05-02T10:00:00"),
                   dict(aircraft="Glider", start_time="2026-05-01T09:00:00", metrics=None),
                   dict(aircraft="Viper", start_time="2026-05-01T10:00:00"),
                   dict(aircraft="Glider", start_time="2026-06-01T09:00:00", metrics=None))
    assert list(table["aircraft"]) == ["Glider", "Viper", "Viper", "Glider"]           # oldest first
    assert list(table["Flug"]) == [1, 1, 2, 2]


def test_logs_that_are_not_flights_have_no_number_and_do_not_shift_the_others():
    table = _table(dict(start_time="2026-05-01T10:00:00"),
                   dict(start_time="2026-05-02T10:00:00", is_flight=0, metrics=None),
                   dict(start_time="2026-05-03T10:00:00"))
    assert table["Flug"].isna().tolist() == [False, True, False]
    assert list(table["Flug"].dropna()) == [1, 2]
    assert table["is_flight"].tolist() == [True, False, True]


def test_a_decision_by_hand_wins_over_the_detection():
    table = _table(dict(start_time="2026-05-01T10:00:00", is_flight=1, is_flight_manual=0),
                   dict(start_time="2026-05-02T10:00:00", is_flight=0, is_flight_manual=1, metrics=None),
                   dict(start_time="2026-05-03T10:00:00", is_flight=1, is_flight_manual=np.nan))
    assert table["is_flight"].tolist() == [False, True, True]
    assert table["auto_flight"].tolist() == [True, False, True]          # the detection stays visible
    assert list(table["Flug"].dropna()) == [1, 2]


def test_switching_goes_by_the_automatic_result_and_a_second_switch_undoes_it():
    assert manual_value_after_switch(is_flight=True, auto_flight=True) == 0          # flight -> no flight
    assert manual_value_after_switch(is_flight=False, auto_flight=False) == 1        # no flight -> flight
    assert manual_value_after_switch(is_flight=False, auto_flight=True) is None      # back to the detection
    assert manual_value_after_switch(is_flight=True, auto_flight=False) is None


def test_duration_falls_back_to_the_log_duration_and_missing_data_stays_empty():
    table = _table(dict(duration_s=None, log_duration_s=321.0, metrics=None),
                   dict(start_time="2026-05-02T10:00:00", duration_s=None, log_duration_s=None, metrics=None))
    assert table["dauer_s"].iloc[0] == 321.0 and np.isnan(table["dauer_s"].iloc[1])
    assert table["entnommen_mAh"].isna().all() and not table["Akku_gueltig"].any()


def test_empty_database_gives_an_empty_typed_table():
    table = build_logbook_table(pd.DataFrame(), lambda aircraft: LI_ION_13S)
    assert table.empty and list(table.columns) == list(empty_logbook_table().columns)
    assert pd.api.types.is_datetime64_any_dtype(table["datum"])
    assert logbook(table).n_counted == 0


def test_the_missing_metrics_text_may_be_none_or_nan():
    columns, has_metrics = metric_columns([_metrics(drawn=123.0), None, float("nan")])
    assert has_metrics.tolist() == [True, False, False]
    assert columns["entnommen_mAh"].tolist()[0] == 123.0 and columns["entnommen_mAh"].isna().tolist() == [False, True, True]


# ---------------- battery validity ----------------
def test_stuck_current_and_voltage_dropout_make_the_battery_values_invalid():
    table = _table(dict(start_time="2026-05-01T10:00:00"),
                   dict(start_time="2026-05-02T10:00:00", metrics=_metrics(mean_a=39.5, max_a=40.0)),      # stuck sensor
                   dict(start_time="2026-05-03T10:00:00", metrics=_metrics(min_v=10.0)))                     # 0.77 V/cell
    assert table["Akku_gueltig"].tolist() == [True, False, False]
    book = logbook(table)
    assert book.n_counted == 3 and book.n_mah == 1 and book.mah_total == 1000


def test_battery_validity_uses_the_settings_of_each_aircraft():
    # the lowest voltage of 15 V is a dropout with 13 cells (1.15 V per cell, limit 1.4 V) but normal with 6 cells
    rows = _rows(dict(aircraft="A", metrics=_metrics(min_v=15.0)),
                 dict(aircraft="B", start_time="2026-05-02T10:00:00", metrics=_metrics(min_v=15.0)))
    settings = {"A": Params(cells=13, chem="Li-Ion"), "B": Params(cells=6, chem="Li-Ion")}
    table = build_logbook_table(rows, lambda aircraft: settings[aircraft])
    assert table.set_index("aircraft")["Akku_gueltig"].to_dict() == {"A": False, "B": True}


def test_the_cell_count_is_estimated_from_the_start_voltage_when_not_set():
    metrics = pd.DataFrame({"U_ruhe_start_V": [25.2, 25.0], "U_start_V": [25.0, 24.9], "U_min_V": [20.0, 8.0],
                            "I_mittel_A": [10.0, 10.0], "I_max_A": [30.0, 30.0]})
    # 25.2 V / (4.2 V + 0.05 V) -> 6 cells: 8 V is 1.33 V per cell, below half of the 3.0 V load limit
    assert battery_valid(metrics, Params(cells=0, chem="LiPo")).tolist() == [True, False]
    no_voltage = metrics.assign(U_ruhe_start_V=np.nan, U_start_V=np.nan)
    assert battery_valid(no_voltage, Params(cells=0, chem="LiPo")).tolist() == [True, True]      # only the current counts


# ---------------- against the folder analysis and the real database ----------------
@pytest.fixture(scope="module")
def database(tmp_path_factory):
    folder = tmp_path_factory.mktemp("logbook_flights")
    write_glider_log(folder, "Glider-2030-02-01-12-00-00.csv", airborne_s=600, start="2030-02-01 12:00:00")
    db = FlightDatabase(str(folder / "flights.db"))
    import_paths(db, [str(EXAMPLES), str(folder)], ela.Params())
    yield db
    db.close()


def test_the_logbook_of_the_database_equals_the_analysis_of_the_files(database):
    folder = analyse_logs(EXAMPLE_FILES, LI_ION_13S)
    table = build_logbook_table(flight_store.logbook_rows(database.connection), lambda aircraft: LI_ION_13S)
    flights = table[table["is_flight"] & (table["aircraft"] == "Viper-Jet")]
    expected, actual = logbook(folder.df), logbook(flights)
    assert actual.n_counted == expected.n_counted == 3 and actual.flight_days == expected.flight_days
    assert actual.total_s == expected.total_s and actual.mah_total == expected.mah_total
    assert actual.longest == {**expected.longest, "aircraft": "Viper-Jet"}
    assert actual.shortest == {**expected.shortest, "aircraft": "Viper-Jet"}
    assert list(flights["Akku_gueltig"]) == list(folder.df["Akku_gueltig"])
    assert list(flights["Flug"]) == list(folder.df["Flug"]) == [1, 2, 3]
    pd.testing.assert_frame_equal(actual.per_month, expected.per_month)
    pd.testing.assert_frame_equal(actual.per_year, expected.per_year)


def test_a_flight_without_battery_data_counts_without_charge(database):
    table = build_logbook_table(flight_store.logbook_rows(database.connection), lambda aircraft: LI_ION_13S)
    glider = table[table["aircraft"] == "Glider"].iloc[0]
    assert glider["is_flight"] and glider["Flug"] == 1 and glider["dauer_s"] > 0
    assert np.isnan(glider["entnommen_mAh"]) and not glider["Akku_gueltig"]
    assert logbook(table[table["is_flight"]]).n_counted == 4
    assert logbook(table[table["is_flight"]]).n_mah == 3


def test_switching_a_log_by_hand_is_stored_and_the_detection_is_kept(database, tmp_path):
    path = tmp_path / "copy.db"
    database.save_as(str(path))
    copy = FlightDatabase(str(path))
    try:
        rows = flight_store.logbook_rows(copy.connection)
        log_id = int(rows["log_id"].iloc[0])
        flight_store.set_flight_manual(copy.connection, log_id, 0)
        table = build_logbook_table(flight_store.logbook_rows(copy.connection), lambda aircraft: LI_ION_13S)
        row = table[table["log_id"] == log_id].iloc[0]
        assert not row["is_flight"] and row["auto_flight"]
        assert copy.stats().flight_count == 3                           # the database counts it the same way
        flight_store.set_flight_manual(copy.connection, log_id, None)   # back to the detection
        table = build_logbook_table(flight_store.logbook_rows(copy.connection), lambda aircraft: LI_ION_13S)
        assert table[table["log_id"] == log_id].iloc[0]["is_flight"] and copy.stats().flight_count == 4
    finally:
        copy.close()


def test_a_log_with_the_same_aircraft_and_start_time_is_marked_as_possible_duplicate(tmp_path):
    folder = tmp_path / "logs"
    folder.mkdir()
    first = sorted(EXAMPLES.glob("*.csv"))[0]
    shutil.copy(first, folder / first.name)
    changed = folder / "other" / first.name
    changed.parent.mkdir()
    changed.write_bytes(first.read_bytes() + b"\n")                 # other content, same aircraft and start
    database = FlightDatabase(str(tmp_path / "flights.db"))
    try:
        import_paths(database, [str(folder)], LI_ION_13S)
        table = build_logbook_table(flight_store.logbook_rows(database.connection), lambda aircraft: LI_ION_13S)
        assert table["possible_duplicate"].tolist().count(True) == 1
        marked = table[table["possible_duplicate"]].iloc[0]
        _raw, shown, _tags = list_row(marked.to_dict())
        assert DUPLICATE_SYMBOL in shown
    finally:
        database.close()


# ---------------- the rows of the flight list ----------------
def test_list_rows_show_the_flight_switch_the_duplicate_symbol_and_grey_out_non_flights():
    table = _table(dict(start_time="2026-05-01T10:00:00", possible_duplicate=1),
                   dict(start_time="2026-05-02T10:00:00", is_flight=0, metrics=None))
    flight, non_flight = (list_row(row) for row in table.to_dict("records"))
    assert flight[1][0] == 1 and flight[1][6] == CHECKED and flight[1][7] == DUPLICATE_SYMBOL and flight[2] == ()
    assert non_flight[1][0] == "–" and non_flight[1][6] == UNCHECKED and non_flight[1][7] == "" and non_flight[2]
    assert non_flight[0][0] is None and non_flight[0][-1] == 2          # sorting: no number last; log id kept


# ---------------- the model behind the page ----------------
class FakeController:
    """What LogbookModel needs of the DatabaseController."""

    def __init__(self, database):
        self.database, self.generation = SimpleNamespace(connection=database.connection), 1
        self.annotations_generation = 1


@pytest.fixture
def model(database, tmp_path):
    path = tmp_path / "model.db"
    database.save_as(str(path))
    copy = FlightDatabase(str(path))
    settings = {"params": LI_ION_13S}
    controller = FakeController(copy)
    logbook_model = LogbookModel(controller, lambda aircraft: settings["params"])
    logbook_model.controller, logbook_model.settings = controller, settings
    yield logbook_model
    copy.close()


def test_the_model_reads_the_database_only_when_something_changed(model):
    assert model.refresh() and not model.refresh()
    model.controller.generation += 1                       # database changed
    assert model.refresh() and not model.refresh()
    model.settings["params"] = Params(cells=6, chem="Li-Ion")            # battery settings changed
    assert model.refresh() and not model.refresh()


def test_the_view_follows_filter_selection_and_non_flights(model):
    model.refresh()
    view = model.view(FlightFilter())
    assert view.n_flights == view.n_total == 4 and view.n_aircraft == 2 and len(view.listed) == 4
    assert model.aircraft_names() == ["Glider", "Viper-Jet"] and model.years() == [2026, 2030]
    viper = model.view(FlightFilter(aircraft="Viper-Jet"))
    assert viper.n_flights == 3 and viper.book.n_counted == 3 and viper.n_aircraft == 1 and viper.n_total == 4
    assert model.view(FlightFilter(year=2030)).n_flights == 1

    assert len(model.listed(FlightFilter())) == 4          # the list always shows all flights of the filter
    assert len(model.listed(FlightFilter(year=2026))) == 3 and len(model.listed(FlightFilter(aircraft="Glider"))) == 1


def test_switching_a_flight_removes_it_from_the_totals_and_shows_it_as_a_non_flight(model):
    model.refresh()
    log_id = int(model.table[model.table["aircraft"] == "Glider"]["log_id"].iloc[0])
    assert model.switch_flight(log_id)
    model.controller.generation += 1
    model.refresh()
    assert model.view(FlightFilter()).n_flights == 3 and len(model.view(FlightFilter()).listed) == 3
    model.show_non_flights = True
    view = model.view(FlightFilter())
    assert view.n_flights == 3 and len(view.listed) == 4 and not view.listed["is_flight"].all()
    assert model.summary().n_non_flights == 1 + model.summary().n_flights * 0
    assert model.switch_flight(log_id)                     # the same switch undoes it
    model.controller.generation += 1
    model.refresh()
    assert model.view(FlightFilter()).n_flights == 4
    assert not model.switch_flight(123456)                 # unknown log


def test_the_summary_of_the_database(model):
    model.refresh()
    summary = model.summary()
    assert (summary.n_flights, summary.n_non_flights, summary.n_aircraft) == (4, 0, 2)
    assert summary.first < summary.last and summary.last.year == 2030
    empty = LogbookModel(SimpleNamespace(database=None, generation=0, annotations_generation=0),
                         lambda aircraft: LI_ION_13S)
    assert empty.refresh() and empty.summary().n_flights == 0 and empty.summary().first is None
    assert empty.view(FlightFilter(year=2026)).n_flights == 0


def test_notes_and_anomalies_show_in_the_list_and_filter_it(model):
    from ethosloganalyser.db import annotations
    from ethosloganalyser.gui.logbook_flight_list import NOTE_SYMBOL, SEVERITY_SYMBOLS
    from ethosloganalyser.gui.logbook_model import ANNOTATIONS_CHANGED, FLIGHTS_CHANGED

    assert model.refresh() == FLIGHTS_CHANGED
    connection = model.controller.database.connection
    first, second = (int(log_id) for log_id in model.table["log_id"].iloc[:2])
    annotations.set_note(connection, first, "fuel smell")
    annotations.add_manual_anomaly(connection, second, "canopy loose", "critical")
    model.controller.annotations_generation += 1
    assert model.refresh() == ANNOTATIONS_CHANGED and model.refresh() is None
    rows = {int(row["log_id"]): list_row(row) for row in model.table.to_dict("records")}
    assert rows[first][1][7] == NOTE_SYMBOL and rows[second][1][7] == SEVERITY_SYMBOLS[3]
    assert rows[second][0][7] > rows[first][0][7]          # sorting: open anomalies before notes
    model.only_annotated = True
    assert sorted(model.listed(FlightFilter())["log_id"]) == sorted([first, second])
    assert model.hint_lines(second) == [("critical", "canopy loose")]
    assert model.hint_lines(first) == [("note", "fuel smell")]
