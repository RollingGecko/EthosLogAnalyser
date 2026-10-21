# -*- coding: utf-8 -*-
"""Receiver current spikes: detection and cause assignment (synthetic data)."""

import numpy as np

import helpers  # noqa: F401  (sets the import path)
from ethosloganalyser.analysis.rx_spikes import rx_spike_analysis
from ethosloganalyser.config import STEP


def _signal(spike_times, duration=400.0, base=0.5, height=2.0):
    t = np.arange(0, duration, STEP)
    rx = np.full_like(t, base) + np.random.default_rng(0).normal(0, 0.01, len(t))
    for ts in spike_times:
        rx[(t >= ts) & (t < ts + 1.0)] += height
    return t, rx


def _cause(res, t_spike):
    sp = min(res["spikes"], key=lambda s: abs(s["t"] - t_spike))
    assert abs(sp["t"] - t_spike) < 2
    return sp["anlass"]


def test_spikes_are_found_and_assigned_a_cause():
    t, rx = _signal([10, 100, 200, 300])
    stick = np.zeros_like(t)
    stick[(t >= 199) & (t < 202)] = 300.0                 # fast stick movement at 200 s
    g = np.ones_like(t)                                   # attitude data present, calm flight
    switches = [(299.0, "LS1", 0.0, 1.0)]                 # switch flipped shortly before the spike at 300 s
    res = rx_spike_analysis(t, rx, g=g, stick=stick, switches=switches)
    assert len(res["spikes"]) == 4
    assert _cause(res, 10) == "Start/Landung"
    assert _cause(res, 100) == "ohne erkennbaren Anlass"
    assert _cause(res, 200) == "Manöver"
    assert _cause(res, 300) == "Schalter"


def test_without_attitude_data_no_verdict():
    t, rx = _signal([150])
    res = rx_spike_analysis(t, rx)
    assert _cause(res, 150) == "keine Lagedaten"


def test_quiet_signal_has_no_spikes():
    t, rx = _signal([])
    res = rx_spike_analysis(t, rx, g=np.ones_like(t))
    assert res["spikes"] == []
    assert abs(res["base"] - 0.5) < 0.05


def test_spikes_close_together_count_once():
    t, rx = _signal([100, 101.5])                         # gap < 1 s
    res = rx_spike_analysis(t, rx, g=np.ones_like(t))
    assert len(res["spikes"]) == 1


def test_no_receiver_current():
    t = np.arange(0, 100, STEP)
    assert rx_spike_analysis(t, None) is None
    assert rx_spike_analysis(t, np.zeros_like(t)) is None
