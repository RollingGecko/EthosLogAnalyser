# -*- coding: utf-8 -*-
"""Filter by aircraft/year/month/date range, the grouping tree of the logbook and the shared filter state."""

from datetime import date

import pandas as pd
import pytest

from ethosloganalyser.analysis.logbook_groups import (AIRCRAFT, GROUP_BY_AIRCRAFT, GROUP_BY_TIME, MONTH, YEAR,
                                                      all_selectors, build_groups, select_flights)
from ethosloganalyser.analysis.periods import FlightFilter, apply_filter, aircraft_in, filter_mask, years_in
from ethosloganalyser.gui.flight_filter import FilterState


@pytest.fixture
def flights():
    """Two aircraft over two years; the numbers are chosen so that every grouping has a different sum."""
    rows = [
        ("Viper", "2025-12-31 23:30", 100), ("Viper", "2026-01-01 00:15", 200), ("Viper", "2026-05-04 13:00", 300),
        ("Viper", "2026-05-18 09:00", 400), ("Glider", "2026-05-04 15:00", 500), ("Glider", "2025-05-04 15:00", 600),
    ]
    return pd.DataFrame({"aircraft": [r[0] for r in rows], "datum": pd.to_datetime([r[1] for r in rows]),
                         "dauer_s": [r[2] for r in rows]})


def _durations(table):
    return sorted(table["dauer_s"])


# ---------------- filter ----------------
def test_no_filter_keeps_everything(flights):
    assert not FlightFilter().is_active
    assert apply_filter(flights, FlightFilter()) is flights


def test_filter_by_aircraft_year_and_month(flights):
    assert _durations(apply_filter(flights, FlightFilter(aircraft="Glider"))) == [500, 600]
    assert _durations(apply_filter(flights, FlightFilter(year=2026))) == [200, 300, 400, 500]
    assert _durations(apply_filter(flights, FlightFilter(year=2026, month=5))) == [300, 400, 500]
    assert _durations(apply_filter(flights, FlightFilter(month=5))) == [300, 400, 500, 600]    # May of every year
    assert _durations(apply_filter(flights, FlightFilter(aircraft="Viper", year=2026, month=5))) == [300, 400]
    assert apply_filter(flights, FlightFilter(aircraft="Nobody")).empty


def test_date_range_includes_both_end_days(flights):
    only_may_4 = FlightFilter(date_from=date(2026, 5, 4), date_to=date(2026, 5, 4))
    assert _durations(apply_filter(flights, only_may_4)) == [300, 500]           # flights at 13:00 and 15:00
    assert _durations(apply_filter(flights, FlightFilter(date_from=date(2026, 1, 1)))) == [200, 300, 400, 500]
    assert _durations(apply_filter(flights, FlightFilter(date_to=date(2025, 12, 31)))) == [100, 600]
    combined = FlightFilter(aircraft="Viper", date_from=date(2026, 1, 1), date_to=date(2026, 5, 4))
    assert _durations(apply_filter(flights, combined)) == [200, 300]
    assert filter_mask(flights, only_may_4).sum() == 2


def test_choices_for_the_filter(flights):
    assert years_in(flights) == [2025, 2026]
    assert aircraft_in(flights) == ["Glider", "Viper"]
    assert years_in(flights.iloc[0:0]) == [] and aircraft_in(flights.iloc[0:0]) == []


# ---------------- grouping tree ----------------
def test_group_by_time_is_year_month_aircraft(flights):
    tree = build_groups(flights, GROUP_BY_TIME)
    assert [(node.level, node.value, node.n_flights, node.duration_s) for node in tree] == [
        (YEAR, 2025, 2, 700), (YEAR, 2026, 4, 1400)]
    year_2026 = tree[1]
    assert [(child.level, child.value, child.n_flights) for child in year_2026.children] == [(MONTH, 1, 1), (MONTH, 5, 3)]
    may = year_2026.children[1]
    assert [(child.level, child.value, child.n_flights, child.duration_s) for child in may.children] == [
        (AIRCRAFT, "Glider", 1, 500), (AIRCRAFT, "Viper", 2, 700)]
    assert may.children[1].selector == {YEAR: 2026, MONTH: 5, AIRCRAFT: "Viper"}


