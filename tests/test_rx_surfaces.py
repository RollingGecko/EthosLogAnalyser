# -*- coding: utf-8 -*-
"""Receiver current per control surface: estimate from the total current (synthetic data)."""

import numpy as np

import helpers  # noqa: F401  (sets the import path)
from ethosloganalyser.analysis.rx_surfaces import (assign_spikes, combined_manoeuvres, surface_current_analysis,
                                                   surface_trend)
from ethosloganalyser.config import STEP, Params, channel_names


def _sticks(n, seed):
    """Independent stick movements [%] like a pilot's: smooth random moves with pauses at neutral."""
    rng = np.random.default_rng(seed)
    out = {}
    for k in ("aileron", "elevator", "rudder"):
        x = np.zeros(n)
        i = 0
        while i < n:
            dur = int(rng.integers(4, 24))
            amp = rng.choice([0.0, 0.0, rng.uniform(-100, 100)])
            x[i:i + dur] = amp
            i += dur
        out[k] = np.convolve(x, np.ones(3) / 3, "same")
    return out


def _flight(per100, base=0.6, lag_s=0.75, seed=0, sticks=None, noise=0.03, duration=500.0):
    """Synthetic flight: receiver current = base + sum(per100[k] * |deflection_k|), delayed by lag_s."""
    t = np.arange(0, duration, STEP)
    st = sticks if sticks is not None else _sticks(len(t), seed)
    i = np.full(len(t), base)
    for k, a in per100.items():
        i = i + a * np.abs(st[k]) / 100.0
    sh = int(round(lag_s / STEP))
    rx = np.r_[np.full(sh, base), i[:-sh]] + np.random.default_rng(seed + 100).normal(0, noise, len(t))
    alt = np.full(len(t), 100.0)
    return t, rx, st, alt


def test_per_surface_current_and_lag_are_recovered():
    t, rx, st, alt = _flight({"aileron": 1.2, "elevator": 0.3, "rudder": 0.2})
    res = surface_current_analysis(t, rx, st, alt, n_boot=100)
    assert res["lag_s"] == 0.75
    s = res["surfaces"]
    assert abs(s["aileron"]["per100"] - 1.2) < 0.1
    assert abs(s["elevator"]["per100"] - 0.3) < 0.1
    assert s["aileron"]["per100_lo"] < 1.2 < s["aileron"]["per100_hi"]
    assert abs(res["base_a"] - 0.6) < 0.05
    assert all(v["status"] == "ok" for v in s.values())


def test_surface_with_rising_current_is_detected_across_flights():
    """Aileron current rises from flight to flight, the others stay - only the aileron shows a trend."""
    vals = {k: [] for k in ("aileron", "elevator", "rudder")}
    for n in range(10):
        t, rx, st, alt = _flight({"aileron": 0.3 + 0.08 * n, "elevator": 0.3, "rudder": 0.3}, seed=n)
        res = surface_current_analysis(t, rx, st, alt, n_boot=60, seed=n)
        for k in vals:
            v = res["surfaces"][k]
            vals[k].append((v["per100"], v["per100_lo"], v["per100_hi"]))
    x = np.arange(10)
    trend = {k: surface_trend(x, *np.array(v).T) for k, v in vals.items()}
    assert trend["aileron"]["rising"]
    assert abs(trend["aileron"]["slope"] - 0.08) < 0.02
    assert not trend["elevator"]["rising"] and not trend["elevator"]["falling"]
    assert not trend["rudder"]["rising"] and not trend["rudder"]["falling"]


def test_coupled_channels_are_not_separable():
    """Rudder always moved with the aileron (e.g. a mix or coordinated turns) -> no statement per surface."""
    n = int(500 / STEP)
    st = _sticks(n, 3)
    st["rudder"] = 0.9 * st["aileron"] + np.random.default_rng(1).normal(0, 3, n)
    t, rx, st, alt = _flight({"aileron": 1.0, "elevator": 0.3, "rudder": 0.0}, sticks=st)
    res = surface_current_analysis(t, rx, st, alt, n_boot=50)
    assert res["surfaces"]["aileron"]["status"] == "not_separable"
    assert res["surfaces"]["rudder"]["status"] == "not_separable"
    assert res["surfaces"]["elevator"]["status"] == "ok"
    assert abs(res["coupling"][("aileron", "rudder")]) > 0.9


