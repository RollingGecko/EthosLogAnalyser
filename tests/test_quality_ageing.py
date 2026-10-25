# -*- coding: utf-8 -*-
"""Measurement-error detection, the robust ageing model (SoH, trend, forecast) and the period filter."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from helpers import analyse_folder_logs, tmpdir, write_ethos_csv
import ethosloganalyser as ela
from ethosloganalyser.analysis.ageing import ageing_model, battery_mix, check_consistency, depth_effect, forecast
from ethosloganalyser.analysis.periods import parse_date
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

def _series(values, depth=None, per_day=1):
    """Flights 1..n; per_day flights share one day (same battery age)."""
    n = len(values)
    df = pd.DataFrame({"Flug": np.arange(1, n + 1, dtype=float), "y": values,
                       "day": np.arange(n) // per_day})
    if depth is not None:
        df["d"] = depth
    return df


def _depth_series(rng, n_days=12, per_day=3, ageing=-8.0, bias=-40.0, depth_drift=1.0, noise=40.0):
    """Capacity estimates with ageing per flight, a depth-of-discharge bias and depth rising over time."""
    n = n_days * per_day
    x = np.arange(1, n + 1, dtype=float)
    depth = 55 + depth_drift * (x - 1) * 25 / n + rng.uniform(-8, 8, n)     # later flights deeper
    y = 8800 + ageing * (x - 1) + bias * (depth - 65) + rng.normal(0, noise, n)
    return _series(y, depth, per_day)


def test_start_current_and_trend_come_from_one_robust_line():
    rng = np.random.default_rng(1)
    x = np.arange(1, 61)
    y = 9000 - 5.0 * (x - 1) + rng.normal(0, 60, len(x))
    y[:3] = [9800, 9700, 9750]           # single high start flights must not set the start value
    y[30] = 5500                         # a gross outlier is down-weighted to almost nothing
    m = ageing_model(_series(y), "y", "capacity")
    assert m["status"] == "ok" and m["trend"] == "down" and m["reliable"]
    assert abs(m["start"] - 9000) < 120 and abs(m["current"] - (9000 - 5 * 59)) < 80
    assert m["current"] == pytest.approx(m["start"] + m["slope"] * (m["last"] - m["first"]))
    assert 31 in m["outliers"] and m["weights"][31] < 0.05
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
    n = 42
    depth = rng.uniform(45, 90, n)
    y = 8800 - 25.0 * (depth - 65) + rng.normal(0, 40, n)      # no ageing, only the bias of the estimate
    m = ageing_model(_series(y, depth, per_day=3), "y", "capacity", depth_col="d", session_col="day")
    assert m["depth_method"] == "day"
    assert m["depth_coef"] == pytest.approx(-25, abs=5)
    assert m["trend"] == "none" and not m["reliable"]
    assert m["start"] == m["current"] == m["level"]          # no confirmed change: one level, no slope shown
    assert np.nanstd(m["normed"]) < 0.3 * np.std(y)


def test_falling_capacity_stays_falling_when_later_flights_go_deeper():
    """Depth rises with time and the capacity falls: the depth correction must not swallow the ageing."""
    for seed in range(5):
        rng = np.random.default_rng(10 + seed)
        df = _depth_series(rng)
        m = ageing_model(df, "y", "capacity", depth_col="d", session_col="day")
        assert np.corrcoef(df["d"], df["Flug"])[0, 1] > 0.6
        assert m["depth_coef"] == pytest.approx(-40, abs=12)
        assert m["trend"] == "down" and m["reliable"], seed
        assert m["slope"] == pytest.approx(-8, abs=3)
        assert m["current"] < m["start"]


def test_depth_effect_comes_only_from_flights_of_the_same_day():
    # ageing and rising depth, but no depth bias at all: a joint fit over time could mistake the ageing for a
    # depth effect, the within-day estimate must not
    rng = np.random.default_rng(5)
    df = _depth_series(rng, ageing=-10.0, bias=0.0)
    eff = depth_effect(df["y"], df["d"], df["day"])
    assert abs(eff["coef"]) < 2.5 * eff["se"]
    m = ageing_model(df, "y", "capacity", depth_col="d", session_col="day")
    assert m["depth_coef"] == 0.0 and m["trend"] == "down"
    assert m["slope"] == pytest.approx(-10, abs=3)


def test_one_flight_per_day_with_drifting_depth_is_uncertain():
    rng = np.random.default_rng(6)
    df = _depth_series(rng, n_days=30, per_day=1)
    m = ageing_model(df, "y", "capacity", depth_col="d", session_col="day")
    assert m["depth_method"] == "none" and "depth_confounded" in m["uncertain"]
    assert not m["reliable"]
    assert forecast(m, 7200, "down")["status"] == "uncertain"


def test_rising_capacity_is_never_shown_as_a_trend():
    x = np.arange(1, 31)
    rng = np.random.default_rng(7)
    m = ageing_model(_series(8500 + 12.0 * x + rng.normal(0, 30, len(x))), "y", "capacity")
    assert m["trend"] == "up"
    assert "capacity_rising" in m["uncertain"] and not m["reliable"]
    assert m["start"] == m["current"] == m["level"]
    assert forecast(m, 0.8 * 9000, "down")["status"] == "uncertain"


def test_capacity_and_reference_voltage_must_agree():
    x = np.arange(1, 31)
    rng = np.random.default_rng(8)
    cap = ageing_model(_series(8800 + rng.normal(0, 120, len(x))), "y", "capacity")
    u_down = ageing_model(_series(3.63 - 0.0006 * x + rng.normal(0, 0.002, len(x))), "y", "u_ref")
    assert cap["trend"] == "none" and u_down["trend"] == "down"
    check_consistency(cap, u_down)
    assert "contradicts_u_ref" in cap["uncertain"] and cap["u_ref_trend"] == "down"
    # both falling: consistent, the capacity line is shown
    cap2 = ageing_model(_series(8800 - 10.0 * x + rng.normal(0, 30, len(x))), "y", "capacity")
    check_consistency(cap2, u_down)
    assert cap2["reliable"] and not cap2["uncertain"]


def test_low_values_at_the_end_that_follow_the_trend_are_kept():
    rng = np.random.default_rng(9)
    x = np.arange(1, 34, dtype=float)
    y = 8800 - 8.0 * x + rng.normal(0, 60, len(x))
    y[-2:] = 8800 - 8.0 * x[-2:] - 120                # the last two flights are low, but still along the trend
    m = ageing_model(_series(y), "y", "capacity")
    assert all(m["weights"][f] > 0.5 for f in (32, 33))
    assert not set(m["outliers"]) & {32, 33}
    assert m["trend"] == "down" and m["reliable"]
    # even values far below the line are only down-weighted, never dropped
    y[-2:] -= 600
    m = ageing_model(_series(y), "y", "capacity")
    assert all(m["weights"][f] > 0 for f in (32, 33))


def test_two_battery_groups_are_recognised_but_not_noise():
    rng = np.random.default_rng(5)
    two = np.concatenate([rng.normal(8000, 80, 30), rng.normal(9200, 80, 30)])
    mix = battery_mix(two)
    assert mix and abs(mix["low"] - 8000) < 100 and abs(mix["high"] - 9200) < 100
    assert battery_mix(rng.normal(8700, 180, 90)) is None


# ---------------------------------------------------------------- dates typed by the user

def test_dates_are_parsed_in_the_usual_formats():
    assert parse_date("2026-04-19") == date(2026, 4, 19)
    assert parse_date("19.04.2026") == parse_date("19/04/2026") == date(2026, 4, 19)
    assert parse_date("  ") is None
    with pytest.raises(ValueError):
        parse_date("April")


# ---------------------------------------------------------------- several flights

def _flight(unplugged=False, stuck=False, glide=False, short=False, drop=0.09):
    """Synthetic 13S Li-Ion flight of about 4 min with 40 s of log after landing (short: about 2 min)."""
    t = np.arange(0, 300, 0.25)
    fly = (t >= 10) & (t < (140 if short else 250))
    i = np.where(fly, 40 + 60 * (np.sin(t / 7) > 0.3), 0.0)
    if stuck:
        i = np.where(fly, 100.0, 0.0)
    if glide:                                                        # last 20 s of the flight at low power
        i = np.where((t >= 230) & (t < 250), 5.0, i)
    q = np.cumsum(i * 0.25) / 3600                                   # Ah
    u = 13 * (4.15 - drop * q) - 0.06 * i
    if unplugged:                                                    # battery unplugged 3 s after landing
        u = np.where(t > 253, 9.0, u)
    return t, u, i


def test_unplugged_battery_after_landing_is_a_data_error_not_a_deep_discharge():
    d = tmpdir()
    for k in range(3):
        t, u, i = _flight(unplugged=(k == 1))
        write_ethos_csv(d, f"Viper-Jet-2026-05-0{k + 1}-12-00-00.csv", t, u, i, start=f"2026-05-0{k + 1} 12:00:00")
    res = analyse_folder_logs(d, Params(chem="Li-Ion", nominal_mah=9000))
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
    res = analyse_folder_logs(d, Params(chem="Li-Ion", nominal_mah=9000))
    assert res.meta["quality"]["current_stuck"] == {1}
    first = res.df.iloc[0]
    assert not first["Akku_gueltig"]
    # no coulomb counting, capacity, Ri or timer; the state of charge falls back to the (valid) voltage
    for col in ("SoC_ende_Q_pct", "Kap_gesch_mAh", "Ri_Zelle_mOhm", "U_ref_Zelle_V", "Timer_s"):
        assert np.isnan(first[col]), col
    assert first["SoC_ende_pct"] == first["SoC_ende_U_pct"]
    assert res.df.iloc[1:]["SoC_ende_Q_pct"].notna().all()


def test_rest_voltage_between_flight_minimum_and_end_of_flight_voltage_is_caught():
    """Gliding in at low current: the resting voltage cannot be below the voltage of the last seconds under load,
    even if it is still above the minimum of the whole flight."""
    d = tmpdir()
    for k in range(3):
        t, u, i = _flight(glide=True)
        if k == 1:
            u = np.where(t > 253, 13 * 3.55, u)          # too low for the end of the flight, above the flight minimum
        write_ethos_csv(d, f"Viper-Jet-2026-05-0{k + 1}-12-00-00.csv", t, u, i, start=f"2026-05-0{k + 1} 12:00:00")
    res = analyse_folder_logs(d, Params(chem="Li-Ion", nominal_mah=9000))
    r = res.df.iloc[1]
    assert r["U_min_Zelle_V"] < 3.55 < r["U_last_Zelle_V"]
    assert res.meta["quality"] == {"rest_voltage_invalid": {2}}
    assert r["U_ende_Quelle"] == "estimated"


def test_short_flights_are_kept_out_of_capacity_and_internal_resistance_trends():
    d = tmpdir()
    days = ["2026-05-%02d" % k for k in range(1, 13)]
    for k, day in enumerate(days):
        t, u, i = _flight(short=(k == len(days) - 1), drop=0.16)      # normal flights about 70 % deep
        write_ethos_csv(d, f"Viper-Jet-{day}-12-00-00.csv", t, u, i, start=f"{day} 12:00:00")
    p = Params(chem="Li-Ion", nominal_mah=9000)
    res = analyse_folder_logs(d, p)
    last = int(res.df["Flug"].max())
    assert res.meta["short_flights"] == {last}
    assert np.isnan(res.df.iloc[-1]["Kap_gesch_mAh"])
    assert last not in res.meta["ageing"]["ri"]["weights"]
    text = "\n".join(line for _, line in summary_lines(res, p))
    assert f"Kurzflüge unter 40 % Entladetiefe zählen nicht für Kapazität und Innenwiderstand: Flug {last}" in text
