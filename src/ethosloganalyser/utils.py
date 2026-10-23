# -*- coding: utf-8 -*-
"""Small helpers for numbers, smoothing, trends and formatting."""

import numpy as np
import pandas as pd


def _nanmin(vals):
    v = [x for x in vals if np.isfinite(x)]
    return float(min(v)) if v else np.nan


def _nanmax(vals):
    v = [x for x in vals if np.isfinite(x)]
    return float(max(v)) if v else np.nan


def _rolling(a, n, how="mean"):
    s = pd.Series(a).rolling(n, min_periods=1, center=True)
    return (s.median() if how == "median" else s.mean()).to_numpy()


def _f(v, fmt="{:.0f}", na="–"):
    """Format a number, NaN/None as a dash."""
    try:
        return fmt.format(v) if v is not None and np.isfinite(v) else na
    except (TypeError, ValueError):
        return na


def _col(df, name):
    return df[name].to_numpy(dtype=float) if name in df.columns else np.full(len(df), np.nan)


def _ranges(nums):
    """[1,2,3,5,7,8] -> '1-3, 5, 7-8'"""
    nums = sorted(int(n) for n in nums)
    out, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append(f"{start}" if start == prev else f"{start}-{prev}")
            start = prev = n
    if start is not None:
        out.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ", ".join(out)


def _trend(x, y):
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3 or np.ptp(x[m]) == 0:
        return None
    s, b = np.polyfit(x[m], y[m], 1)
    return s, b


def fmt_duration(s, unit=False, na="–"):
    """Duration in seconds as min:s, from one hour on as h:min:s - the one time format of the app.

    Rounded to whole seconds first (59.9 s -> "1:00"). Negative values get a leading minus, missing values
    (None, NaN, inf, non-numbers) become na. unit=True appends " min" or " h".
    Examples: 0 -> "0:00", 75 -> "1:15", 3599 -> "59:59", 3600 -> "1:00:00".
    """
    try:
        v = float(s)
    except (TypeError, ValueError):
        return na
    if not np.isfinite(v):
        return na
    sign = "-" if v < 0 and round(abs(v)) > 0 else ""
    total = int(round(abs(v)))
    h, rest = divmod(total, 3600)
    m, sec = divmod(rest, 60)
    if h:
        txt = f"{sign}{h}:{m:02d}:{sec:02d}"
        return txt + " h" if unit else txt
    txt = f"{sign}{m}:{sec:02d}"
    return txt + " min" if unit else txt


def _mmss(s):
    """Duration with unit for running text, e.g. "8:58 min" (see fmt_duration)."""
    return fmt_duration(s, unit=True)


def _window_change(df, col, k):
    v = df[col].to_numpy(dtype=float)
    v = v[np.isfinite(v)]
    if len(v) < 4:
        return None
    return float(np.median(v[:k])), float(np.median(v[-k:]))