def test_group_by_aircraft_is_aircraft_year_month(flights):
    tree = build_groups(flights, GROUP_BY_AIRCRAFT)
    assert [(node.value, node.n_flights, node.duration_s) for node in tree] == [("Glider", 2, 1100), ("Viper", 4, 1000)]
    viper = tree[1]
    assert [(child.level, child.value, child.n_flights) for child in viper.children] == [(YEAR, 2025, 1), (YEAR, 2026, 3)]
    assert [(m.value, m.n_flights) for m in viper.children[1].children] == [(1, 1), (5, 2)]
    assert viper.children[1].children[1].selector == {AIRCRAFT: "Viper", YEAR: 2026, MONTH: 5}


def test_every_grouping_adds_up_to_all_flights(flights):
    for group_by in (GROUP_BY_TIME, GROUP_BY_AIRCRAFT):
        tree = build_groups(flights, group_by)
        assert sum(node.n_flights for node in tree) == len(flights)
        assert sum(node.duration_s for node in tree) == flights["dauer_s"].sum()
        for node in tree:                        # a parent is the sum of its children
            assert node.n_flights == sum(child.n_flights for child in node.children)


def test_selector_selects_the_flights_of_a_row(flights):
    assert _durations(select_flights(flights, {YEAR: 2026, MONTH: 5, AIRCRAFT: "Viper"})) == [300, 400]
    assert _durations(select_flights(flights, {AIRCRAFT: "Glider"})) == [500, 600]
    assert select_flights(flights, None) is flights
    for group_by in (GROUP_BY_TIME, GROUP_BY_AIRCRAFT):                 # a row counts exactly its flights
        for node in build_groups(flights, group_by) + [c for n in build_groups(flights, group_by) for c in n.children]:
            assert len(select_flights(flights, node.selector)) == node.n_flights
    assert len(all_selectors(build_groups(flights, GROUP_BY_TIME))) == 2 + 4 + 5     # years, months, aircraft


def test_empty_table_has_no_groups(flights):
    assert build_groups(flights.iloc[0:0], GROUP_BY_TIME) == []


def test_missing_duration_counts_as_a_flight_without_time(flights):
    flights.loc[0, "dauer_s"] = float("nan")
    year_2025 = build_groups(flights, GROUP_BY_TIME)[0]
    assert year_2025.n_flights == 2 and year_2025.duration_s == 600


# ---------------- shared filter state ----------------
def test_filter_state_tells_listeners_only_about_real_changes():
    state, calls = FilterState(), []
    state.add_listener(lambda: calls.append(state.value))
    state.set(year=2026)
    state.set(year=2026)                         # same value: no message
    state.set(aircraft="Viper", month=5)
    assert calls == [FlightFilter(year=2026), FlightFilter(aircraft="Viper", year=2026, month=5)]
    state.reset()
    assert state.value == FlightFilter() and len(calls) == 3
    state.reset()
    assert len(calls) == 3


def test_filter_state_drops_choices_that_no_longer_exist():
    state = FilterState()
    state.set_choices(["Glider", "Viper"], [2025, 2026])
    state.set(aircraft="Viper", year=2025, month=3)
    calls = []
    state.add_listener(lambda: calls.append(1))
    state.set_choices(["Glider", "Viper"], [2025, 2026])             # nothing changed
    assert calls == []
    state.set_choices(["Glider"], [2026])                          # Viper and 2025 are gone
    assert state.value == FlightFilter(month=3) and len(calls) == 1
    assert state.aircraft_choices == ["Glider"] and state.year_choices == [2026]


def test_listener_can_be_removed():
    state, calls = FilterState(), []
    listener = lambda: calls.append(1)
    state.add_listener(listener)
    state.remove_listener(listener)
    state.set(year=2026)
    assert calls == []
