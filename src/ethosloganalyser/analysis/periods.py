# -*- coding: utf-8 -*-
"""Quick selection of a year or a month on top of the period filter (from/to dates, Params.date_from/date_to).

The selection does not filter on its own: it only writes the from/to fields, so every analysis and every tab
follows it exactly as if the dates had been typed.
"""

import calendar
from datetime import date

import pandas as pd

from .fleet import parse_date

DATE_FIELD = "%d.%m.%Y"          # format written into the from/to fields (accepted by parse_date)


def period_of(year=None, month=None):
    """(first day, last day) of a year or of one month; (None, None) for "all years"."""
    if year is None:
        return None, None
    if month is None:
        return date(year, 1, 1), date(year, 12, 31)
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def period_fields(year=None, month=None, fmt=None):
    """Texts for the from/to fields of a year/month selection ("" = no limit).

    fmt: function date -> text (e.g. i18n.fmt_date for the format of the UI language); default DD.MM.YYYY.
    The text must be readable by parse_date.
    """
    fmt = fmt or (lambda d: d.strftime(DATE_FIELD))
    d0, d1 = period_of(year, month)
    return (fmt(d0) if d0 else "", fmt(d1) if d1 else "")


def selection_of(date_from, date_to):
    """Which quick selection the from/to fields correspond to.

    Returns ("all", None, None) for empty fields, ("year", y, None) or ("month", y, m) if the dates are exactly
    that year or month, else ("custom", None, None) - also for dates that cannot be read.
    """
    try:
        d0, d1 = parse_date(date_from), parse_date(date_to)
    except ValueError:
        return "custom", None, None
    if d0 is None and d1 is None:
        return "all", None, None
    if d0 is None or d1 is None:
        return "custom", None, None
    if (d0, d1) == period_of(d0.year):
        return "year", d0.year, None
    if (d0, d1) == period_of(d0.year, d0.month):
        return "month", d0.year, d0.month
    return "custom", None, None


def months_of(dates):
    """Set of (year, month) of the given dates/datetimes (missing values are ignored)."""
    s = pd.to_datetime(pd.Series(list(dates), dtype="object"), errors="coerce").dropna()
    return set(zip(s.dt.year.astype(int), s.dt.month.astype(int)))


def years_months(months):
    """{year: [months]} sorted: years newest first, months in calendar order."""
    out = {}
    for y, m in months:
        out.setdefault(int(y), set()).add(int(m))
    return {y: sorted(out[y]) for y in sorted(out, reverse=True)}
