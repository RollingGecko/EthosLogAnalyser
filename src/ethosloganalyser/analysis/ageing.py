# -*- coding: utf-8 -*-
"""One robust method for state of health, ageing trend and forecast.

Every ageing metric (estimated capacity, internal resistance, voltage at reference load) is described by one
robust straight line over the flight number::

    y = current + slope * (flight - last_flight) [+ depth_coef * (depth - depth_ref)]

fitted with Huber weights (iteratively reweighted least squares), so single outliers and single start flights
do not move it. The start value, the current value, the trend and the forecast all come from this one line,
so they cannot contradict each other. The 90 % range of the slope decides whether there is a trend at all;
without a significant ageing trend, or with too few or too scattered values, no forecast is made and the
reason is returned instead.

The capacity estimate depends on the depth of discharge of the flight (the resting-voltage curve is only an
approximation). If this dependency is significant, it is estimated together with the trend and the capacity
is reported at the median depth of the analysed flights.
"""

import numpy as np

Z90 = 1.645            # two-sided 90 % range
HUBER_K = 1.345        # Huber tuning constant (95 % efficiency for normal residuals)
OUTLIER_Z = 3.5        # |residual| / scale above which a value is ignored completely

# minimum number of valid values for start/current value, and for a trend/forecast
MIN_VALUES = 6
MIN_TREND_VALUES = 10
MIN_TREND_SPAN = 10            # flights between the first and the last valid value
# relative scatter (robust residual SD / current value) above which no forecast is made
MAX_REL_SCATTER = {"capacity": 0.06, "ri": 0.15, "u_ref": 0.03}


def _mad_scale(r):
    r = r[np.isfinite(r)]
    if len(r) == 0:
        return np.nan
    return float(np.median(np.abs(r - np.median(r)))) * 1.4826


def robust_linfit(X, y, iters=30):
    """Huber IRLS fit of y = X @ coef. Returns (coef, cov, resid, weights, scale)."""
    w = np.ones(len(y))
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    scale = np.nan
    for _ in range(iters):
        r = y - X @ coef
        scale = _mad_scale(r[w > 0]) if np.any(w > 0) else np.nan
        if not np.isfinite(scale) or scale <= 0:
            scale = float(np.std(r)) or 1e-12
        u = np.abs(r) / scale
        w_new = np.where(u <= HUBER_K, 1.0, HUBER_K / np.maximum(u, 1e-12))
        w_new[u > OUTLIER_Z] = 0.0
        if w_new.sum() < X.shape[1] + 2:
            break
        sw = np.sqrt(w_new)
        coef_new = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]
        done = np.allclose(coef_new, coef, rtol=1e-9, atol=1e-12) and np.array_equal(w_new > 0, w > 0)
        coef, w = coef_new, w_new
        if done:
            break
    r = y - X @ coef
    used = w > 0
    dof = max(int(used.sum()) - X.shape[1], 1)
    s2 = float(np.sum(w[used] * r[used] ** 2) / dof)
    try:
        cov = s2 * np.linalg.inv((X[used] * w[used, None]).T @ X[used])
    except np.linalg.LinAlgError:
        cov = np.full((X.shape[1], X.shape[1]), np.nan)
    return coef, cov, r, w, scale


