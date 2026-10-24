# -*- coding: utf-8 -*-
"""Receiver current per control surface - an estimate, not a measurement.

The log only contains the TOTAL current of the receiver (all servos together). How much of it each control
surface draws can only be estimated statistically from how the sticks were moved. Everything here is such an
estimate with an uncertainty range; callers must present it that way.

Method (details and limits in docs/methodology.md, "Receiver current per control surface"):

1. Regression over the airborne part of the flight::

       I_rx(t + lag) = I_0 + sum_k ( a_k * |deflection_k(t)| + b_k * |stick speed_k(t)| )

   with deflection in fractions of full travel (1 = 100 %) and stick speed in full travels per second.
   a_k is the estimated current per 100 % deflection of surface k (holding the surface against the air
   load), b_k the extra current per 100 %/s stick speed (moving it). The lag between stick and current
   (telemetry delay, about 0.5-1 s on the real logs) is chosen by the best fit. Uncertainty ranges come from
   a moving-block bootstrap (blocks of 10 s), because consecutive samples are not independent.
   Combined manoeuvres in which ALL surfaces are at (nearly) full deflection at the same time (e.g. a spin or
   snap roll) are left out of the regression (+- COMBINED_MARGIN_S): nothing in them tells the surfaces
   apart. They are reported separately with the receiver current they caused - a repeated, comparable load
   across flights.
2. Coupling: if the deflections of two surfaces are strongly correlated (e.g. always aileron and elevator
   together in turns), their contributions cannot be told apart -> status "not_separable".
3. Clean events: periods in which only one surface is deflected and all others are near neutral. They are
   counted per surface as a plausibility check of the regression; with too few of them the regression is the
   only source.
4. Spike -> probable surface: for each receiver current spike, the surface with the largest deflection in the
   window before the spike (shifted by the lag). This is an assignment, not a measurement; "several" if two
   surfaces are deflected about equally, "none" if no surface was deflected noticeably.
5. Across flights: a robust line (Huber, as for battery ageing) through the per-flight estimates of one surface,
   weighted by their uncertainty; a change is only reported when its 90 % range excludes zero.

All codes returned here are language-neutral; user-facing labels live in config.STICK_LABELS and the report.
"""

import numpy as np

from ..config import STEP
from ..utils import _rolling
from .ageing import Z90, robust_linfit

SURFACES = ("aileron", "elevator", "rudder")

MAX_LAG_S = 2.0           # largest delay between stick and receiver current that is searched
SKIP_START_S = 30.0       # take-off roll and climb-out (nose-wheel steering, gear) are left out
SKIP_END_S = 45.0         # approach and landing roll
MIN_ALT_M = 15.0          # below this the model counts as on the ground / in the circuit
ACTIVE_DEFLECTION = 0.25  # deflection (fraction of full travel) above which a surface counts as "used"
NEUTRAL = 0.10            # deflection below which a surface counts as "near neutral"
MIN_ACTIVE_S = 10.0       # seconds of use needed for an estimate of that surface
MIN_CLEAN_EVENTS = 5      # clean events needed for an event-based estimate
COUPLED_R = 0.7           # |correlation| of two deflections above which they are "not separable"
BLOCK_S = 10.0            # block length of the bootstrap
N_BOOT = 200
COMBINED_DEFLECTION = 0.85   # all surfaces at least this deflected at the same time -> combined manoeuvre
COMBINED_MIN_S = 1.0
COMBINED_MARGIN_S = 4.0   # left out of the regression before and after a combined manoeuvre
SPIKE_WINDOW_S = (-1.0, 0.25)   # stick window around (spike time - lag)
SPIKE_MIN_DEFLECTION = 0.30
SPIKE_SEVERAL = 0.8       # second-largest deflection >= this share of the largest -> "several"

# status codes per surface
STATUS = ("ok", "few_data", "not_separable", "missing")


def _shift(a, sh):
    """Value of a at index + sh (NaN where outside)."""
    out = np.full(len(a), np.nan)
    if sh > 0:
        out[:-sh] = a[sh:]
    elif sh < 0:
        out[-sh:] = a[:sh]
    else:
        out[:] = a
    return out


