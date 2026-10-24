# -*- coding: utf-8 -*-
"""Receiver base current (sticks neutral): per flight and trend across flights (synthetic data)."""

import numpy as np

import helpers  # noqa: F401  (sets the import path)
from ethosloganalyser.analysis.evaluate import evaluate
from ethosloganalyser.analysis.rx_baseline import MIN_CHANGE_A, base_current, base_trend
from ethosloganalyser.config import STEP, Params, channel_names
from ethosloganalyser.i18n import set_language


def _sticks(n, seed, hold_elevator=True):
    """Stick movements [%] like a pilot's: aileron and rudder in short moves, elevator mostly pulled."""
    rng = np.random.default_rng(seed)
    out = {}
    for k in ("aileron", "elevator", "rudder"):
        x = np.zeros(n)
        i = 0
        while i < n:
            dur = int(rng.integers(4, 24))
            if k == "elevator" and hold_elevator:
                amp = rng.choice([-50.0, -30.0, rng.uniform(-90, 60)])     # neutral only by chance
            else:
                amp = rng.choice([0.0, 0.0, rng.uniform(-100, 100)])
            x[i:i + dur] = amp
            i += dur
        out[k] = np.convolve(x, np.ones(3) / 3, "same")
    return out


def _flight(base, seed=0, duration=480.0, lag_s=0.75, sticks=None):
    """Receiver current = base + servo current proportional to deflection, delayed, coarse like telemetry."""
    t = np.arange(0, duration, STEP)
    st = sticks if sticks is not None else _sticks(len(t), seed)
    rng = np.random.default_rng(seed + 50)
    i = np.full(len(t), base)
    for k, a in (("aileron", 0.4), ("elevator", 0.25), ("rudder", 0.5)):
        i = i + a * np.abs(st[k]) / 100.0
    sh = int(round(lag_s / STEP))
    rx = np.r_[np.full(sh, base), i[:-sh]] + rng.normal(0, 0.04, len(t))
    rx[rng.random(len(t)) < 0.01] += 2.0                   # a few spikes must not move the value
    rx = np.round(np.repeat(rx[::2], 2)[:len(t)], 2)       # updated only every 0.5 s, 0.01 A resolution
    return t, rx, st, np.full(len(t), 100.0)


def test_base_current_is_found_although_sticks_are_rarely_neutral():
    t, rx, st, alt = _flight(0.7)
    neutral = np.mean(np.all([np.abs(v) < 10 for v in st.values()], axis=0))
    assert neutral < 0.1                                    # all sticks neutral less than 10 % of the time
    res = base_current(t, rx, st, alt)
    assert res["reason"] == ""
    assert abs(res["value"] - 0.7) < 0.05
    assert res["lag_s"] in (0.5, 0.75, 1.0)


def test_rising_base_current_is_detected():
    x = np.arange(1, 21)
    vals = [base_current(*_flight(0.6 + 0.012 * k, seed=k))["value"] for k in range(20)]
    tr_ = base_trend(x, vals)
    assert tr_["trend"] == "up" and tr_["reliable"]
    assert tr_["change"] >= MIN_CHANGE_A
    assert abs(tr_["start"] - 0.6) < 0.06 and abs(tr_["current"] - 0.83) < 0.06
    assert np.all(tr_["band_lo"] <= tr_["band_hi"])


def test_constant_base_current_shows_no_trend():
    x = np.arange(1, 21)
    vals = [base_current(*_flight(0.8, seed=k))["value"] for k in range(20)]
    tr_ = base_trend(x, vals)
    assert tr_["trend"] == "none" and not tr_["reliable"]
    assert tr_["start"] == tr_["current"] == tr_["level"]
    assert abs(tr_["level"] - 0.8) < 0.05


def test_small_significant_change_is_not_a_trend():
    """A change smaller than MIN_CHANGE_A over the period is of no practical use - no trend, no hint."""
    x = np.arange(1, 31)
    y = 0.7 + 0.002 * x                    # +0.06 A over 30 flights, without scatter: significant but tiny
    tr_ = base_trend(x, y)
    assert tr_["slope_lo"] > 0 and tr_["trend"] == "none"


