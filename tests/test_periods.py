# -*- coding: utf-8 -*-
"""Filter by aircraft/year/month/date range and the shared filter state."""

from datetime import date

import pandas as pd
import pytest

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


def test_selections_take_single_values_and_collections():
    assert FlightFilter(aircraft="Glider").aircraft == frozenset({"Glider"})
    assert FlightFilter(year=2026).year == frozenset({2026})
    assert FlightFilter(month=[1, 5, 5]).month == frozenset({1, 5})
    assert FlightFilter(year=(2025, 2026)).year == frozenset({2025, 2026})
    assert FlightFilter().aircraft is None and FlightFilter(year=None).year is None
    assert FlightFilter(year=2026) == FlightFilter(year={2026}) == FlightFilter(year=frozenset([2026]))


def test_several_values_of_one_criterion_are_alternatives(flights):
    both_aircraft = FlightFilter(aircraft={"Viper", "Glider"})
    assert _durations(apply_filter(flights, both_aircraft)) == [100, 200, 300, 400, 500, 600]
    assert _durations(apply_filter(flights, FlightFilter(aircraft={"Viper", "Nobody"}))) == [100, 200, 300, 400]
    assert _durations(apply_filter(flights, FlightFilter(year={2025, 2026}))) == [100, 200, 300, 400, 500, 600]
    assert _durations(apply_filter(flights, FlightFilter(month={12, 1}))) == [100, 200]


def test_criteria_are_combined_with_and_and_year_and_month_separately(flights):
    # years {2025, 2026} and months {5, 12}: May and December of both years (not January)
    years_and_months = FlightFilter(year={2025, 2026}, month={5, 12})
    assert _durations(apply_filter(flights, years_and_months)) == [100, 300, 400, 500, 600]
    assert _durations(apply_filter(flights, FlightFilter(year={2025}, month={5, 12}))) == [100, 600]
    assert _durations(apply_filter(flights, FlightFilter(aircraft={"Viper", "Nobody"}, year={2026}))) == [200, 300, 400]
    with_dates = FlightFilter(aircraft={"Viper", "Glider"}, month={5}, date_from=date(2026, 5, 5))
    assert _durations(apply_filter(flights, with_dates)) == [400]


def test_an_empty_selection_matches_no_flight_without_error(flights):
    for empty in (FlightFilter(aircraft=frozenset()), FlightFilter(year=set()), FlightFilter(month=[])):
        assert empty.is_active and apply_filter(flights, empty).empty
        assert not filter_mask(flights, empty).any()
    assert apply_filter(flights, FlightFilter(aircraft=frozenset(), year={2026})).empty
    assert apply_filter(flights.iloc[0:0], FlightFilter(year=frozenset())).empty


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


def test_filter_state_stores_a_selection_of_everything_as_no_restriction():
    state, calls = FilterState(), []
    state.set_choices(["Glider", "Viper"], [2025, 2026])
    state.add_listener(lambda: calls.append(state.value))
    state.set(year={2025, 2026})                                    # every year: nothing is restricted
    assert state.value == FlightFilter() and calls == []
    state.set(year={2026})
    state.set(year=[2025, 2026])                                    # ticked back to every year
    assert state.value.year is None and len(calls) == 2
    state.set(month=set(range(1, 13)))                               # months are always 1..12
    assert state.value.month is None and len(calls) == 2
    state.set(aircraft={"Viper"}, month={6, 7})
    assert state.value == FlightFilter(aircraft="Viper", month={6, 7})
    state.set(aircraft={"Glider", "Viper", "Extra"})                 # a superset of the existing ones: everything
    assert state.value == FlightFilter(month={6, 7})


def test_filter_state_keeps_a_selection_while_the_choices_are_unknown():
    state = FilterState()                                           # no database loaded yet
    state.set(year={2025, 2026})
    assert state.value.year == frozenset({2025, 2026})
    state.set_choices(["Viper"], [2025, 2026])                      # now it is known: that is every year
    assert state.value.year is None


def test_filter_state_removes_vanished_values_from_a_selection():
    state = FilterState()
    state.set_choices(["Glider", "Viper", "Wing"], [2024, 2025, 2026])
    state.set(aircraft={"Glider", "Wing"}, year={2024, 2025})
    state.set_choices(["Glider", "Viper"], [2025, 2026])             # Wing and 2024 are gone
    assert state.value == FlightFilter(aircraft="Glider", year=2025)
    state.set_choices(["Viper"], [2026])                             # nothing of the selection is left: no limit
    assert state.value == FlightFilter()
    state.set_choices(["Viper", "Wing"], [2026, 2027])
    state.set(aircraft={"Viper"})
    state.set_choices(["Viper"], [2026, 2027])                       # Wing is gone: Viper is every aircraft now
    assert state.value.aircraft is None


def test_filter_state_new_values_stay_in_alle_but_not_in_a_narrowed_selection():
    state = FilterState()
    state.set_choices(["Viper"], [2025])
    state.set_choices(["Glider", "Viper"], [2025, 2026])             # after an import: "alle" stays "alle"
    assert state.value == FlightFilter()
    state.set(aircraft={"Viper"}, year={2025})
    state.set_choices(["Glider", "Viper", "Wing"], [2025, 2026, 2027])
    assert state.value == FlightFilter(aircraft="Viper", year=2025)   # a narrowed selection does not grow


def test_filter_state_keeps_an_empty_selection_and_reset_clears_everything():
    state, calls = FilterState(), []
    state.set_choices(["Glider", "Viper"], [2025, 2026])
    state.set(year=frozenset(), aircraft=frozenset())
    state.add_listener(lambda: calls.append(1))
    assert state.value.year == frozenset() and state.value.is_active
    state.set_choices(["Glider", "Viper"], [2025, 2026, 2027])       # the choices change, the empty selection stays
    assert state.value.year == frozenset() and state.value.aircraft == frozenset() and len(calls) == 1
    state.reset()
    assert state.value == FlightFilter() and len(calls) == 2


def test_listener_can_be_removed():
    state, calls = FilterState(), []
    listener = lambda: calls.append(1)
    state.add_listener(listener)
    state.remove_listener(listener)
    state.set(year=2026)
    assert calls == []
