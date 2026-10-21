# -*- coding: utf-8 -*-
"""Analysis across all flights: numbering, cell count, state of charge, timer, assessment."""

import numpy as np
import pandas as pd

from helpers import example_result
from ethosloganalyser.analysis.evaluate import evaluate
from ethosloganalyser.config import Params, soc_pct
from ethosloganalyser.utils import _ranges


def test_three_flights_in_chronological_order():
    df = example_result().df
    assert list(df["Flug"]) == [1, 2, 3]
    assert df["datum"].is_monotonic_increasing


def test_cell_count_detected_automatically():
    assert example_result().meta["cells"] == 13


def test_state_of_charge_and_timer_are_computed():
    res = example_result()
    df = res.df
    assert df["SoC_ende_pct"].notna().all()
    assert df["Timer_s"].notna().all()
    assert 200 < res.meta["timer_s"] < 600
    assert (df["Timer_s"] > 0).all()


def test_too_small_nominal_capacity_flags_implausible_state_of_charge():
    res = example_result(nominal_mah=3000.0)
    flags = res.meta["flags"]
    assert flags.get("Ladezustand unplausibel") == {1, 2, 3}
    assert "Tiefentladung" in flags


def test_no_outlier_detection_below_six_flights():
    texts = [txt for _, txt in example_result().meta["warnings"]]
    assert not any("auffälliger Wert" in txt for txt in texts)


def test_internal_resistance_outlier_is_detected():
    n = 10
    df = pd.DataFrame({
        "Flug": np.arange(1, n + 1), "datum": pd.date_range("2026-05-01", periods=n),
        "Ri_Zelle_mOhm": [4.0, 4.05, 3.98, 4.02, 4.01, 6.5, 4.03, 4.0, 4.04, 3.99],
    })
    for col in ["SoC_Abw_pct", "Reserve_Zelle_V", "SoC_ende_Q_pct", "U_ende_Zelle_V", "Sensor_Abw_pct",
                "RxSp_ohne", "U_ref_Zelle_V", "Kap_gesch_mAh", "P_ref_W", "RSSI_min", "VFR_min",
                "RxBatt_min_V", "RxStrom_max_A"]:
        df[col] = np.nan
    df["U_min_Zelle_V"] = 3.5
    df["U_ende_Quelle"] = "–"
    meta = dict(cap_src="Nennkapazität", cap_ref=5000.0)
    warns, flags = evaluate(df, Params(), meta)
    assert flags.get("Innenwiderstand") == {6}


def test_state_of_charge_curves():
    assert soc_pct(4.20, "LiPo") == 100
    assert soc_pct(3.27, "LiPo") == 0
    assert soc_pct(4.35, "LiHV") == 100
    assert 40 < soc_pct(3.84, "LiPo") < 60


def test_flight_numbers_as_ranges():
    assert _ranges([1, 2, 3, 5, 7, 8]) == "1-3, 5, 7-8"
    assert _ranges([4]) == "4"