def stick_features(sticks, surfaces=SURFACES):
    """|deflection| [fraction of full travel] and |stick speed| [full travels per second] per surface.

    sticks: dict code -> stick position in % (-100..100) on the STEP grid (series["sticks"]).
    """
    feats = {}
    for k in surfaces:
        s = sticks.get(k)
        if s is None:
            continue
        s = np.asarray(s, dtype=float)
        defl = np.abs(s) / 100.0
        speed = _rolling(np.abs(np.gradient(_rolling(s, 2), STEP)) / 100.0, 3)
        feats[k] = (defl, speed)
    return feats


def airborne_mask(t, alt=None):
    """Samples counted as airborne: without take-off/landing phases and above MIN_ALT_M if altitude is known."""
    t = np.asarray(t, dtype=float)
    m = (t - t[0] > SKIP_START_S) & (t[-1] - t > SKIP_END_S)
    if alt is not None:
        alt = np.asarray(alt, dtype=float)
        m &= np.where(np.isfinite(alt), alt > MIN_ALT_M, False)
    return m


def combined_manoeuvres(defl, keys):
    """Segments (start, end index) in which all surfaces are deflected >= COMBINED_DEFLECTION together."""
    if len(keys) < 2:
        return []
    on = np.all([defl[k] >= COMBINED_DEFLECTION for k in keys], axis=0)
    d = np.diff(np.r_[0, on.astype(int), 0])
    n_min = int(round(COMBINED_MIN_S / STEP))
    return [(s0, s1) for s0, s1 in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)) if s1 - s0 >= n_min]


def _design(feats, keys):
    """Columns: 1, then |deflection| and |stick speed| per surface. The deflection is smoothed like the
    receiver current (3 samples), so both see the same step response."""
    n = len(next(iter(feats.values()))[0])
    cols = [np.ones(n)]
    for k in keys:
        cols += [_rolling(feats[k][0], 3), feats[k][1]]
    return np.column_stack(cols)


def _ols(X, y):
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ coef
    var = float(np.var(y))
    return coef, (1.0 - float(np.var(res)) / var) if var > 0 else np.nan


def _block_bootstrap(X, y, n_boot, block, seed):
    """Coefficients of n_boot moving-block bootstrap samples (rows of X/y in time order)."""
    n = len(y)
    block = max(1, min(block, n))
    starts = np.arange(0, n - block + 1)
    k = int(np.ceil(n / block))
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_boot):
        idx = (rng.choice(starts, k)[:, None] + np.arange(block)[None, :]).ravel()[:n]
        try:
            out.append(np.linalg.lstsq(X[idx], y[idx], rcond=None)[0])
        except np.linalg.LinAlgError:
            continue
    return np.array(out)


def _clean_events(defl, mask, k, keys, min_len=3):
    """Clean events of surface k: k deflected >= ACTIVE_DEFLECTION, all other surfaces near neutral."""
    on = mask & (defl[k] >= ACTIVE_DEFLECTION)
    for j in keys:
        if j != k:
            on &= defl[j] < NEUTRAL
    d = np.diff(np.r_[0, on.astype(int), 0])
    return [(s0, s1) for s0, s1 in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)) if s1 - s0 >= min_len]


def assign_spikes(spike_times, t, defl, lag_s, keys):
    """Probable surface per spike: code of a surface, "several" or "none" (an assignment, not a measurement)."""
    t = np.asarray(t, dtype=float)
    out = []
    for ts in spike_times:
        lo, hi = ts - lag_s + SPIKE_WINDOW_S[0], ts - lag_s + SPIKE_WINDOW_S[1]
        w = (t >= lo) & (t <= hi)
        if not w.any():
            out.append("none")
            continue
        score = sorted(((float(np.max(defl[k][w])), k) for k in keys), reverse=True)
        if not score or score[0][0] < SPIKE_MIN_DEFLECTION:
            out.append("none")
        elif len(score) > 1 and score[1][0] >= SPIKE_MIN_DEFLECTION and score[1][0] >= SPIKE_SEVERAL * score[0][0]:
            out.append("several")
        else:
            out.append(score[0][1])
    return out


