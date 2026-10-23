# -*- coding: utf-8 -*-
"""Measurement-error detection, the robust ageing model (SoH, trend, forecast) and the period filter."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from helpers import tmpdir, write_ethos_csv
import ethosloganalyser as ela
from ethosloganalyser.analysis.ageing import ageing_model, battery_mix, forecast
from ethosloganalyser.analysis.fleet import in_period, parse_date
from ethosloganalyser.analysis.quality import detect_data_errors, rest_voltage_invalid
from ethosloganalyser.config import CHEM, Params
from ethosloganalyser.report.text import summary_lines

LIION = CHEM["Li-Ion"]


# ---------------------------------------------------------------- data errors

def test_rest_voltage_below_the_end_of_flight_load_voltage_is_impossible():
    bad = rest_voltage_invalid([0.72, 3.45, 3.10, np.nan], [3.09, 3.10, 3.11, 3.0])
    assert bad.tolist() == [True, False, False, False]          # 3.10 vs 3.11 is within the tolerance


def _flights(**cols):
    n = len(next(iter(cols.values())))
    base = dict(I_mittel_A=[40.0] * n, I_max_A=[118.0] * n, U_min_Zelle_V=[3.1] * n, VFR_min=[80.0] * n,
                Ri_Zelle_mOhm=[4.4] * n)
    base.update(cols)
    return pd.DataFrame(base)


def test_stuck_current_sensor_is_detected():
    df = _flights(I_mittel_A=[40.0, 99.8, 41.0], I_max_A=[118.0, 100.0, 117.0])
    assert detect_data_errors(df, LIION)["current_stuck"].tolist() == [False, True, False]


def test_voltage_dropout_and_negative_vfr_are_detected():
    df = _flights(U_min_Zelle_V=[3.1, 0.0, 2.9], VFR_min=[80.0, -4.7, 101.0])
    err = detect_data_errors(df, LIION)
    assert err["voltage_dropout"].tolist() == [False, True, False]   # 2.9 V is a real (if low) value
    assert err["vfr_invalid"].tolist() == [False, True, True]


def test_internal_resistance_far_from_the_median_is_implausible():
    df = _flights(Ri_Zelle_mOhm=[4.4, 4.3, 17.55, 4.5, 1.33, 4.6, 5.6])
    assert detect_data_errors(df, LIION)["ri_implausible"].tolist() == [False, False, True, False, True, False, False]


# ---------------------------------------------------------------- ageing model

def _series(values, depth=None):
    df = pd.DataFrame({"Flug": np.arange(1, len(values) + 1, dtype=float), "y": values})
    if depth is not None:
        df["d"] = depth
    return df


def test_start_current_and_trend_come_from_one_robust_line():
    rng = np.random.default_rng(1)
    x = np.arange(1, 61)
    y = 9000 - 5.0 * (x - 1) + rng.normal(0, 60, len(x))
    y[:3] = [9800, 9700, 9750]           # single high start flights must not set the start value
    y[30] = 5500                         # a gross outlier is ignored
    m = ageing_model(_series(y), "y", "capacity")
    assert m["status"] == "ok" and m["trend"] == "down"
    assert abs(m["start"] - 9000) < 120 and abs(m["current"] - (9000 - 5 * 59)) < 80
    assert m["current"] == pytest.approx(m["start"] + m["slope"] * (m["last"] - m["first"]))
    assert 31 in m["outliers"]
    f = forecast(m, 0.8 * 9000, "down")
    assert f["status"] == "ok"
    assert f["lo"] < f["flights"] < f["hi"]
    # the forecast is consistent with the line: current - slope * flights = threshold
    assert m["current"] + m["slope"] * f["flights"] == pytest.approx(0.8 * 9000)


def test_no_forecast_without_significant_trend():
    rng = np.random.default_rng(2)
    m = ageing_model(_series(8700 + rng.normal(0, 150, 30)), "y", "capacity")
    assert m["trend"] == "none"
    assert forecast(m, 7200, "down")["status"] == "no_trend"


def test_no_forecast_from_falling_internal_resistance():
    x = np.arange(1, 31)
    m = ageing_model(_series(4.6 - 0.01 * x), "y", "ri")
    assert m["trend"] == "down"
    assert forecast(m, 1.5 * m["start"], "up")["status"] == "improving"


def test_no_forecast_with_too_few_or_too_scattered_values():
    assert forecast(ageing_model(_series([4.4, 4.5, 4.3]), "y", "ri"), 6.6, "up")["status"] == "too_few"
    m = ageing_model(_series([4.4, 4.5, 4.3, 4.4, 4.6, 4.5, 4.4]), "y", "ri")      # level only, no trend
    assert m["status"] == "ok" and not m["trend_possible"]
    assert forecast(m, 6.6, "up")["status"] == "too_few"
    rng = np.random.default_rng(3)
    x = np.arange(1, 41)
    m = ageing_model(_series(9000 - 20 * x + rng.normal(0, 1500, len(x))), "y", "capacity")
    assert forecast(m, 7200, "down")["status"] == "too_scattered"


def test_threshold_already_reached():
    x = np.arange(1, 31)
    m = ageing_model(_series(7300 - 10.0 * x), "y", "capacity")
    assert forecast(m, 7200, "down") == {"status": "reached", "flights": 0.0}


def test_capacity_is_corrected_for_the_depth_of_discharge():
    rng = np.random.default_rng(4)
    n = 40
    depth = rng.uniform(45, 90, n)
    y = 8800 - 25.0 * (depth - 65) + rng.normal(0, 40, n)      # no ageing, only the bias of the estimate
    m = ageing_model(_series(y, depth), "y", "capacity", depth_col="d")
    assert m["depth_coef"] == pytest.approx(-25, abs=4)
    assert m["trend"] == "none"
    assert np.nanstd(m["normed"]) < 0.3 * np.std(y)


def test_two_battery_groups_are_recognised_but_not_noise():
    rng = np.random.default_rng(5)
    two = np.concatenate([rng.normal(8000, 80, 30), rng.normal(9200, 80, 30)])
    mix = battery_mix(two)
    assert mix and abs(mix["low"] - 8000) < 100 and abs(mix["high"] - 9200) < 100
    assert battery_mix(rng.normal(8700, 180, 90)) is None


# ---------------------------------------------------------------- period filter

def test_dates_are_parsed_in_the_usual_formats():
    assert parse_date("2026-04-19") == date(2026, 4, 19)
    assert parse_date("19.04.2026") == parse_date("19/04/2026") == date(2026, 4, 19)
    assert parse_date("  ") is None
    with pytest.raises(ValueError):
        parse_date("April")


def test_period_is_inclusive_and_open_ended():
    p = Params(date_from="2026-01-01")
    assert in_period(date(2026, 1, 1), p) and not in_period(date(2025, 12, 31), p)
    p = Params(date_from="2026-01-01", date_to="2026-06-30")
    assert in_period(date(2026, 6, 30), p) and not in_period(date(2026, 7, 1), p)


# ---------------------------------------------------------------- whole folder

def _flight(unplugged=False, stuck=False, glide=False):
    """Synthetic 13S Li-Ion flight of about 4 min with 40 s of log after landing."""
    t = np.arange(0, 300, 0.25)
    fly = (t >= 10) & (t < 250)
    i = np.where(fly, 40 + 60 * (np.sin(t / 7) > 0.3), 0.0)
    if stuck:
        i = np.where(fly, 100.0, 0.0)
    if glide:                                                        # last 20 s of the flight at low power
        i = np.where((t >= 230) & (t < 250), 5.0, i)
    q = np.cumsum(i * 0.25) / 3600                                   # Ah
    u = 13 * (4.15 - 0.09 * q) - 0.06 * i
    if unplugged:                                                    # battery unplugged 3 s after landing
        u = np.where(t > 253, 9.0, u)
    return t, u, i


def test_unplugged_battery_after_landing_is_a_data_error_not_a_deep_discharge():
    d = tmpdir()
    for k in range(3):
        t, u, i = _flight(unplugged=(k == 1))
        write_ethos_csv(d, f"Viper-Jet-2026-05-0{k + 1}-12-00-00.csv", t, u, i, start=f"2026-05-0{k + 1} 12:00:00")
    res = ela.analyse_folder(d, Params(chem="Li-Ion", nominal_mah=9000))
    assert res.meta["quality"] == {"rest_voltage_invalid": {2}}
    assert "deep_discharge" not in res.meta["flags"]
    assert res.df.loc[1, "U_ende_Quelle"] == "estimated"
    text = "\n".join(line for _, line in summary_lines(res, Params(chem="Li-Ion", nominal_mah=9000)))
    assert "Ruhespannung nach der Landung unmöglich in 1 von 3 Flügen (Flug 2)" in text


def test_stuck_current_flight_is_kept_out_of_the_battery_values():
    d = tmpdir()
    for k in range(3):
        t, u, i = _flight(stuck=(k == 0))
        write_ethos_csv(d, f"Viper-Jet-2026-05-0{k + 1}-12-00-00.csv", t, u, i, start=f"2026-05-0{k + 1} 12:00:00")
    res = ela.analyse_folder(d, Params(chem="Li-Ion", nominal_mah=9000))
    assert res.meta["quality"]["current_stuck"] == {1}
    first = res.df.iloc[0]
    assert not first["Akku_gueltig"]
    # no coulomb counting, capacity, Ri or timer; the state of charge falls back to the (valid) voltage
    for col in ("SoC_ende_Q_pct", "Kap_gesch_mAh", "Ri_Zelle_mOhm", "U_ref_Zelle_V", "Timer_s"):
        assert np.isnan(first[col]), col
    assert first["SoC_ende_pct"] == first["SoC_ende_U_pct"]
    assert res.df.iloc[1:]["SoC_ende_Q_pct"].notna().all()


def test_period_filter_skips_files_outside_without_reading_them():
    d = tmpdir()
    for day in ("2025-08-01", "2026-05-01", "2026-05-02"):
        t, u, i = _flight()
        write_ethos_csv(d, f"Viper-Jet-{day}-12-00-00.csv", t, u, i, start=f"{day} 12:00:00")
    res = ela.analyse_folder(d, Params(chem="Li-Ion", date_from="2026-01-01"))
    assert len(res.df) == 2 and res.meta["outside_period"] == 1
    assert res.df["datum"].min() >= pd.Timestamp("2026-01-01")


def test_rest_voltage_between_flight_minimum_and_end_of_flight_voltage_is_caught():
    """Gliding in at low current: the resting voltage cannot be below the voltage of the last seconds under load,
    even if it is still above the minimum of the whole flight."""
    d = tmpdir()
    for k in range(3):
        t, u, i = _flight(glide=True)
        if k == 1:
            u = np.where(t > 253, 13 * 3.55, u)          # too low for the end of the flight, above the flight minimum
        write_ethos_csv(d, f"Viper-Jet-2026-05-0{k + 1}-12-00-00.csv", t, u, i, start=f"2026-05-0{k + 1} 12:00:00")
    res = ela.analyse_folder(d, Params(chem="Li-Ion", nominal_mah=9000))
    r = res.df.iloc[1]
    assert r["U_min_Zelle_V"] < 3.55 < r["U_last_Zelle_V"]
    assert res.meta["quality"] == {"rest_voltage_invalid": {2}}
    assert r["U_ende_Quelle"] == "estimated"
