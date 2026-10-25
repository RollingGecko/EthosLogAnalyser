# -*- coding: utf-8 -*-
"""Selecting flights by aircraft, year, month and date range (the filter of the logbook).

The functions work on a flight table (``pandas.DataFrame``) with the columns ``aircraft`` (name) and
``datum`` (start of the flight as a timestamp). They only read the table, so any page that shows flights
can use the same filter.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd

MONTHS = tuple(range(1, 13))


@dataclass(frozen=True)
class FlightFilter:
    """Which flights are shown. ``None`` in a field means "no restriction"; all given fields must match."""
    aircraft: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None            # 1..12, in every year unless a year is chosen as well
    date_from: Optional[date] = None       # first day (inclusive)
    date_to: Optional[date] = None         # last day (inclusive)

    @property
    def is_active(self):
        """True if the filter restricts anything."""
        return any(value is not None for value in (self.aircraft, self.year, self.month, self.date_from,
                                                   self.date_to))


def filter_mask(table, flight_filter):
    """Boolean Series: which rows of the table pass the filter."""
    mask = pd.Series(True, index=table.index)
    if flight_filter.aircraft is not None:
        mask &= table["aircraft"] == flight_filter.aircraft
    if flight_filter.year is not None:
        mask &= table["datum"].dt.year == flight_filter.year
    if flight_filter.month is not None:
        mask &= table["datum"].dt.month == flight_filter.month
    if flight_filter.date_from is not None:
        mask &= table["datum"] >= pd.Timestamp(flight_filter.date_from)
    if flight_filter.date_to is not None:
        # inclusive: up to the end of the last day
        mask &= table["datum"] < pd.Timestamp(flight_filter.date_to) + pd.Timedelta(days=1)
    return mask


def apply_filter(table, flight_filter):
    """The rows of the table that pass the filter (same columns, original order)."""
    if not flight_filter.is_active:
        return table
    return table[filter_mask(table, flight_filter)]


def years_in(table):
    """Years with at least one flight, ascending."""
    if table.empty:
        return []
    return sorted(int(year) for year in table["datum"].dt.year.dropna().unique())


def aircraft_in(table):
    """Aircraft names of the table, sorted."""
    if table.empty:
        return []
    return sorted(table["aircraft"].dropna().unique())
