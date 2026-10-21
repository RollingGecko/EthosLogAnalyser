# -*- coding: utf-8 -*-
"""Empfängerstrom-Spitzen: Erkennung und Zuordnung des Anlasses (synthetische Daten)."""

import numpy as np

import helpers  # noqa: F401  (setzt den Importpfad)
from ethosloganalyser.analysis.rx_spikes import rx_spike_analysis
from ethosloganalyser.config import STEP


def _signal(spike_times, dauer=400.0, base=0.5, hoehe=2.0):
    t = np.arange(0, dauer, STEP)
    rx = np.full_like(t, base) + np.random.default_rng(0).normal(0, 0.01, len(t))
    for ts in spike_times:
        rx[(t >= ts) & (t < ts + 1.0)] += hoehe
    return t, rx


def _anlass(res, t_spike):
    sp = min(res["spikes"], key=lambda s: abs(s["t"] - t_spike))
    assert abs(sp["t"] - t_spike) < 2
    return sp["anlass"]


def test_spitzen_werden_gefunden_und_zugeordnet():
    t, rx = _signal([10, 100, 200, 300])
    stick = np.zeros_like(t)
    stick[(t >= 199) & (t < 202)] = 300.0                 # schnelle Knüppelbewegung bei 200 s
    g = np.ones_like(t)                                   # Lagedaten vorhanden, ruhiger Flug
    switches = [(299.0, "LS1", 0.0, 1.0)]                 # Schalter kurz vor der Spitze bei 300 s
    res = rx_spike_analysis(t, rx, g=g, stick=stick, switches=switches)
    assert len(res["spikes"]) == 4
    assert _anlass(res, 10) == "Start/Landung"
    assert _anlass(res, 100) == "ohne erkennbaren Anlass"
    assert _anlass(res, 200) == "Manöver"
    assert _anlass(res, 300) == "Schalter"


def test_ohne_lagedaten_kein_urteil():
    t, rx = _signal([150])
    res = rx_spike_analysis(t, rx)
    assert _anlass(res, 150) == "keine Lagedaten"


def test_ruhiges_signal_ohne_spitzen():
    t, rx = _signal([])
    res = rx_spike_analysis(t, rx, g=np.ones_like(t))
    assert res["spikes"] == []
    assert abs(res["base"] - 0.5) < 0.05


def test_dicht_aufeinanderfolgende_spitzen_zaehlen_einmal():
    t, rx = _signal([100, 101.5])                         # Lücke < 1 s
    res = rx_spike_analysis(t, rx, g=np.ones_like(t))
    assert len(res["spikes"]) == 1


def test_kein_empfaengerstrom():
    t = np.arange(0, 100, STEP)
    assert rx_spike_analysis(t, None) is None
    assert rx_spike_analysis(t, np.zeros_like(t)) is None
