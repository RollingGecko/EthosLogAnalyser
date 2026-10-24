# -*- coding: utf-8 -*-
"""Overall motor curve (analysis/motor_curve.py)."""

import numpy as np
import pytest

import helpers
from matplotlib.backends.backend_agg import FigureCanvasAgg

from ethosloganalyser.analysis.motor_curve import (class_width, curve_power, flight_deviation, overall_curve,
                                                   steady_points)
from ethosloganalyser.config import Params
from ethosloganalyser.plots.overview import figure_antrieb
from ethosloganalyser.plots.single import single_chart

K = 5.0e-12          # P = K * rpm^3: 4000 W at about 92 800 RPM


def truth(rpm):
    return K * np.asarray(rpm, float) ** 3


def synthetic_flight(seed, factor=1.0, n=2400, step=0.25):
    """RPM/power time series: steady sections at several RPM levels, fast run-ups between them, noise and a
    few gross outliers (sensor glitches)."""
    rng = np.random.default_rng(seed)
    levels = rng.permutation(np.arange(40000, 95001, 5000))
    seg = n // len(levels)
    rpm = np.concatenate([np.full(seg, lv, float) for lv in levels])
    for k in range(1, len(levels)):                         # run-up/down over 1 s between the levels
        j = k * seg
        rpm[j - 2:j + 2] = np.linspace(rpm[j - 3], rpm[j + 2], 4)
    rpm = rpm + rng.normal(0, 300, len(rpm))
    p = factor * truth(rpm) * (1 + rng.normal(0, 0.03, len(rpm)))
    # during the run-ups the power leads the RPM (not in equilibrium): far off the curve
    ramp = np.abs(np.gradient(rpm, step)) / rpm > 0.2
    p[ramp] *= 1.8
    bad = rng.choice(len(p), 15, replace=False)
    p[bad] = rng.choice([30000.0, 5.0], 15)                 # outliers
    return rpm, p


def test_steady_points_drop_run_ups_and_idle():
    rpm = np.concatenate([np.full(80, 500.0), np.linspace(500, 80000, 20), np.full(200, 80000.0)])
    p = truth(rpm) + 50
    r, pp = steady_points(rpm, p)
    assert len(r) and r.min() > 1000                          # idle (below MIN_RPM) left out
    assert np.all(np.abs(r - 80000) < 1)                      # only the steady part


def test_steady_points_without_rpm():
    assert [len(a) for a in steady_points(None, np.ones(10))] == [0, 0]


@pytest.mark.parametrize("lo, hi, width", [(30000, 95000, 5000), (20000, 30000, 500), (1000, 4000, 250),
                                           (0, 2e6, 20000)])
def test_class_width(lo, hi, width):
    assert class_width(lo, hi) == width


def test_curve_follows_the_truth_despite_outliers_and_transitions():
    flights = [steady_points(*synthetic_flight(k)) for k in range(6)]
    curve = overall_curve(flights)
    assert curve is not None and len(curve["rpm"]) >= 10
    rel = curve["p50"] / truth(curve["rpm"]) - 1
    assert np.max(np.abs(rel)) < 0.02                        # median within 2 % of the true curve
    assert np.all(curve["p25"] <= curve["p50"]) and np.all(curve["p50"] <= curve["p75"])
    assert np.all(np.diff(curve["rpm"]) > 0) and np.all(curve["flights"] == 6)
    # the band reflects the 3 % noise, not the outliers
    assert np.max((curve["p75"] - curve["p25"]) / curve["p50"]) < 0.08


def test_classes_with_too_few_data_are_left_out():
    flights = [steady_points(*synthetic_flight(k)) for k in range(4)]
    rpm, p = synthetic_flight(9)
    flights.append((np.full(20, 30000.0), truth(np.full(20, 30000.0))))     # one flight, 5 s at 30 000 RPM
    curve = overall_curve(flights)
    assert curve["rpm"].min() > 35000                        # the 30 000 RPM class is not used
    assert np.isnan(curve_power(curve, 30000.0))             # no extrapolation outside the curve


def test_too_few_data_gives_no_curve():
    assert overall_curve([]) is None
    assert overall_curve([(np.array([50000.0]), np.array([600.0]))]) is None


def test_flight_deviation():
    flights = [steady_points(*synthetic_flight(k)) for k in range(6)]
    curve = overall_curve(flights)
    heavy = steady_points(*synthetic_flight(42, factor=1.10))
    normal = steady_points(*synthetic_flight(43))
    assert flight_deviation(curve, *heavy) == pytest.approx(10, abs=1.5)
    assert flight_deviation(curve, *normal) == pytest.approx(0, abs=1.5)
    assert np.isnan(flight_deviation(curve, np.array([60000.0]), np.array([1000.0])))     # too few points
    assert np.isnan(flight_deviation(None, *normal))


def test_overall_curve_in_drive_chart():
    res = helpers.example_result(9000.0)
    p = Params(nominal_mah=9000.0)
    curve = res.meta["motor_curve"]
    assert curve is not None
    assert "P_Kurve_Abw_pct" in res.df and res.df["P_Kurve_Abw_pct"].notna().any()
    fig = figure_antrieb(res, p)
    FigureCanvasAgg(fig).draw()
    ax = fig.axes[0]
    labels = [ln.get_label() for ln in ax.lines]
    assert "Gesamtkennlinie (Median aller Flüge)" in labels and "Streuband 25–75 %" in labels
    line = next(ln for ln in ax.lines if ln.get_label() == "Gesamtkennlinie (Median aller Flüge)")
    assert line.get_xdata() == pytest.approx(curve["rpm"] / 1000)
    assert len(ax.collections) >= 1                          # the band
    # enlarged alone: keeps its own x label (not "Flug Nr." of the chart below it)
    fig = figure_antrieb(res, p)
    (kept,) = single_chart(fig, 0)
    assert kept.get_xlabel() == "Drehzahl [1000 U/min]"
