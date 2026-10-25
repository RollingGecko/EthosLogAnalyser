# -*- coding: utf-8 -*-
"""Logbook page: scope, totals, tables per year and month with a bar chart, sortable list of all flights.

Filled from the flight table of the folder analysis (analysis/logbook.py); from WP-17 on from the database.
"""

import numpy as np
import pandas as pd

from ..analysis.fleet import parse_date
from ..analysis.logbook import logbook
from ..config import model_label
from ..i18n import fmt_date, tr
from ..plots.logbook import figure_logbook, month_label
from ..utils import fmt_duration
from .common import sortable_tree

TOTAL_KEYS = ("flights", "days", "total", "longest", "shortest", "mah")


def _mah_text(value):
    return "–" if not np.isfinite(value) else f"{value:.0f}"


class LogbookPage:
    """The widgets of the logbook page and how they are filled from an analysis result."""

    def __init__(self, parent, charts, family, title):
        import tkinter as tk
        from tkinter import ttk

        self.charts = charts
        self.title = title
        self.state = {"book": None}
        self.on_open_flight = None            # callback(flight number) for a double-click on a flight
        frame = ttk.Frame(parent, padding=(10, 8))
        frame.pack(fill="both", expand=True)
        self.frame = frame
        self.scope = tk.StringVar()
        self.missing = tk.StringVar()
        ttk.Label(frame, textvariable=self.scope, font=(family, 10, "bold")).pack(anchor="w")
        ttk.Label(frame, textvariable=self.missing, foreground="#b36b00").pack(anchor="w")
        self._build_totals(frame, family)
        self._build_periods(frame)
        self._build_flight_list(frame)

    def _build_totals(self, parent, family):
        import tkinter as tk
        from tkinter import ttk
        box = ttk.LabelFrame(parent, text=tr("Summen"), padding=(10, 4))
        box.pack(fill="x", pady=(4, 6))
        self.totals = {}
        texts = {"flights": tr("Flüge"), "days": tr("Flugtage"), "total": tr("Log-Dauer gesamt"),
                 "longest": tr("Längster Flug (Log-Dauer)"), "shortest": tr("Kürzester Flug (Log-Dauer)"),
                 "mah": tr("Entnommen gesamt")}
        for k, key in enumerate(TOTAL_KEYS):
            ttk.Label(box, text=texts[key] + ":").grid(row=k // 3, column=2 * (k % 3), sticky="w", padx=(0, 6), pady=2)
            self.totals[key] = tk.StringVar(value="–")
            ttk.Label(box, textvariable=self.totals[key], font=(family, 10, "bold")).grid(
                row=k // 3, column=2 * (k % 3) + 1, sticky="w", padx=(0, 30), pady=2)
        ttk.Label(box, text=tr("Log-Dauer = Zeit von „Motor scharf“ bis „Motor gesperrt“ im Log, nicht die reine "
                               "Flugzeit."), foreground="#666").grid(row=2, column=0, columnspan=6, sticky="w",
                                                                    pady=(2, 0))

    @staticmethod
    def _period_tree(parent, first, height):
        from tkinter import ttk
        heads = [first, ("Fluege", tr("Flüge"), 50), ("dauer_s", tr("Log-Dauer"), 75),
                 ("Flugtage", tr("Flugtage"), 60), ("entnommen_mAh", tr("entnommen mAh"), 100)]
        tree = ttk.Treeview(parent, columns=[c for c, _h, _w in heads], show="headings", height=height)
        for key, head, width in heads:
            tree.heading(key, text=head)
            tree.column(key, width=width, anchor="center", stretch=False)
        return tree

    def _build_periods(self, parent):
        from tkinter import ttk
        middle = ttk.Frame(parent)
        middle.pack(fill="x")
        box = ttk.LabelFrame(middle, text=tr("Je Jahr"), padding=4)
        box.pack(side="left", fill="y", padx=(0, 6))
        self.year_tree = self._period_tree(box, ("Jahr", tr("Jahr"), 55), 9)
        self.year_tree.pack(fill="y", expand=True)
        box = ttk.LabelFrame(middle, text=tr("Je Monat"), padding=4)
        box.pack(side="left", fill="y", padx=(0, 6))
        self.month_tree = self._period_tree(box, ("Monat", tr("Monat"), 70), 9)
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=self.month_tree.yview)
        self.month_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.month_tree.pack(fill="y", expand=True)
        self.chart_frame = ttk.Frame(middle, height=300)
        self.chart_frame.pack(side="left", fill="both", expand=True)
        self.chart_frame.pack_propagate(False)

    def _build_flight_list(self, parent):
        from tkinter import ttk
        box = ttk.LabelFrame(parent, text=tr("Flüge (Klick auf eine Spaltenüberschrift sortiert)"), padding=4)
        box.pack(fill="both", expand=True, pady=(6, 0))
        columns = [("Flug", tr("Flug"), 60), ("datum", tr("Datum"), 100), ("zeit", tr("Uhrzeit"), 80),
                   ("dauer_s", tr("Log-Dauer"), 90), ("entnommen_mAh", tr("entnommen mAh"), 110)]
        self.flight_list = ttk.Treeview(box, columns=[c for c, _h, _w in columns], show="headings")
        for key, _head, width in columns:
            self.flight_list.column(key, width=width, anchor="center", stretch=False)
        self.sorter = sortable_tree(self.flight_list, columns)
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=self.flight_list.yview)
        self.flight_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.flight_list.pack(fill="both", expand=True)
        self.flight_list.bind("<Double-1>", self._on_double_click)

    def _on_double_click(self, event):
        item = self.flight_list.identify_row(event.y)
        if item and self.on_open_flight is not None:
            self.on_open_flight(int(self.flight_list.item(item, "values")[0]))

    def chart_canvas(self):
        """Canvas of the bar chart (for tests)."""
        return self.charts.page_canvases.get(str(self.chart_frame))

    def show(self, res, p):
        """Fills the page from the flight table of an analysis result (one model, period filter)."""
        book = logbook(res.df)
        self.state["book"] = book
        period = tr("alle Flüge")
        if p.date_from or p.date_to:
            period = "{} – {}".format(fmt_date(parse_date(p.date_from)) if p.date_from else "…",
                                      fmt_date(parse_date(p.date_to)) if p.date_to else "…")
        self.scope.set(tr("Modell {model}  ·  Zeitraum: {period}", model=model_label(res.meta.get("model")),
                          period=period))
        self.missing.set(tr("{n} Flüge ohne Datum oder Log-Dauer – in den Summen nicht enthalten.",
                            n=book.n_missing) if book.n_missing else "")
        self._show_totals(book)
        self._show_periods(book)
        self._show_flights(book)
        self.charts.show_fig(self.chart_frame, figure_logbook(book), builder=lambda: figure_logbook(self.state["book"]),
                             title=self.title)

    def _show_totals(self, book):
        totals = self.totals
        for var in totals.values():
            var.set("–")
        totals["flights"].set(str(book.n_counted))
        if not book.n_counted:
            return
        totals["flights"].set(tr("{n}  ({first} – {last})", n=book.n_counted, first=fmt_date(book.first),
                                 last=fmt_date(book.last)))
        totals["days"].set(str(book.flight_days))
        totals["total"].set(fmt_duration(book.total_s))
        for key in ("longest", "shortest"):
            row = getattr(book, key)
            totals[key].set(tr("{dur}  (Flug {no}, {date})", dur=fmt_duration(row["dauer_s"]), no=row["Flug"],
                               date=fmt_date(row["datum"])))
        mah = tr("{ah:.1f} Ah ({mah:.0f} mAh)", ah=book.mah_total / 1000, mah=book.mah_total)
        if book.n_mah < book.n_counted:
            mah += tr("  – ohne {n} Flüge mit ungültigen Akkuwerten", n=book.n_counted - book.n_mah)
        totals["mah"].set(mah)

    def _show_periods(self, book):
        for tree, table, first in ((self.year_tree, book.per_year, lambda k: str(k)),
                                   (self.month_tree, book.per_month, lambda k: month_label(int(k[0]), int(k[1])))):
            tree.delete(*tree.get_children())
            for k, row in table.iterrows():
                tree.insert("", "end", values=(first(k), int(row["Fluege"]), fmt_duration(row["dauer_s"]),
                                               int(row["Flugtage"]), _mah_text(float(row["entnommen_mAh"]))))

    def _show_flights(self, book):
        rows = []
        for _, row in book.flights.iterrows():
            when = row["datum"]
            has_date = not pd.isna(when)
            rows.append(((int(row["Flug"]), when if has_date else None,
                          when.strftime("%H:%M:%S") if has_date else None,
                          float(row["dauer_s"]), float(row["entnommen_mAh"])),
                         (int(row["Flug"]), fmt_date(when) if has_date else "–", f"{when:%H:%M}" if has_date else "–",
                          fmt_duration(row["dauer_s"]), _mah_text(float(row["entnommen_mAh"])))))
        self.sorter["set_rows"](rows)
