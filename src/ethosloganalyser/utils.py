# -*- coding: utf-8 -*-
"""Kleine Hilfsfunktionen für Zahlen, Glättung, Trends und Formatierung."""

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
    """Zahl formatieren, NaN/None als Strich."""
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


def _mmss(s):
    return "–" if not np.isfinite(s) else f"{int(s // 60)}:{int(s % 60):02d} min"


def _window_change(df, col, k):
    v = df[col].to_numpy(dtype=float)
    v = v[np.isfinite(v)]
    if len(v) < 4:
        return None
    return float(np.median(v[:k])), float(np.median(v[-k:]))