def surface_current_analysis(t, rx, sticks, alt=None, spike_times=(), surfaces=SURFACES,
                             max_lag_s=MAX_LAG_S, n_boot=N_BOOT, seed=0):
    """Estimated receiver current per control surface for one flight.

    t: time [s] on the STEP grid, rx: receiver current [A], sticks: dict code -> stick position [%],
    alt: altitude above start [m] or None, spike_times: times of receiver current spikes (same time base as t).
    Returns None if there is no receiver current or no stick channel, otherwise a dict:

      lag_s, r2, n              - delay stick -> current, fit quality, samples used for the fit
      base_a, base_lo, base_hi  - current with all surfaces at neutral and still (intercept), 90 % range
      combined                  - combined manoeuvres (all surfaces near full deflection): t0, t1 and the
                                  receiver current during them (peak_a, median_a); left out of the fit
      coupling                  - {(a, b): correlation of the deflections}
      surfaces[code]            - status ("ok", "few_data", "not_separable", "missing"),
                                  per100 / per100_lo / per100_hi   current per 100 % deflection [A] with 90 % range,
                                  speed / speed_lo / speed_hi      extra current per 100 %/s stick speed [A],
                                  share                            share of the current explained by the surfaces,
                                  active_s, clean_events, clean_per100 (median of clean events or NaN)
      spikes                    - probable surface per spike (see assign_spikes), spike_share {code: share}
    """
    if rx is None or not sticks:
        return None
    t = np.asarray(t, dtype=float)
    rx = np.asarray(rx, dtype=float)
    if not np.any(np.isfinite(rx)) or np.nanmax(rx) <= 0:
        return None
    feats = stick_features(sticks, surfaces)
    keys = [k for k in surfaces if k in feats]
    if not keys:
        return None
    defl = {k: feats[k][0] for k in keys}
    rs = _rolling(rx, 3)                         # the receiver current is only updated about every 0.5 s
    air = airborne_mask(t, alt)
    combined = combined_manoeuvres(defl, keys)
    margin = int(round(COMBINED_MARGIN_S / STEP))
    fit_mask = air.copy()
    for s0, s1 in combined:
        fit_mask[max(0, s0 - margin):s1 + margin] = False
    X = _design(feats, keys)

    best = None
    for sh in range(0, int(round(max_lag_s / STEP)) + 1):
        y = _shift(rs, sh)
        m = fit_mask & np.isfinite(y) & np.all(np.isfinite(X), axis=1)
        if m.sum() < 4 * len(keys) * 2 + 40:
            continue
        coef, r2 = _ols(X[m], y[m])
        if np.isfinite(r2) and (best is None or r2 > best[0]):
            best = (r2, sh, coef, m, y)
    if best is None:
        return None
    r2, sh, coef, m, y = best
    lag_s = sh * STEP
    Xm, ym = X[m], y[m]
    boot = _block_bootstrap(Xm, ym, n_boot, int(round(BLOCK_S / STEP)), seed)
    def q(col):        # 90 % range of a coefficient
        if not len(boot):
            return np.nan, np.nan
        return float(np.percentile(boot[:, col], 5)), float(np.percentile(boot[:, col], 95))

    coupling = {}
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            da, db = defl[a][m], defl[b][m]
            r = float(np.corrcoef(da, db)[0, 1]) if np.std(da) > 0 and np.std(db) > 0 else np.nan
            coupling[(a, b)] = r

    contrib = {k: coef[1 + 2 * i] * Xm[:, 1 + 2 * i] + coef[2 + 2 * i] * Xm[:, 2 + 2 * i] for i, k in enumerate(keys)}
    pos = {k: max(float(np.mean(v)), 0.0) for k, v in contrib.items()}
    tot = sum(pos.values())

    res = {}
    for i, k in enumerate(keys):
        ca, cb = 1 + 2 * i, 2 + 2 * i
        active_s = float(np.sum(defl[k][m] >= ACTIVE_DEFLECTION) * STEP)
        events = _clean_events(defl, m, k, keys)
        slopes = []
        for s0, s1 in events:
            pre = np.arange(max(0, s0 - 8), s0)
            pre = pre[np.all([defl[j][pre] < NEUTRAL for j in keys], axis=0) & np.isfinite(y[pre])] \
                if len(pre) else pre
            seg = y[s0:s1]
            if len(pre) >= 3 and np.all(np.isfinite(seg)):
                slopes.append((float(np.median(seg)) - float(np.median(y[pre]))) / float(np.max(defl[k][s0:s1])))
        max_r = max([abs(r) for (a, b), r in coupling.items() if k in (a, b) and np.isfinite(r)], default=0.0)
        if active_s < MIN_ACTIVE_S:
            status = "few_data"
        elif max_r >= COUPLED_R:
            status = "not_separable"
        else:
            status = "ok"
        lo_a, hi_a = q(ca)
        lo_b, hi_b = q(cb)
        res[k] = dict(status=status, per100=float(coef[ca]), per100_lo=lo_a, per100_hi=hi_a,
                      speed=float(coef[cb]), speed_lo=lo_b, speed_hi=hi_b,
                      share=pos[k] / tot if tot > 0 else np.nan, active_s=active_s,
                      clean_events=len(events),
                      clean_per100=float(np.median(slopes)) if len(slopes) >= MIN_CLEAN_EVENTS else np.nan)
    for k in surfaces:
        if k not in res:
            res[k] = dict(status="missing", per100=np.nan, per100_lo=np.nan, per100_hi=np.nan, speed=np.nan,
                          speed_lo=np.nan, speed_hi=np.nan, share=np.nan, active_s=0.0, clean_events=0,
                          clean_per100=np.nan)

    comb = []
    for s0, s1 in combined:
        seg = y[s0:s1 + sh]
        seg = seg[np.isfinite(seg)]
        if len(seg):
            comb.append(dict(t0=float(t[s0]), t1=float(t[s1 - 1]), peak_a=float(np.max(seg)),
                             median_a=float(np.median(seg))))
    base_lo, base_hi = q(0)

    spikes = assign_spikes(spike_times, t, defl, lag_s, keys)
    share = {}
    if spikes:
        for code in list(keys) + ["several", "none"]:
            share[code] = spikes.count(code) / len(spikes)
    return dict(lag_s=lag_s, r2=float(r2), n=int(m.sum()), base_a=float(coef[0]), base_lo=base_lo,
                base_hi=base_hi, coupling=coupling, surfaces=res, combined=comb, spikes=spikes, spike_share=share)