def test_rarely_used_surface_has_too_few_data():
    t, rx, st, alt = _flight({"aileron": 1.0, "elevator": 0.3, "rudder": 0.5})
    st["rudder"] = np.where(np.arange(len(t)) < 20, 60.0, 0.0)        # only 5 s at the start (not airborne)
    res = surface_current_analysis(t, rx, st, alt, n_boot=30)
    assert res["surfaces"]["rudder"]["status"] == "few_data"


def test_missing_channel_and_no_current():
    t, rx, st, alt = _flight({"aileron": 1.0, "elevator": 0.3})
    del st["rudder"]
    res = surface_current_analysis(t, rx, st, alt, n_boot=20)
    assert res["surfaces"]["rudder"]["status"] == "missing"
    assert np.isnan(res["surfaces"]["rudder"]["per100"])
    assert surface_current_analysis(t, None, st, alt) is None
    assert surface_current_analysis(t, np.zeros_like(t), st, alt) is None
    assert surface_current_analysis(t, rx, {}, alt) is None


def test_combined_full_deflection_is_left_out_and_reported():
    t, rx, st, alt = _flight({"aileron": 0.5, "elevator": 0.3, "rudder": 0.3})
    seg = (t >= 200) & (t < 205)
    for k in st:
        st[k][seg] = 98.0
    rx = rx.copy()
    rx[(t >= 200.75) & (t < 205.75)] += 2.0      # extra load only during the combined manoeuvre
    res = surface_current_analysis(t, rx, st, alt, n_boot=50)
    assert len(res["combined"]) == 1
    c = res["combined"][0]
    assert 199.5 < c["t0"] < 200.5 and c["peak_a"] > 3.0
    # the manoeuvre does not distort the per-surface estimate
    assert abs(res["surfaces"]["aileron"]["per100"] - 0.5) < 0.1


def test_spike_assignment():
    t = np.arange(0, 100, STEP)
    z = np.zeros_like(t)
    defl = {"aileron": z.copy(), "elevator": z.copy(), "rudder": z.copy()}
    defl["aileron"][(t >= 19) & (t < 20)] = 0.9                       # spike at 20.75 s, lag 0.75 s
    defl["aileron"][(t >= 49) & (t < 50)] = 0.8
    defl["elevator"][(t >= 49) & (t < 50)] = 0.75                     # both about equal -> several
    keys = list(defl)
    got = assign_spikes([20.75, 50.75, 80.75], t, defl, 0.75, keys)
    assert got == ["aileron", "several", "none"]
    assert combined_manoeuvres(defl, keys) == []


def test_channel_assignment_defaults_and_override():
    assert channel_names("aileron")[0] == "QR"
    assert channel_names("elevator")[0] == "HR"
    assert channel_names("rudder")[0] == "SR"
    assert channel_names("throttle")[0] == "Gas"
    assert channel_names("aileron", {"aileron": "Ail1"}) == ("Ail1",)
    assert Params().channels == {}


def test_assigned_channel_names_are_read_from_the_log():
    """A log with other stick names: found only with an assignment in Params.channels."""
    from ethosloganalyser.analysis.flight import analyse_file
    t = np.arange(0, 300, 0.25)
    u = 50 - 0.01 * t
    i = np.where((t > 5) & (t < 295), 30.0, 0.0)
    move = 80 * np.sin(t / 3.0)
    path = helpers.write_ethos_csv(helpers.tmpdir(), "Model-2026-05-01-12-00-00.csv", t, u, i,
                                   extra={"Roll": np.round(move), "Pitch": np.round(move * 0.5)})
    row, _ = analyse_file(str(path), Params(min_flight_s=60))
    assert "aileron" not in row["_series"]["sticks"]
    row, _ = analyse_file(str(path), Params(min_flight_s=60, channels={"aileron": "Roll", "elevator": "Pitch"}))
    assert set(row["_series"]["sticks"]) == {"aileron", "elevator"}
