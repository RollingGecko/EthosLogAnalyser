# -*- coding: utf-8 -*-
"""One robust method for state of health, ageing trend and forecast.

Every ageing metric (estimated capacity, internal resistance, voltage at reference load) is described by one
robust straight line over the flight number::

    y = current + slope * (flight - last_flight)

fitted with Huber weights (iteratively reweighted least squares). Huber weights only limit the influence of
large residuals; no value is thrown away by the fit, so low values at the end of the series that follow the
trend stay in (measurement errors are removed beforehand, see quality.py). The 90 % range of the slope decides
whether there is a trend at all.

The line is only *shown* (start value, current value, forecast) when the trend is significant and plausible.
Otherwise the metric is reported as its robust mean level over the period ("no confirmed change"), so a
non-significant or implausible slope never appears as a rising or falling value. Implausible means:

* capacity_rising - a significantly rising capacity (a battery does not gain capacity),
* contradicts_u_ref - capacity and voltage at reference load point in different directions
  (see check_consistency),
* depth_confounded - the depth of discharge changes over the period and its effect could not be separated
  from the ageing trend (see below).

Depth of discharge: the capacity estimate (drawn charge / state-of-charge drop from the resting-voltage curve)
depends on how deep a flight went. This bias must not be estimated from the same time series as the trend:
when later flights are deeper, a joint fit cannot tell the bias from ageing and takes the trend with it. The
bias is therefore estimated only from flights of the same day (same battery age): the capacity differences
within a day are regressed on the depth differences within that day. The capacity is then reported at the
median depth of the analysed flights.
"""

import numpy as np

Z90 = 1.645            # two-sided 90 % range
HUBER_K = 1.345        # Huber tuning constant (95 % efficiency for normal residuals)
OUTLIER_Z = 3.5        # |residual| / scale above which a value is listed as strongly down-weighted

# minimum number of valid values for start/current value, and for a trend/forecast
MIN_VALUES = 6
MIN_TREND_VALUES = 10
MIN_TREND_SPAN = 10            # flights between the first and the last valid value
# relative scatter (robust residual SD / current value) above which no forecast is made
MAX_REL_SCATTER = {"capacity": 0.06, "ri": 0.15, "u_ref": 0.03}

# depth of discharge: within-day estimate of its effect on the capacity estimate
MIN_DEPTH_SESSIONS = 3         # days with at least two valid flights
MIN_DEPTH_PAIRS = 6            # flights in those days minus the number of days
MIN_DEPTH_SPREAD = 5.0         # percentage points of depth variation needed at all
CONFOUND_CORR = 0.3            # |corr(depth, flight)| above which an uncorrected depth effect may fake a trend

# reasons why a trend is not shown (codes; labels in report.text)
UNCERTAIN_CODES = ("capacity_rising", "contradicts_u_ref", "depth_confounded")


def _mad_scale(r):
    r = r[np.isfinite(r)]
    if len(r) == 0:
        return np.nan
    return float(np.median(np.abs(r - np.median(r)))) * 1.4826


def robust_linfit(X, y, iters=50):
    """Huber IRLS fit of y = X @ coef. Returns (coef, cov, resid, weights, scale)."""
    w = np.ones(len(y))
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    scale = np.nan
    for _ in range(iters):
        r = y - X @ coef
        scale = _mad_scale(r)
        if not np.isfinite(scale) or scale <= 0:
            scale = float(np.std(r)) or 1e-12
        u = np.abs(r) / scale
        w = np.where(u <= HUBER_K, 1.0, HUBER_K / np.maximum(u, 1e-12))
        sw = np.sqrt(w)
        coef_new = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]
        done = np.allclose(coef_new, coef, rtol=1e-9, atol=1e-12)
        coef = coef_new
        if done:
            break
    r = y - X @ coef
    dof = max(len(y) - X.shape[1], 1)
    s2 = float(np.sum(w * r ** 2) / dof)
    try:
        cov = s2 * np.linalg.inv((X * w[:, None]).T @ X)
    except np.linalg.LinAlgError:
        cov = np.full((X.shape[1], X.shape[1]), np.nan)
    return coef, cov, r, w, scale