MIN_TREND_CHANGE_A = 0.10   # smallest change over the period (A per 100 %) that counts as a change at all


def surface_trend(x, values, lo, hi, min_flights=6, min_change=MIN_TREND_CHANGE_A):
    """Robust line through the per-flight estimates of one surface (x: flight number or days).

    Weights 1 / (width of the 90 % range)^2, so uncertain flights count less. Returns None with fewer than
    min_flights usable values, otherwise dict(slope, slope_lo, slope_hi, start, end, n, rising, falling):
    rising / falling only when the 90 % range of the slope excludes zero AND the change between the first and
    the last flight is at least min_change (smaller changes are of no practical use).
    """
    x, v, lo, hi = (np.asarray(a, dtype=float) for a in (x, values, lo, hi))
    ok = np.isfinite(x) & np.isfinite(v) & np.isfinite(lo) & np.isfinite(hi) & (hi > lo)
    if ok.sum() < min_flights:
        return None
    x, v, sd = x[ok], v[ok], (hi[ok] - lo[ok]) / (2 * Z90)
    w = 1.0 / np.maximum(sd, 1e-3)
    xc = x - x[-1]
    X = np.column_stack([np.ones(len(v)), xc])
    coef, cov, *_ = robust_linfit(X * w[:, None], v * w)
    se = float(np.sqrt(cov[1, 1])) if np.isfinite(cov[1, 1]) else np.nan
    slope = float(coef[1])
    s_lo, s_hi = slope - Z90 * se, slope + Z90 * se
    start, end = float(coef[0] + slope * (x[0] - x[-1])), float(coef[0])
    big = abs(end - start) >= min_change
    return dict(slope=slope, slope_lo=s_lo, slope_hi=s_hi, end=end, start=start, n=int(ok.sum()),
                rising=bool(big and np.isfinite(s_lo) and s_lo > 0),
                falling=bool(big and np.isfinite(s_hi) and s_hi < 0))
