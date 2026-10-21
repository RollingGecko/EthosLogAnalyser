# -*- coding: utf-8 -*-
"""Reading FrSky Ethos logs: encoding, column detection, time axis, switch channels."""

import os
import re
import numpy as np
import pandas as pd
from datetime import datetime


VOLT_KEYS = ["vfas", "ecu", "pack", "voltage", "volt", "(v)"]


CURR_KEYS = ["current", "curr", "amp", "(a)"]


EXCLUDE = ("rx", "tx", "adc", "empf", "esc rpm", "consumption", "rssi", "vfr")   # receiver / transmitter / radio values


def _find_col(columns, keys, override=""):
    low = {c: str(c).lower() for c in columns}
    if override:
        for c, l in low.items():
            if override.lower() in l:
                return c
        return None
    pool = {c: l for c, l in low.items() if not l.startswith(EXCLUDE)}
    for k in keys:
        for c, l in pool.items():
            if k in l:
                return c
    return None


def _to_num(s):
    if not pd.api.types.is_numeric_dtype(s):          # text (object or pandas 3 string dtype): decimal comma
        s = s.astype(str).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _numeric_cols(df, keys, exclude=()):
    """All columns whose name contains one of the keys and that hold values."""
    out = []
    for c in df.columns:
        l = str(c).lower()
        if any(k in l for k in keys) and not any(x in l for x in exclude):
            s = _to_num(df[c])
            if s.notna().sum() > 0:
                out.append((c, s))
    return out


def _first_series(df, keys, exclude=()):
    r = _numeric_cols(df, keys, exclude)
    return r[0][1] if r else None


def _active_series(df, keys, exclude=()):
    """First column with positive values (e.g. RSSI of the receiver actually in use)."""
    r = _numeric_cols(df, keys, exclude)
    for _, s in r:
        if s.max() > 0:
            return s
    return r[0][1] if r else None


def _exact_series(df, names):
    """Column with exactly one of the names (case-insensitive), e.g. stick channels 'QR', 'HR'."""
    want = {n.lower() for n in names}
    for c in df.columns:
        if str(c).strip().lower() in want:
            s = _to_num(df[c])
            if s.notna().sum() > 0:
                return s
    return None


SWITCH_SKIP = ("rx", "vfr", "rssi", "pot", "drehg", "r9m", "adc", "unnamed", "date", "time", "fuel")


def _switch_columns(df):
    """Switches/buttons: columns with values only from {-1, 0, 1} that change at least once in the log."""
    out = []
    for c in df.columns:
        l = str(c).strip().lower()
        if l.startswith(SWITCH_SKIP):
            continue
        s = _to_num(df[c])
        v = s.dropna()
        if len(v) < 20:
            continue
        u = set(np.unique(v.to_numpy()))
        if len(u) >= 2 and u <= {-1.0, 0.0, 1.0}:
            out.append((str(c).strip(), s))
    return out


def _time_seconds(df):
    """Returns time in seconds since the start (float array) or None."""
    cols = {str(c).lower().strip(): c for c in df.columns}
    tcol = next((cols[k] for k in cols if k in ("time", "zeit", "t")), None)
    dcol = next((cols[k] for k in cols if k in ("date", "datum")), None)
    if tcol is None:
        tcol = next((cols[k] for k in cols if "time" in k), None)
    if tcol is None:
        return None
    raw = df[tcol]
    num = _to_num(raw)
    if num.notna().mean() > 0.9:                      # numeric time
        t = num.to_numpy(dtype=float)
        if np.nanmax(t) - np.nanmin(t) > 20000 and "ms" in str(tcol).lower():
            t = t / 1000.0
        return t - np.nanmin(t)
    txt = raw.astype(str).str.strip()
    if dcol is not None:
        txt = df[dcol].astype(str).str.strip() + " " + txt
    dt = pd.to_datetime(txt, errors="coerce", format="mixed")
    if dt.notna().mean() < 0.9:
        return None
    sec = np.array((dt - dt.iloc[0]).dt.total_seconds(), dtype=float)   # writable copy (pandas 3)
    jumps = np.where(np.diff(sec) < -43200)[0]        # midnight wrap-around when only the time of day is logged
    for j in jumps:
        sec[j + 1:] += 86400
    return sec


def _file_datetime(path):
    name = os.path.basename(path)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})[-_ T]?(\d{2})[-_:]?(\d{2})[-_:]?(\d{2})", name)
    if m:
        try:
            return datetime(*map(int, m.groups()))
        except ValueError:
            pass
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)
    if m:
        try:
            return datetime(*map(int, m.groups()))
        except ValueError:
            pass
    return datetime.fromtimestamp(os.path.getmtime(path))


def _clean_name(c):
    """Ethos mixes UTF-8 and code page characters in column names ('Â°', 'au›en') - make them readable."""
    c = str(c).strip()
    for a, b in (("Â°", "°"), ("›", "ß"), ("Ã¤", "ä"), ("Ã¶", "ö"), ("Ã¼", "ü"), ("ÃŸ", "ß")):
        c = c.replace(a, b)
    return c


def read_log(path):
    last = None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):      # Ethos often writes cp1252 (umlauts, °)
        try:
            df = pd.read_csv(path, sep=None, engine="python", encoding=enc)
            df.columns = [_clean_name(c) for c in df.columns]
            return df
        except UnicodeDecodeError as e:
            last = e
    raise last
