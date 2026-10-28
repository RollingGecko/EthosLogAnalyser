# -*- coding: utf-8 -*-
"""Selecting flights by aircraft, year, month and date range (the filter of the logbook).

The functions work on a flight table (``pandas.DataFrame``) with the columns ``aircraft`` (name) and
``datum`` (start of the flight as a timestamp). They only read the table, so any page that shows flights
can use the same filter.

Aircraft, year and month each take a *selection*: ``None`` means "no restriction", otherwise a ``frozenset`` of
the values that are wanted (an empty set therefore matches no flight). Within one criterion the values are
alternatives (2024 *or* 2025), between criteria all must match (aircraft *and* year *and* month ...); year and
month are separate criteria, so years {2024, 2025} and months {6, 7} give June and July of both years.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import FrozenSet, Optional

import pandas as pd

MONTHS = tuple(range(1, 13))


def parse_date(text):
    """Date from user input: YYYY-MM-DD, DD.MM.YYYY or DD/MM/YYYY; empty -> None. Raises ValueError."""
    text = (text or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d.%m.%y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError(text)


def as_selection(value):
    """A selection from what a caller gives: ``None`` stays ``None`` (no restriction), a single name or number
    becomes a one-element set, any other collection becomes a ``frozenset``."""
    if value is None:
        return None
    if isinstance(value, (str, int)):
        return frozenset((value,))
    return frozenset(value)


@dataclass(frozen=True)
class FlightFilter:
    """Which flights are shown. ``None`` in a field means "no restriction"; all given fields must match.

    ``aircraft``, ``year`` and ``month`` are selections (see the module text); they accept a single value or any
    collection and are stored as ``frozenset``.
    """
    aircraft: Optional[FrozenSet[str]] = None
    year: Optional[FrozenSet[int]] = None
    month: Optional[FrozenSet[int]] = None  # 1..12, in every year unless years are chosen as well
    date_from: Optional[date] = None       # first day (inclusive)
    date_to: Optional[date] = None         # last day (inclusive)

    def __post_init__(self):
        for name in ("aircraft", "year", "month"):
            object.__setattr__(self, name, as_selection(getattr(self, name)))   # frozen dataclass: set directly

    @property
    def is_active(self):
        """True if the filter restricts anything (an empty selection restricts to no flight at all)."""
        return any(value is not None for value in (self.aircraft, self.year, self.month, self.date_from,
                                                   self.date_to))


def filter_mask(table, flight_filter):
    """Boolean Series: which rows of the table pass the filter."""
    mask = pd.Series(True, index=table.index)
    if flight_filter.aircraft is not None:
        mask &= table["aircraft"].isin(flight_filter.aircraft)
    if flight_filter.year is not None:
        mask &= table["datum"].dt.year.isin(flight_filter.year)
    if flight_filter.month is not None:
        mask &= table["datum"].dt.month.isin(flight_filter.month)
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