def ageing_model(df, col, kind, depth_col=None):
    """Robust start value, current value and trend of an ageing metric.

    Returns a dict; "status" is "ok" or the reason code why nothing can be said ("too_few").
    Keys (status ok): n, first, last (flight numbers), start, current, se_current, slope, slope_lo, slope_hi,
    trend ("up", "down" or "none"), rel_scatter, depth_coef, depth_ref, outliers (flight numbers), normed
    (values corrected to depth_ref, aligned with df).
    """
    x = df["Flug"].to_numpy(dtype=float)
    y = df[col].to_numpy(dtype=float) if col in df.columns else np.full(len(df), np.nan)
    d = df[depth_col].to_numpy(dtype=float) if depth_col and depth_col in df.columns else np.full(len(df), np.nan)
    m = np.isfinite(x) & np.isfinite(y)
    n = int(m.sum())
    out = dict(kind=kind, col=col, n=n)
    if n < MIN_VALUES:
        out["status"] = "too_few"
        return out
    xm, ym = x[m], y[m]
    x_first, x_last = float(xm.min()), float(xm.max())
    xc = xm - x_last
    use_trend = n >= MIN_TREND_VALUES and (x_last - x_first) >= MIN_TREND_SPAN

    # depth of discharge as a second regressor, only if it varies and its effect is significant
    depth_coef, depth_ref = 0.0, np.nan
    if depth_col is not None and np.all(np.isfinite(d[m])) and n >= MIN_TREND_VALUES and np.std(d[m]) >= 5:
        depth_ref = float(np.median(d[m]))
        cols = [np.ones(n), xc, d[m] - depth_ref] if use_trend else [np.ones(n), d[m] - depth_ref]
        X = np.column_stack(cols)
        coef, cov, *_ = robust_linfit(X, ym)
        se = np.sqrt(cov[-1, -1]) if np.isfinite(cov[-1, -1]) else np.nan
        if np.isfinite(se) and se > 0 and abs(coef[-1]) / se >= 2.0:
            depth_coef = float(coef[-1])
    y_n = ym - depth_coef * (d[m] - depth_ref) if depth_coef else ym

    if use_trend:
        X = np.column_stack([np.ones(n), xc])
        coef, cov, r, w, scale = robust_linfit(X, y_n)
        current, slope = float(coef[0]), float(coef[1])
        se_cur = float(np.sqrt(cov[0, 0])) if np.isfinite(cov[0, 0]) else np.nan
        se_sl = float(np.sqrt(cov[1, 1])) if np.isfinite(cov[1, 1]) else np.nan
        start = current + slope * (x_first - x_last)
    else:          # no trend: robust level only (Huber location)
        X = np.ones((n, 1))
        coef, cov, r, w, scale = robust_linfit(X, y_n)
        current = start = float(coef[0])
        se_cur = float(np.sqrt(cov[0, 0])) if np.isfinite(cov[0, 0]) else np.nan
        slope, se_sl = 0.0, np.nan

    lo, hi = (slope - Z90 * se_sl, slope + Z90 * se_sl) if np.isfinite(se_sl) else (np.nan, np.nan)
    trend = "none"
    if use_trend and np.isfinite(lo):
        trend = "down" if hi < 0 else ("up" if lo > 0 else "none")
    normed = np.full(len(df), np.nan)
    normed[m] = y_n
    out.update(status="ok", first=x_first, last=x_last, start=start, current=current, se_current=se_cur,
               slope=slope, slope_lo=lo, slope_hi=hi, trend=trend, trend_possible=use_trend,
               rel_scatter=float(scale / abs(current)) if current else np.nan,
               depth_coef=depth_coef, depth_ref=depth_ref,
               outliers=sorted(int(v) for v in xm[w == 0]), normed=normed)
    return out


def forecast(model, threshold, ageing_direction):
    """Flights until the fitted line reaches threshold.

    ageing_direction: "down" (capacity falls with age) or "up" (internal resistance rises).
    Returns dict(status="ok", flights, lo, hi) or dict(status=<reason code>): "too_few", "too_scattered",
    "no_trend" (90 % range includes zero), "improving" (significant trend against the ageing direction),
    "reached" (threshold already reached, flights = 0).
    """
    if model.get("status") != "ok":
        return dict(status="too_few", n=model.get("n", 0))
    if not model["trend_possible"]:
        return dict(status="too_few", n=model["n"])
    if model["rel_scatter"] > MAX_REL_SCATTER.get(model["kind"], 0.1):
        return dict(status="too_scattered", scatter=model["rel_scatter"])
    sign = -1.0 if ageing_direction == "down" else 1.0
    if (sign * (model["current"] - threshold)) >= 0:
        return dict(status="reached", flights=0.0)
    if model["trend"] == "none":
        return dict(status="no_trend")
    if model["trend"] != ageing_direction:
        return dict(status="improving")
    gap = threshold - model["current"]
    flights = gap / model["slope"]
    # the steeper end of the 90 % range gives the shorter remaining life
    steep, flat = (model["slope_lo"], model["slope_hi"]) if ageing_direction == "down" else \
        (model["slope_hi"], model["slope_lo"])
    return dict(status="ok", flights=float(flights), lo=float(gap / steep), hi=float(gap / flat))


def battery_mix(values, min_n=20):
    """Hint at several batteries: do the (trend-free) capacity values form two separate groups?

    Uses the bimodality coefficient (> 0.555 points to two modes) together with a two-group split in which both
    groups hold at least 20 % of the flights and are clearly separated (Ashman's D > 3).
    Returns dict(low, high, n_low, n_high) or None.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    n = len(v)
    if n < min_n or np.std(v) == 0:
        return None
    z = (v - v.mean()) / v.std()
    skew, kurt = float(np.mean(z ** 3)), float(np.mean(z ** 4) - 3)
    bc = (skew ** 2 + 1) / (kurt + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))
    c = np.percentile(v, [25, 75]).astype(float)
    lab = np.zeros(n, dtype=int)
    for _ in range(50):
        lab = np.abs(v[:, None] - c[None, :]).argmin(1)
        if lab.min() == lab.max():
            return None
        c_new = np.array([v[lab == 0].mean(), v[lab == 1].mean()])
        if np.allclose(c_new, c):
            break
        c = c_new
    n0, n1 = int((lab == 0).sum()), int((lab == 1).sum())
    sd = np.sqrt((v[lab == 0].var() + v[lab == 1].var()) / 2)
    ashman = abs(c[1] - c[0]) / sd if sd > 0 else np.inf
    if bc > 0.555 and min(n0, n1) >= 0.2 * n and ashman > 3:
        lo, hi = (0, 1) if c[0] < c[1] else (1, 0)
        return dict(low=float(c[lo]), high=float(c[hi]), n_low=(n0, n1)[lo], n_high=(n0, n1)[hi])
    return None