def depth_effect(y, depth, session):
    """Effect of the depth of discharge on y [unit per percentage point], from flights of the same day only.

    Capacity and depth are centred per session (day); the slope of the centred values cannot contain ageing,
    because all flights of one day have the same battery age. Returns dict(coef, se, n, sessions) or None if
    there are too few days with several flights or too little depth variation within them.
    """
    y, depth, session = np.asarray(y, float), np.asarray(depth, float), np.asarray(session)
    ok = np.isfinite(y) & np.isfinite(depth)
    y, depth, session = y[ok], depth[ok], session[ok]
    if len(y) == 0:
        return None
    keys, inv, counts = np.unique(session, return_inverse=True, return_counts=True)
    multi = counts[inv] >= 2
    if (counts >= 2).sum() < MIN_DEPTH_SESSIONS:
        return None
    y, depth = y[multi], depth[multi]
    inv = np.unique(inv[multi], return_inverse=True)[1]     # renumber the remaining days 0..k-1
    k = int(inv.max()) + 1
    if len(y) - k < MIN_DEPTH_PAIRS:
        return None
    mean = lambda v: (np.bincount(inv, v) / np.bincount(inv))[inv]
    dc, yc = depth - mean(depth), y - mean(y)
    sxx = float(np.sum(dc ** 2))
    if sxx <= 0 or np.std(dc) < 1.0:
        return None
    coef = float(np.sum(dc * yc) / sxx)
    r = yc - coef * dc
    dof = max(len(y) - k - 1, 1)
    se = float(np.sqrt(np.sum(r ** 2) / dof / sxx))
    return dict(coef=coef, se=se, n=int(len(y)), sessions=int(k))


def _line(xc, y):
    """Robust line over centred flight numbers: (current, slope, se_current, se_slope, resid, weights, scale)."""
    X = np.column_stack([np.ones(len(y)), xc])
    coef, cov, r, w, scale = robust_linfit(X, y)
    se = lambda i: float(np.sqrt(cov[i, i])) if np.isfinite(cov[i, i]) else np.nan
    return float(coef[0]), float(coef[1]), se(0), se(1), r, w, scale


def _slope_range(slope, se):
    if not np.isfinite(se):
        return np.nan, np.nan
    return slope - Z90 * se, slope + Z90 * se


def finalize(model):
    """Decide whether the fitted line is shown and set start/current accordingly (see module docstring)."""
    if model.get("status") != "ok":
        return model
    uncertain = list(dict.fromkeys(model.get("uncertain", [])))
    if model["kind"] == "capacity" and model["trend"] == "up" and "capacity_rising" not in uncertain:
        uncertain.append("capacity_rising")
    model["uncertain"] = uncertain
    model["reliable"] = model["trend"] in ("up", "down") and not uncertain
    if model["reliable"]:
        model["current"] = model["fit_current"]
        model["start"] = model["fit_current"] + model["slope"] * (model["first"] - model["last"])
        model["se_current"] = model["fit_se_current"]
    else:
        model["current"] = model["start"] = model["level"]
        model["se_current"] = model["level_se"]
    return model


