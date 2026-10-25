# -*- coding: utf-8 -*-
"""The three small tables of the logbook page: per aircraft, per year and per month.

They sit side by side under the totals and follow the shared filter. All three come from the same calculation
(``analysis/logbook.py``); this module only turns the tables into rows of text and builds the Treeviews. Column
widths and row height follow the font (``table_fit``), so nothing is cut off at any screen scaling.
"""

import numpy as np

from ..config import model_label
from ..i18n import tr
from ..utils import fmt_duration
from .table_fit import TableFonts

SUM_TAG = "sum"
SUM_BACKGROUND = "#e3e9f2"
TABLE_HEIGHT = 7                    # rows shown before a table scrolls
# the widest values the number columns can show: digits count (the duration is shaped from a long one)
WIDEST_FLIGHTS, WIDEST_DAYS, WIDEST_MAH = 5, 4, 7
WIDEST_DURATION_S = 1000 * 3600 - 1


def month_label(year, month):
    return f"{month:02d}/{year}"


def mah_text(value):
    return "–" if not np.isfinite(value) else f"{value:.0f}"


def aircraft_rows(book):
    """(rows, sum row) of the table per aircraft: (aircraft, flights, flight days, log duration, drawn mAh).

    The sum row repeats the totals of the page, so the table adds up to them. Without flights there are no rows
    and no sum row (None).
    """
    rows = [(model_label(name), int(row["Fluege"]), int(row["Flugtage"]), fmt_duration(row["dauer_s"]),
             mah_text(float(row["entnommen_mAh"]))) for name, row in book.per_aircraft.iterrows()]
    total = None
    if rows:
        total = (tr("Summe"), book.n_counted, book.flight_days, fmt_duration(book.total_s), mah_text(book.mah_total))
    return rows, total


def year_rows(book):
    """Rows of the table per year: (year, flights, log duration, flight days, drawn mAh)."""
    return [(str(year), int(row["Fluege"]), fmt_duration(row["dauer_s"]), int(row["Flugtage"]),
             mah_text(float(row["entnommen_mAh"]))) for year, row in book.per_year.iterrows()]


def month_rows(book):
    """Rows of the table per month, same columns as per year."""
    return [(month_label(int(year), int(month)), int(row["Fluege"]), fmt_duration(row["dauer_s"]),
             int(row["Flugtage"]), mah_text(float(row["entnommen_mAh"])))
            for (year, month), row in book.per_month.iterrows()]


class PeriodTable:
    """One small table in a labelled frame. ``columns``: [(key, heading)], the first column is the name."""

    def __init__(self, parent, title, columns, name_samples, scrollbar=False):
        from tkinter import ttk

        self.columns = columns
        self.name_samples = name_samples          # texts that decide the width of the first column
        self.frame = ttk.LabelFrame(parent, text=title, padding=4)
        keys = [key for key, _head in columns]
        self.tree = ttk.Treeview(self.frame, columns=keys, show="headings", height=TABLE_HEIGHT)
        for key, head in columns:
            self.tree.heading(key, text=head)
            self.tree.column(key, anchor="center", stretch=False)
        self.tree.tag_configure(SUM_TAG, background=SUM_BACKGROUND)      # not bold: the widths are for the normal font
        if scrollbar:
            bar = ttk.Scrollbar(self.frame, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=bar.set)
            bar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="y")
        self._fit([])

    def _samples(self, key, names):
        """The widest texts a column can show (the actual names for the first column)."""
        fonts = self.fonts
        if key == self.columns[0][0]:
            return list(self.name_samples) + list(names)
        return {"Fluege": [fonts.digits(WIDEST_FLIGHTS)], "Flugtage": [fonts.digits(WIDEST_DAYS)],
                "entnommen_mAh": [fonts.digits(WIDEST_MAH)],
                "dauer_s": [fonts.shaped(fmt_duration(WIDEST_DURATION_S))]}[key]

    def _fit(self, names):
        self.fonts = TableFonts(self.tree)
        for key, head in self.columns:
            self.tree.column(key, width=self.fonts.width(head, self._samples(key, names)), stretch=False)

    def show(self, rows, total=None):
        """Fills the table with rows of texts and, if given, the sum row (shaded) at the end."""
        self.tree.delete(*self.tree.get_children())
        self._fit([str(row[0]) for row in rows])
        for row in rows:
            self.tree.insert("", "end", values=row)
        if total is not None:
            self.tree.insert("", "end", values=total, tags=(SUM_TAG,))


class LogbookTables:
    """The three tables side by side: per aircraft, per year, per month."""

    def __init__(self, parent):
        from tkinter import ttk

        self.frame = ttk.Frame(parent)
        digit = TableFonts(parent).digits
        flights, days, duration, drawn = (tr("Flüge"), tr("Flugtage"), tr("Log-Dauer"), tr("entnommen mAh"))
        self.aircraft = PeriodTable(self.frame, tr("Je Flugzeug"), [
            ("aircraft", tr("Flugzeug")), ("Fluege", flights), ("Flugtage", days), ("dauer_s", duration),
            ("entnommen_mAh", drawn)], [tr("Summe")])
        period_columns = [("Fluege", flights), ("dauer_s", duration), ("Flugtage", days), ("entnommen_mAh", drawn)]
        self.year = PeriodTable(self.frame, tr("Je Jahr"), [("Jahr", tr("Jahr"))] + period_columns, [digit(4)])
        self.month = PeriodTable(self.frame, tr("Je Monat"), [("Monat", tr("Monat"))] + period_columns,
                                 [digit(2) + "/" + digit(4)], scrollbar=True)
        for table in (self.aircraft, self.year, self.month):
            table.frame.pack(side="left", fill="y", padx=(0, 6))

    def show(self, book):
        """Fills the three tables from a ``Logbook`` (``analysis/logbook.py``)."""
        rows, total = aircraft_rows(book)
        self.aircraft.show(rows, total)
        self.year.show(year_rows(book))
        self.month.show(month_rows(book))
