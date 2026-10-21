# -*- coding: utf-8 -*-
"""Einlesen der Ethos-Logs: Encoding, Spaltenerkennung, Zeitachse."""

from datetime import datetime

import numpy as np
import pandas as pd

from helpers import EXAMPLE_FILES
from ethosloganalyser.io.ethos_log import (CURR_KEYS, VOLT_KEYS, _file_datetime, _find_col, _switch_columns,
                                           _time_seconds, _to_num, read_log)


def test_beispiel_logs_vorhanden():
    assert len(EXAMPLE_FILES) == 3


def test_sonderzeichen_in_spaltennamen_werden_lesbar():
    df = read_log(EXAMPLE_FILES[0])
    assert "R.angle(°)" in df.columns
    assert "LI-außen" in df.columns
    assert not any("Â" in c or "›" in c for c in df.columns)


def test_akkuspalten_statt_empfaengerspalten():
    df = read_log(EXAMPLE_FILES[0])
    assert _find_col(df.columns, VOLT_KEYS) == "VFAS(V)"
    assert _find_col(df.columns, CURR_KEYS) == "Current(A)"          # nicht RxCurrent(A)


def test_spalte_manuell_vorgeben():
    df = read_log(EXAMPLE_FILES[0])
    assert _find_col(df.columns, VOLT_KEYS, override="rxbatt1") == "RxBatt1(V)"
    assert _find_col(df.columns, VOLT_KEYS, override="gibtsnicht") is None


def test_zeitachse_beginnt_bei_null_und_steigt():
    t = _time_seconds(read_log(EXAMPLE_FILES[0]))
    assert t[0] == 0
    assert np.all(np.diff(t) >= 0)
    assert t[-1] > 400


def test_zeitachse_ueber_mitternacht():
    df = pd.DataFrame({"Time": ["23:59:58.000", "23:59:59.500", "00:00:01.000"]})
    assert list(_time_seconds(df)) == [0.0, 1.5, 3.0]


def test_dezimalkomma_wird_gelesen():
    assert list(_to_num(pd.Series(["3,5", "4.25", "x"]))[:2]) == [3.5, 4.25]
    assert np.isnan(_to_num(pd.Series(["x"]))[0])


def test_datum_aus_dateiname():
    assert _file_datetime("Viper-Jet-2026-09-13-13-56-38.csv") == datetime(2026, 9, 13, 13, 56, 38)


def test_schalter_werden_erkannt_knueppel_nicht():
    names = [n for n, _ in _switch_columns(read_log(EXAMPLE_FILES[0]))]
    assert "LS1" in names
    for stick in ("QR", "HR", "SR", "Gas"):
        assert stick not in names
