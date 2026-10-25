# -*- coding: utf-8 -*-
"""Logbook totals (analysis/logbook.py) on synthetic flight tables and on the example logs."""

import numpy as np
import pandas as pd

import helpers
from ethosloganalyser import Params, analyse_folder
from ethosloganalyser.analysis.logbook import logbook
from ethosloganalyser.gui.common import sort_key


def _table(rows, valid=None):
    df = pd.DataFrame(rows, columns=["datum", "dauer_s", "entnommen_mAh"])
    df["datum"] = pd.to_datetime(df["datum"])
    df.insert(0, "Flug", np.arange(1, len(df) + 1))
    df["Akku_gueltig"] = True if valid is None else valid
    return df


def test_totals_over_new_year_and_several_flights_per_day():
    df = _table([
        ("2025-12-31 10:00", 300, 1000),
        ("2025-12-31 11:00", 420, 1500),          # second flight on the same day
        ("2026-01-01 09:30", 360, 1200),          # new year
        ("2026-01-15 12:00", 600, 2000),
        ("2026-02-03 08:00", 240, 900),
    ])
    lb = logbook(df)
    assert lb.n_flights == lb.n_counted == 5 and lb.n_missing == 0
    assert lb.total_s == 1920
    assert lb.flight_days == 4
    assert lb.longest["Flug"] == 4 and lb.longest["dauer_s"] == 600
    assert lb.shortest["Flug"] == 5 and lb.shortest["dauer_s"] == 240
    assert lb.mah_total == 6600 and lb.n_mah == 5
    assert lb.first == pd.Timestamp("2025-12-31 10:00") and lb.last == pd.Timestamp("2026-02-03 08:00")
    y = lb.per_year
    assert list(y.index) == [2025, 2026]
    assert list(y["Fluege"]) == [2, 3] and list(y["dauer_s"]) == [720, 1200] and list(y["Flugtage"]) == [1, 3]
    assert list(y["entnommen_mAh"]) == [2500, 4100]
    m = lb.per_month
    assert list(m.index) == [(2025, 12), (2026, 1), (2026, 2)]
    assert list(m["Fluege"]) == [2, 2, 1] and list(m["Flugtage"]) == [1, 2, 1]
    # the totals per year and per month add up to the overall totals
    assert y["Fluege"].sum() == m["Fluege"].sum() == lb.n_counted
    assert y["dauer_s"].sum() == m["dauer_s"].sum() == lb.total_s


def test_missing_date_or_duration_is_left_out_and_counted():
    df = _table([
        ("2026-05-01 10:00", 300, 1000),
        (None, 400, 1100),                         # no date
        ("2026-05-01 12:00", np.nan, 1200),        # no duration
        ("2026-05-02 12:00", 500, np.nan),         # no drawn charge: counted, but not in the mAh total
    ])
    lb = logbook(df)
    assert lb.n_flights == 4 and lb.n_counted == 2 and lb.n_missing == 2
    assert lb.total_s == 800 and lb.flight_days == 2
    assert lb.mah_total == 1000 and lb.n_mah == 1
    assert len(lb.flights) == 4                      # the flight list shows all flights
    assert lb.per_month.loc[(2026, 5), "entnommen_mAh"] == 1000


def test_invalid_battery_values_do_not_count_in_the_charge():
    df = _table([("2026-05-01 10:00", 300, 1000), ("2026-05-01 11:00", 300, 99999)], valid=[True, False])
    lb = logbook(df)
    assert lb.n_counted == 2 and lb.total_s == 600   # the flight itself counts
    assert lb.mah_total == 1000 and lb.n_mah == 1   # same rule as "total drawn" in the summary


def test_empty_and_only_missing():
    for df in (pd.DataFrame(), None, _table([(None, np.nan, np.nan)])):
        lb = logbook(df)
        assert lb.n_counted == 0 and lb.total_s == 0 and lb.flight_days == 0 and lb.longest == {}
        assert lb.per_year.empty and lb.per_month.empty


def test_logbook_of_the_example_logs():
    res = analyse_folder(str(helpers.EXAMPLES), Params(cells=13, chem="Li-Ion", nominal_mah=9000))
    lb = logbook(res.df)
    assert lb.n_counted == len(res.df) == 3
    assert lb.total_s == res.df["dauer_s"].sum()
    valid = res.df[res.df["Akku_gueltig"]]
    assert np.isclose(lb.mah_total, valid["entnommen_mAh"].sum())       # = "total drawn" of the summary


def test_sort_key_puts_missing_values_last():
    vals = [3.0, None, 1.0, np.nan, 2.0]
    ok = sorted([v for v in vals if not sort_key(v)[0]])
    assert ok == [1.0, 2.0, 3.0]
    assert sort_key(None)[0] and sort_key(np.nan)[0] and not sort_key(pd.Timestamp("2026-01-01"))[0]
