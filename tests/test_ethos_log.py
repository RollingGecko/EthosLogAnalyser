# -*- coding: utf-8 -*-
"""Reading Ethos logs: encoding, column detection, time axis."""

from datetime import datetime

import numpy as np
import pandas as pd

from helpers import EXAMPLE_FILES
from ethosloganalyser.io.ethos_log import (CURR_KEYS, VOLT_KEYS, _file_datetime, _find_col, _switch_columns,
                                           _time_seconds, _to_num, read_log)


def test_example_logs_present():
    assert len(EXAMPLE_FILES) == 3


def test_special_characters_in_column_names_are_fixed():
    df = read_log(EXAMPLE_FILES[0])
    assert "R.angle(°)" in df.columns
    assert "LI-außen" in df.columns
    assert not any("Â" in c or "›" in c for c in df.columns)


def test_battery_columns_are_chosen_over_receiver_columns():
    df = read_log(EXAMPLE_FILES[0])
    assert _find_col(df.columns, VOLT_KEYS) == "VFAS(V)"
    assert _find_col(df.columns, CURR_KEYS) == "Current(A)"          # not RxCurrent(A)


def test_column_can_be_set_manually():
    df = read_log(EXAMPLE_FILES[0])
    assert _find_col(df.columns, VOLT_KEYS, override="rxbatt1") == "RxBatt1(V)"
    assert _find_col(df.columns, VOLT_KEYS, override="doesnotexist") is None


def test_time_axis_starts_at_zero_and_increases():
    t = _time_seconds(read_log(EXAMPLE_FILES[0]))
    assert t[0] == 0
    assert np.all(np.diff(t) >= 0)
    assert t[-1] > 400


def test_time_axis_across_midnight():
    df = pd.DataFrame({"Time": ["23:59:58.000", "23:59:59.500", "00:00:01.000"]})
    assert list(_time_seconds(df)) == [0.0, 1.5, 3.0]


def test_decimal_comma_is_parsed():
    assert list(_to_num(pd.Series(["3,5", "4.25", "x"]))[:2]) == [3.5, 4.25]
    assert np.isnan(_to_num(pd.Series(["x"]))[0])


def test_date_from_file_name():
    assert _file_datetime("Viper-Jet-2026-09-13-13-56-38.csv") == datetime(2026, 9, 13, 13, 56, 38)


def test_switches_are_detected_but_not_sticks():
    names = [n for n, _ in _switch_columns(read_log(EXAMPLE_FILES[0]))]
    assert "LS1" in names
    for stick in ("QR", "HR", "SR", "Gas"):
        assert stick not in names
