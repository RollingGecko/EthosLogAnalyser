# -*- coding: utf-8 -*-
"""Overall motor curve: electrical power against RPM from all analysed flights.

The single flights scatter a lot (gusts, manoeuvres, battery voltage), so one flight alone shows no clear
curve. The overall curve pools the steady-state points of all flights and takes, per RPM class, the median
power with the 25-75 % band:

* only steady operation: RPM above MIN_RPM, power above MIN_POWER_W and the (smoothed) RPM changing by less
  than MAX_REL_CHANGE per second - run-up, throttle changes and spool-down are left out, because power and
  RPM are not in equilibrium there (and the two sensors are logged with a small time offset),
* median and quartiles instead of mean and standard deviation: single outliers do not move them,
* a class is only used with at least MIN_POINTS points from at least MIN_FLIGHTS flights (fewer flights
  analysed: all of them); classes with too few data are left out instead of being interpolated.

The deviation of one flight from the curve is the median of its relative deviations at its steady points
(in %), so a flight that needs more power for the same RPM (prop, fan, airframe, sensor) stands out.
"""

import numpy as np

from ..config import STEP
from ..utils import _rolling

MIN_RPM = 1000.0
MIN_POWER_W = 100.0
MAX_REL_CHANGE = 0.05       # per second (5 %/s of the current RPM)
MIN_POINTS = 40             # 10 s at the 0.25 s grid
MIN_FLIGHTS = 3
CLASS_WIDTHS = (250, 500, 1000, 2000, 2500, 5000, 10000, 20000)
TARGET_CLASSES = 25


def steady_points(rpm, p, step=STEP):
    """Steady-state (rpm, power) points of one flight (smoothed like the per-flight fit), or two empty arrays."""
    if rpm is None or p is None or len(rpm) < 8:
        return np.array([]), np.array([])
    rpm = np.asarray(rpm, dtype=float)
    p = np.asarray(p, dtype=float)
    rs = _rolling(rpm, 4, "median")
    ps = _rolling(p, 4)
    change = np.abs(np.gradient(rs, step)) / np.maximum(rs, 1.0)
    m = np.isfinite(rs) & np.isfinite(ps) & (rs > MIN_RPM) & (ps > MIN_POWER_W) & (change < MAX_REL_CHANGE)
    return rs[m], ps[m]


def class_width(lo, hi, target=TARGET_CLASSES):
    """Round class width giving about target classes between lo and hi."""
    span = max(hi - lo, 1.0)
    return next((w for w in CLASS_WIDTHS if span / w <= target), CLASS_WIDTHS[-1])


def overall_curve(flights, min_points=MIN_POINTS, min_flights=MIN_FLIGHTS):
    """Median power per RPM class over all flights.

    flights: list of (rpm, p) arrays of steady points (see steady_points), one entry per flight.
    Returns None without enough data, else dict with arrays rpm (median RPM of the class), p50, p25, p75,
    n (points) and flights (number of flights) per used class, plus width (class width in RPM).
    """
    pts = [(np.asarray(r, float), np.asarray(p, float)) for r, p in flights if len(r)]
    if not pts:
        return None
    need_flights = min(min_flights, len(pts))
    r_all = np.concatenate([r for r, _ in pts])
    p_all = np.concatenate([p for _, p in pts])
    f_all = np.concatenate([np.full(len(r), k) for k, (r, _) in enumerate(pts)])
    lo, hi = np.percentile(r_all, [1, 99])
    width = class_width(lo, hi)
    cls = np.floor(r_all / width).astype(int)
    out = {k: [] for k in ("rpm", "p50", "p25", "p75", "n", "flights")}
    for c in np.unique(cls):
        m = cls == c
        nf = len(np.unique(f_all[m]))
        if m.sum() < min_points or nf < need_flights:
            continue
        q25, q50, q75 = np.percentile(p_all[m], [25, 50, 75])
        out["rpm"].append(float(np.median(r_all[m])))
        out["p50"].append(float(q50))
        out["p25"].append(float(q25))
        out["p75"].append(float(q75))
        out["n"].append(int(m.sum()))
        out["flights"].append(int(nf))
    if len(out["rpm"]) < 2:
        return None
    curve = {k: np.asarray(v) for k, v in out.items()}
    curve["width"] = width
    return curve


def curve_power(curve, rpm):
    """Power of the overall curve at rpm (linear between class medians, NaN outside the curve)."""
    rpm = np.asarray(rpm, dtype=float)
    val = np.interp(rpm, curve["rpm"], curve["p50"])
    return np.where((rpm >= curve["rpm"][0]) & (rpm <= curve["rpm"][-1]), val, np.nan)


def flight_deviation(curve, rpm, p, min_points=MIN_POINTS):
    """Median relative deviation [%] of a flight's steady points from the overall curve (NaN if too few)."""
    if curve is None or len(rpm) == 0:
        return np.nan
    pc = curve_power(curve, rpm)
    ok = np.isfinite(pc) & (pc > 0)
    if ok.sum() < min_points:
        return np.nan
    return float(np.median((np.asarray(p, float)[ok] - pc[ok]) / pc[ok] * 100.0))