def ageing_model(df, col, kind, depth_col=None, session_col=None, use=None):
    """Robust start value, current value and trend of an ageing metric.

    depth_col/session_col: depth of discharge [%] and day of the flight; the depth effect is estimated within
    days (see depth_effect) and removed. use: optional boolean array of flights that may enter the model
    (e.g. no short flights).

    Returns a dict; "status" is "ok" or the reason code why nothing can be said ("too_few").
    Keys (status ok): n, first, last (flight numbers), start, current, se_current (the shown values: line if
    reliable, otherwise the level), level, slope, slope_lo, slope_hi (the fitted trend), trend ("up", "down"
    or "none"), reliable, uncertain (codes), trend_possible, rel_scatter, depth_coef, depth_se, depth_ref,
    depth_method ("day", "none"), depth_days, depth_corr, sensitivity, outliers (strongly down-weighted
    flight numbers),
    normed (values corrected to depth_ref, aligned with df).
    """
    x = df["Flug"].to_numpy(dtype=float)
    y = df[col].to_numpy(dtype=float) if col in df.columns else np.full(len(df), np.nan)
    d = df[depth_col].to_numpy(dtype=float) if depth_col and depth_col in df.columns else np.full(len(df), np.nan)
    m = np.isfinite(x) & np.isfinite(y)
    if use is not None:
        m &= np.asarray(use, dtype=bool)
    n = int(m.sum())
    out = dict(kind=kind, col=col, n=n)
    if n < MIN_VALUES:
        out["status"] = "too_few"
        return out
    xm, ym = x[m], y[m]
    x_first, x_last = float(xm.min()), float(xm.max())
    xc = xm - x_last
    use_trend = n >= MIN_TREND_VALUES and (x_last - x_first) >= MIN_TREND_SPAN
    uncertain = []

    # depth of discharge: effect estimated within days only, so it cannot absorb the ageing trend
    depth_coef, depth_se, depth_ref, depth_method, depth_corr, depth_days = 0.0, np.nan, np.nan, "none", np.nan, 0
    sensitivity = {}
    dm = d[m]
    if depth_col is not None and np.all(np.isfinite(dm)) and np.std(dm) >= MIN_DEPTH_SPREAD:
        depth_ref = float(np.median(dm))
        depth_corr = float(np.corrcoef(dm, xm)[0, 1]) if np.std(xm) > 0 else np.nan
        sess = df[session_col].to_numpy()[m] if session_col and session_col in df.columns else None
        eff = depth_effect(ym, dm, sess) if sess is not None else None
        if eff is not None and eff["coef"] < 0 and abs(eff["coef"]) >= 2.0 * eff["se"]:
            depth_coef, depth_se, depth_method, depth_days = eff["coef"], eff["se"], "day", eff["sessions"]
        elif eff is not None:
            depth_se = eff["se"]
        if depth_method == "none" and use_trend and np.isfinite(depth_corr) and abs(depth_corr) >= CONFOUND_CORR \
                and eff is None:
            uncertain.append("depth_confounded")
        if use_trend:          # how the trend depends on the depth correction (for transparency)
            for name, coef_ in (("none", 0.0), ("day", eff["coef"] if eff else np.nan)):
                if np.isfinite(coef_):
                    c, s, _, se_s, *_ = _line(xc, ym - coef_ * (dm - depth_ref))
                    sensitivity[name] = dict(depth_coef=coef_, slope=s, slope_lo=s - Z90 * se_s, slope_hi=s + Z90 * se_s)
            Xj = np.column_stack([np.ones(n), xc, dm - depth_ref])
            cj, covj, *_ = robust_linfit(Xj, ym)
            se_j = float(np.sqrt(covj[1, 1])) if np.isfinite(covj[1, 1]) else np.nan
            sensitivity["joint"] = dict(depth_coef=float(cj[2]), slope=float(cj[1]),
                                        slope_lo=float(cj[1] - Z90 * se_j), slope_hi=float(cj[1] + Z90 * se_j))
    y_n = ym - depth_coef * (dm - depth_ref) if depth_coef else ym

    # robust level (mean over the period) and, if possible, the trend line
    lres = robust_linfit(np.ones((n, 1)), y_n)
    level = float(lres[0][0])
    level_se = float(np.sqrt(lres[1][0, 0])) if np.isfinite(lres[1][0, 0]) else np.nan
    if use_trend:
        current, slope, se_cur, se_sl, r, w, scale = _line(xc, y_n)
    else:
        current, slope, se_cur, se_sl = level, 0.0, level_se, np.nan
        r, w, scale = lres[2], lres[3], lres[4]

    lo, hi = _slope_range(slope, se_sl)
    trend = "none"
    if use_trend and np.isfinite(lo):
        trend = "down" if hi < 0 else ("up" if lo > 0 else "none")
    normed = np.full(len(df), np.nan)
    normed[m] = y_n
    strong = np.abs(r) / scale > OUTLIER_Z if np.isfinite(scale) and scale > 0 else np.zeros(n, dtype=bool)
    out.update(status="ok", first=x_first, last=x_last, level=level, level_se=level_se,
               fit_current=current, fit_se_current=se_cur,
               slope=slope, slope_lo=lo, slope_hi=hi, trend=trend, trend_possible=use_trend,
               rel_scatter=float(scale / abs(level)) if level else np.nan,
               depth_coef=depth_coef, depth_se=depth_se, depth_ref=depth_ref, depth_method=depth_method,
               depth_days=depth_days, depth_corr=depth_corr, sensitivity=sensitivity, uncertain=uncertain,
               weights=dict(zip((int(v) for v in xm), (float(v) for v in w))),
               outliers=sorted(int(v) for v in xm[strong]), normed=normed)
    return finalize(out)


def check_consistency(cap, u_ref):
    """Capacity and voltage at reference load must not point in different directions.

    Both describe the same ageing (less capacity, lower voltage under load). If one has a significant trend and
    the other a different direction (the opposite one, or no trend), the capacity statement is marked as
    uncertain ("contradicts_u_ref") and shown without trend. Returns the (updated) capacity model.
    """
    if cap.get("status") != "ok" or u_ref.get("status") != "ok":
        return cap
    if not (cap["trend_possible"] and u_ref["trend_possible"]):
        return cap
    if cap["trend"] != u_ref["trend"] and "down" in (cap["trend"], u_ref["trend"]):
        cap["uncertain"] = cap["uncertain"] + ["contradicts_u_ref"]
        cap["u_ref_trend"] = u_ref["trend"]
        finalize(cap)
    return cap


def forecast(model, threshold, ageing_direction):
    """Flights until the shown line reaches threshold.

    ageing_direction: "down" (capacity falls with age) or "up" (internal resistance rises).
    Returns dict(status="ok", flights, lo, hi) or dict(status=<reason code>): "too_few", "too_scattered",
    "uncertain" (trend implausible, see module docstring), "no_trend" (90 % range includes zero), "improving"
    (significant trend against the ageing direction), "reached" (threshold already reached, flights = 0).
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
    if model.get("uncertain"):
        return dict(status="uncertain", codes=list(model["uncertain"]))
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
