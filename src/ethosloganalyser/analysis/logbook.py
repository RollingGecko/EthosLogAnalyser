# -*- coding: utf-8 -*-
"""Flight logbook: totals over the flights of one analysis (tab "Logbook").

Input is the flight table of an analysis (``Result.df``: one model, already limited by the period filter).
The duration is the log duration (column ``dauer_s``, motor armed until disarmed), not an airborne time.
The functions only read the table, so later views (selection by year/month, totals per battery) can reuse them.
In the logbook the table comes from the flight database (db/logbook_table.py) and holds several aircraft; its
flight numbers count per aircraft, so the longest and shortest flight also name their aircraft.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# columns of the flight list, in display order
FLIGHT_COLS = ["Flug", "datum", "dauer_s", "entnommen_mAh"]
# columns of the tables per year and per month
PERIOD_COLS = ["Fluege", "dauer_s", "Flugtage", "entnommen_mAh"]


@dataclass
class Logbook:
    n_flights: int = 0                 # flights in the table
    n_counted: int = 0                 # flights with date and duration (used for all totals)
    n_missing: int = 0                 # flights without date or duration (left out of the totals)
    total_s: float = 0.0               # sum of the log durations [s]
    flight_days: int = 0               # different calendar days with at least one flight
    longest: dict = field(default_factory=dict)    # {"Flug", "datum", "dauer_s", "aircraft"} or {} without flights
    shortest: dict = field(default_factory=dict)
    mah_total: float = 0.0             # drawn charge of the flights with a valid battery value [mAh]
    n_mah: int = 0                     # flights counted in mah_total
    first: object = None               # date of the first and the last counted flight
    last: object = None
    per_year: pd.DataFrame = None      # index year; columns PERIOD_COLS
    per_month: pd.DataFrame = None     # index (year, month); columns PERIOD_COLS
    flights: pd.DataFrame = None       # FLIGHT_COLS, all flights (also those with missing values)


def _valid_mah(df):
    """Drawn charge per flight, NaN where the battery values of the flight are invalid (measurement error).

    The same rule as the summary ("total drawn"): flights with Akku_gueltig == False do not count.
    """
    mah = pd.to_numeric(df.get("entnommen_mAh", pd.Series(np.nan, index=df.index)), errors="coerce")
    if "Akku_gueltig" in df:
        mah = mah.where(df["Akku_gueltig"].fillna(False).astype(bool))
    return mah.where(np.isfinite(mah))


def _period_table(d, keys):
    """Flights, duration, flight days and drawn charge per period (keys: list of grouping columns)."""
    if d.empty:
        idx = pd.MultiIndex.from_tuples([], names=keys) if len(keys) > 1 else pd.Index([], name=keys[0])
        return pd.DataFrame({c: pd.Series(dtype=float) for c in PERIOD_COLS}, index=idx)
    g = d.groupby(keys)
    out = pd.DataFrame({
        "Fluege": g.size(),
        "dauer_s": g["dauer_s"].sum(),
        "Flugtage": g["_day"].nunique(),
        "entnommen_mAh": g["_mah"].sum(min_count=1),
    })
    return out.sort_index()


def logbook(df):
    """Totals of the flight table df (see module doc). Robust against an empty table and missing values."""
    lb = Logbook()
    if df is None or df.empty:
        lb.per_year = _period_table(pd.DataFrame(), ["Jahr"])
        lb.per_month = _period_table(pd.DataFrame(), ["Jahr", "Monat"])
        lb.flights = pd.DataFrame(columns=FLIGHT_COLS)
        return lb

    d = pd.DataFrame(index=df.index)
    d["Flug"] = df["Flug"] if "Flug" in df else np.arange(1, len(df) + 1)
    d["datum"] = pd.to_datetime(df.get("datum"), errors="coerce")
    d["dauer_s"] = pd.to_numeric(df.get("dauer_s"), errors="coerce")
    d["entnommen_mAh"] = pd.to_numeric(df.get("entnommen_mAh"), errors="coerce")
    d["_mah"] = _valid_mah(df)
    d["aircraft"] = df["aircraft"] if "aircraft" in df else None   # flight numbers count per aircraft
    lb.flights = d[FLIGHT_COLS].reset_index(drop=True)
    lb.n_flights = len(d)

    ok = d["datum"].notna() & np.isfinite(d["dauer_s"]) & (d["dauer_s"] >= 0)
    c = d[ok].copy()
    lb.n_counted = len(c)
    lb.n_missing = lb.n_flights - lb.n_counted
    if c.empty:
        lb.per_year = _period_table(pd.DataFrame(), ["Jahr"])
        lb.per_month = _period_table(pd.DataFrame(), ["Jahr", "Monat"])
        return lb

    c["_day"] = c["datum"].dt.normalize()
    c["Jahr"] = c["datum"].dt.year
    c["Monat"] = c["datum"].dt.month
    lb.total_s = float(c["dauer_s"].sum())
    lb.flight_days = int(c["_day"].nunique())
    lb.first, lb.last = c["datum"].min(), c["datum"].max()
    for attr, k in (("longest", c["dauer_s"].idxmax()), ("shortest", c["dauer_s"].idxmin())):
        r = c.loc[k]
        setattr(lb, attr, {"Flug": int(r["Flug"]), "datum": r["datum"], "dauer_s": float(r["dauer_s"]),
                           "aircraft": r["aircraft"]})
    mah = c["_mah"].dropna()
    lb.mah_total = float(mah.sum())
    lb.n_mah = int(len(mah))
    lb.per_year = _period_table(c, ["Jahr"])
    lb.per_month = _period_table(c, ["Jahr", "Monat"])
    return lb
