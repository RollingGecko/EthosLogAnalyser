# -*- coding: utf-8 -*-
"""Base current of the receiver: the current it draws with all sticks at neutral and still.

The log only has the TOTAL receiver current. Servos draw current when they move and when they hold a surface
against the air load; with all sticks at neutral and still, what is left is the base current (receiver, servos
holding neutral, other consumers). A slowly rising base current over many flights can be an early sign that
servos or linkages need more current than before (binding, play, wear) - it does not tell which one.

Moments with ALL sticks at neutral are rare in real flights (the elevator is held pulled most of the time), so
the base current is not read from such moments but estimated from the whole airborne part of the flight
(see docs/methodology.md, "Receiver base current"):

    I_rx(t + delay) = I_base + sum over the logged sticks ( a_k * |deflection_k(t)| + b_k * |stick speed_k(t)| )

fitted with Huber weights (robust against spikes); I_base is the current at 0 % deflection and no stick
movement. The per-stick terms are only a means to that end and are not reported: they cannot be told apart
reliably and say nothing about a single servo. The delay (0-2 s) is chosen by the best fit - the receiver
current is only updated about every 0.5 s and follows the sticks by about 0.75 s on the real logs. Only the
airborne part counts: without the first 30 s and the last 45 s, above 15 m altitude if altitude is logged.

Across flights a robust line (Huber weights, as for battery ageing) is fitted; a rise is only reported when the
90 % range of the slope excludes zero AND the change over the period is at least MIN_CHANGE_A.
"""

import numpy as np

from ..config import STEP
from ..utils import _rolling
from .ageing import MIN_TREND_SPAN, MIN_TREND_VALUES, MIN_VALUES, Z90, robust_linfit

SKIP_START_S = 30.0   # take-off roll and climb-out (nose-wheel steering, gear)
SKIP_END_S = 45.0     # approach and landing
MIN_ALT_M = 15.0
MAX_LAG_S = 2.0       # largest delay stick -> receiver current that is searched
MIN_AIRBORNE_S = 120.0  # airborne time needed for a value
MIN_CHANGE_A = 0.10   # smallest change over the period that counts as a rise or fall at all

# why a flight has no value (codes; labels in config.RX_BASE_LABELS)
REASONS = ("no_rx", "no_sticks", "few_data")


def airborne_mask(t, alt=None):
    """Samples counted as airborne: without take-off/landing phases and above MIN_ALT_M if altitude is known."""
    t = np.asarray(t, dtype=float)
    m = (t - t[0] > SKIP_START_S) & (t[-1] - t > SKIP_END_S)
    if alt is not None:
        alt = np.asarray(alt, dtype=float)
        m &= np.where(np.isfinite(alt), alt > MIN_ALT_M, False)
    return m


def _design(sticks):
    """Columns 1, |deflection| and |stick speed| per stick (deflection in fractions of full travel)."""
    cols = []
    for s in sticks.values():
        s = np.asarray(s, dtype=float) / 100.0
        cols.append(_rolling(np.abs(s), 3))            # smoothed like the receiver current
        cols.append(_rolling(np.abs(np.gradient(_rolling(s, 2), STEP)), 3))
    n = len(cols[0])
    return np.column_stack([np.ones(n)] + cols)


