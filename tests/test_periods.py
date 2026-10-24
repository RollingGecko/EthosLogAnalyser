# -*- coding: utf-8 -*-
"""Year/month quick selection on top of the period filter (analysis/periods.py)."""

from datetime import date, datetime

import numpy as np

from ethosloganalyser import Params
from ethosloganalyser.analysis.fleet import in_period
from ethosloganalyser.analysis.periods import (months_of, period_fields, period_of, selection_of,
                                               years_months)


def test_period_of_year_and_month():
    assert period_of() == (None, None)
    assert period_of(2026) == (date(2026, 1, 1), date(2026, 12, 31))
    assert period_of(2026, 2) == (date(2026, 2, 1), date(2026, 2, 28))
    assert period_of(2024, 2) == (date(2024, 2, 1), date(2024, 2, 29))       # leap year
    assert period_of(2025, 12) == (date(2025, 12, 1), date(2025, 12, 31))


def test_fields_round_trip_and_cover_the_whole_period():
    assert period_fields() == ("", "")
    assert period_fields(2026, 5) == ("01.05.2026", "31.05.2026")
    assert period_fields(2026, 5, fmt=lambda d: f"{d:%d/%m/%Y}") == ("01/05/2026", "31/05/2026")
    for y, m in [(2026, None), (2026, 5), (2024, 2)]:
        d0, d1 = period_fields(y, m)
        assert selection_of(d0, d1) == (("year", y, None) if m is None else ("month", y, m))
        p = Params(date_from=d0, date_to=d1)
        first, last = period_of(y, m)
        # the first and the last minute of the period are inside, the day before and after are not
        assert in_period(datetime(first.year, first.month, first.day, 0, 1), p)
        assert in_period(datetime(last.year, last.month, last.day, 23, 59), p)
        assert not in_period(date.fromordinal(first.toordinal() - 1), p)
        assert not in_period(date.fromordinal(last.toordinal() + 1), p)


def test_selection_of_other_inputs():
    assert selection_of("", "") == ("all", None, None)
    assert selection_of("2026-01-01", "2026-12-31") == ("year", 2026, None)     # other accepted formats
    assert selection_of("01/03/2026", "31/03/2026") == ("month", 2026, 3)
    assert selection_of("20.09.2026", "") == ("custom", None, None)
    assert selection_of("01.01.2025", "31.12.2026") == ("custom", None, None)
    assert selection_of("01.05.2026", "30.05.2026") == ("custom", None, None)
    assert selection_of("kein Datum", "") == ("custom", None, None)


def test_months_with_flights():
    dates = [datetime(2025, 12, 31, 23, 0), datetime(2026, 1, 1, 9, 0), datetime(2026, 1, 20), None, np.nan,
             datetime(2024, 7, 4)]
    months = months_of(dates)
    assert months == {(2025, 12), (2026, 1), (2024, 7)}
    assert years_months(months) == {2026: [1], 2025: [12], 2024: [7]}
    assert list(years_months(months)) == [2026, 2025, 2024]                  # newest year first
    assert months_of([]) == set()