def test_too_little_data_gives_no_value():
    t, rx, st, alt = _flight(0.7, duration=180.0)          # 105 s airborne - too short
    res = base_current(t, rx, st, alt)
    assert np.isnan(res["value"]) and res["reason"] == "few_data"
    t, rx, st, alt = _flight(0.7)
    assert base_current(t, rx, {}, alt)["reason"] == "no_sticks"
    assert base_current(t, None, st, alt)["reason"] == "no_rx"
    assert base_current(t, np.zeros_like(t), st, alt)["reason"] == "no_rx"
    assert base_trend(np.arange(5), np.full(5, 0.7))["status"] == "too_few"


def test_hint_only_for_a_confirmed_rise():
    import pandas as pd
    set_language("de")
    df = pd.DataFrame({"Flug": np.arange(1, 21)})
    for c in ("SoC_Abw_pct", "Reserve_Zelle_V", "SoC_ende_Q_pct", "U_ende_Zelle_V", "U_min_Zelle_V",
              "Sensor_Abw_pct", "RxSp_ohne"):
        df[c] = np.nan
    df["U_ende_Quelle"] = ""
    up = dict(status="ok", trend="up", start=0.6, current=0.85, first=1.0, last=20.0)
    flat = dict(up, trend="none")
    texts = lambda meta: [str(m) for _, m in evaluate(df, Params(), meta)[0]]
    assert any("Grundstrom des Empfängers ist über die Flüge gestiegen" in s for s in texts(dict(rx_base=up)))
    assert not any("Grundstrom" in s for s in texts(dict(rx_base=flat)))


def test_flight_table_has_base_current_column():
    """Synthetic Ethos log: the column exists; a log without stick channels has no value."""
    from ethosloganalyser.analysis.flight import analyse_file
    t = np.arange(0, 400, 0.25)
    st = _sticks(len(t), 7)
    u = 50 - 0.01 * t
    i = np.where((t > 5) & (t < 395), 30.0, 0.0)
    rx = 0.65 + 0.4 * np.abs(st["aileron"]) / 100 + 0.25 * np.abs(st["elevator"]) / 100
    extra = {"RxCurrent(A)": np.round(rx, 2), "Altitude(m)": np.where((t > 20) & (t < 380), 100.0, 0.0)}
    path = helpers.write_ethos_csv(helpers.tmpdir(), "M-2026-05-01-12-00-00.csv", t, u, i, extra=extra)
    row, _ = analyse_file(str(path), Params(min_flight_s=60))
    assert np.isnan(row["Rx_Grund_A"]) and row["_series"]["rx_base"]["reason"] == "no_sticks"
    extra.update({"QR": np.round(st["aileron"] * 10.24), "HR": np.round(st["elevator"] * 10.24)})
    path = helpers.write_ethos_csv(helpers.tmpdir(), "M-2026-05-01-12-00-00.csv", t, u, i, extra=extra)
    row, _ = analyse_file(str(path), Params(min_flight_s=60))
    assert abs(row["Rx_Grund_A"] - 0.65) < 0.05
    # other column names only with an assignment
    extra["Roll"], extra["Pitch"] = extra.pop("QR"), extra.pop("HR")
    path = helpers.write_ethos_csv(helpers.tmpdir(), "M-2026-05-01-12-00-00.csv", t, u, i, extra=extra)
    row, _ = analyse_file(str(path), Params(min_flight_s=60))
    assert np.isnan(row["Rx_Grund_A"])
    row, _ = analyse_file(str(path), Params(min_flight_s=60, channels={"aileron": "Roll", "elevator": "Pitch"}))
    assert abs(row["Rx_Grund_A"] - 0.65) < 0.05


def test_channel_assignment_defaults():
    assert [channel_names(c)[0] for c in ("aileron", "elevator", "rudder", "throttle")] == ["QR", "HR", "SR", "Gas"]
    assert channel_names("aileron", {"aileron": "Ail1"}) == ("Ail1",)
    assert Params().channels == {}