def base_current(t, rx, sticks, alt=None):
    """Base current of the receiver for one flight.

    t: time [s] on the STEP grid, rx: receiver current [A], sticks: dict code -> stick position [%] (the stick
    channels found in the log), alt: altitude above start [m] or None.
    Returns dict(value, reason, lag_s, airborne_s); value is NaN with a reason code ("no_rx", "no_sticks",
    "few_data") if there is no value.
    """
    out = dict(value=np.nan, reason="", lag_s=np.nan, airborne_s=0.0)
    if rx is None or not np.any(np.isfinite(rx)) or np.nanmax(rx) <= 0:
        out["reason"] = "no_rx"
        return out
    if not sticks:
        out["reason"] = "no_sticks"
        return out
    rs = _rolling(np.asarray(rx, dtype=float), 3)   # the receiver current is only updated about every 0.5 s
    X = _design(sticks)
    air = airborne_mask(t, alt) & np.all(np.isfinite(X), axis=1)
    best = None
    for sh in range(0, int(round(MAX_LAG_S / STEP)) + 1):
        y = np.full(len(rs), np.nan)
        y[:len(rs) - sh] = rs[sh:]
        m = air & np.isfinite(y)
        if m.sum() * STEP < MIN_AIRBORNE_S:
            continue
        coef = np.linalg.lstsq(X[m], y[m], rcond=None)[0]
        var = float(np.var(y[m]))
        r2 = 1.0 - float(np.var(y[m] - X[m] @ coef)) / var if var > 0 else -np.inf
        if best is None or r2 > best[0]:
            best = (r2, sh, m, y)
    if best is None:
        out["reason"] = "few_data"
        out["airborne_s"] = float(air.sum() * STEP)
        return out
    _, sh, m, y = best
    coef, *_ = robust_linfit(X[m], y[m])
    out.update(value=float(coef[0]), lag_s=sh * STEP, airborne_s=float(m.sum() * STEP))
    return out


def base_trend(x, y):
    """Robust line through the base currents over the flight numbers x.

    Returns dict(status, ...): status "too_few" with fewer than MIN_VALUES values. Otherwise:
      n, first, last, level, level_lo, level_hi (robust mean with 90 % range),
      slope, slope_lo, slope_hi (A per flight; NaN without trend fit), change (A over the period),
      trend ("up", "down", "none"), reliable (trend shown), start, current (shown values: line or level),
      band_x, band_lo, band_hi (90 % range of what is shown, for the chart).
    A trend is only fitted with MIN_TREND_VALUES values spread over MIN_TREND_SPAN flights, and only shown
    when the 90 % range of the slope excludes zero and the change is at least MIN_CHANGE_A.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    n = len(y)
    if n < MIN_VALUES:
        return dict(status="too_few", n=n)
    first, last = float(x.min()), float(x.max())
    lv, lcov, *_ = robust_linfit(np.ones((n, 1)), y)
    level = float(lv[0])
    level_se = float(np.sqrt(lcov[0, 0])) if np.isfinite(lcov[0, 0]) else np.nan
    out = dict(status="ok", n=n, first=first, last=last, level=level,
               level_lo=level - Z90 * level_se, level_hi=level + Z90 * level_se,
               slope=np.nan, slope_lo=np.nan, slope_hi=np.nan, change=np.nan, trend="none", reliable=False)
    coef = cov = None
    if n >= MIN_TREND_VALUES and last - first >= MIN_TREND_SPAN:
        xc = x - last
        coef, cov, *_ = robust_linfit(np.column_stack([np.ones(n), xc]), y)
        se = float(np.sqrt(cov[1, 1])) if np.isfinite(cov[1, 1]) else np.nan
        slope = float(coef[1])
        out.update(slope=slope, slope_lo=slope - Z90 * se, slope_hi=slope + Z90 * se, change=slope * (last - first))
        big = abs(out["change"]) >= MIN_CHANGE_A
        if big and out["slope_lo"] > 0:
            out["trend"] = "up"
        elif big and out["slope_hi"] < 0:
            out["trend"] = "down"
    out["reliable"] = out["trend"] != "none"
    bx = np.linspace(first, last, 50)
    if out["reliable"]:
        xc = bx - last
        mid = coef[0] + coef[1] * xc
        var = cov[0, 0] + xc ** 2 * cov[1, 1] + 2 * xc * cov[0, 1]
        half = Z90 * np.sqrt(np.maximum(var, 0))
        out.update(current=float(coef[0]), start=float(coef[0] + coef[1] * (first - last)),
                   band_x=bx, band_lo=mid - half, band_hi=mid + half)
    else:
        out.update(current=level, start=level, band_x=bx, band_lo=np.full(len(bx), out["level_lo"]),
                   band_hi=np.full(len(bx), out["level_hi"]))
    return out
