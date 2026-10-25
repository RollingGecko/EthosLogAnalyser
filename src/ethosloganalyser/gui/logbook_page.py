# -*- coding: utf-8 -*-
"""Logbook page (start page): filter, totals, tables per year and month with a bar chart, the "Group by"
tree and the sortable list of flights.

Everything comes from the flight database (``LogbookModel``), so the page is filled as soon as the window is
shown. The filter (aircraft, year, month, date range) is shared with other pages (``flight_filter``); totals,
tables and chart follow the filter, the flight list additionally follows the selected row of the tree.
"""

import numpy as np

from ..analysis.logbook_groups import GROUP_BY_AIRCRAFT, GROUP_BY_TIME
from ..config import model_label
from ..i18n import N_, fmt_date, tr
from ..plots.logbook import figure_logbook, month_label
from ..utils import fmt_duration
from .flight_filter import FilterBar
from .logbook_flight_list import FlightList
from .logbook_group_tree import GroupTree
from .logbook_model import ANNOTATIONS_CHANGED

TOTAL_KEYS = ("flights", "days", "total", "longest", "shortest", "mah")

EMPTY_LOGBOOK = N_("Noch keine Flüge in der Datenbank. Logs importieren: „Daten & Einstellungen“ → „Datenbank“ → "
                   "„Ordner importieren …“ oder „Dateien importieren …“.")


def _mah_text(value):
    return "–" if not np.isfinite(value) else f"{value:.0f}"


class LogbookPage:
    """The widgets of the logbook page and how they are filled from the logbook model."""

    def __init__(self, parent, charts, family, title, model, filter_state):
        import tkinter as tk
        from tkinter import ttk

        self.charts = charts
        self.title = title
        self.model = model                    # LogbookModel
        self.filter_state = filter_state      # FilterState shared with other pages
        self.state = {"book": None, "view": None}
        self.on_open_flight = None            # callback(log id) for a double-click on a flight
        self.on_switch_flight = None          # callback(log id) for the flight switch in the list
        self._show_pending = False
        frame = ttk.Frame(parent, padding=(10, 8))
        frame.pack(fill="both", expand=True)
        self.frame = frame
        self.scope = tk.StringVar()
        self.missing = tk.StringVar()
        self._build_filter_row(frame)
        ttk.Label(frame, textvariable=self.scope, font=(family, 10, "bold")).pack(anchor="w", pady=(6, 0))
        ttk.Label(frame, textvariable=self.missing, foreground="#b36b00").pack(anchor="w")
        self._build_totals(frame, family)
        self._build_periods(frame)
        self._build_lists(frame)
        filter_state.add_listener(self.schedule_show)
        frame.bind("<Destroy>", self._on_destroy)

    # ---------------- building ----------------
    def _build_filter_row(self, parent):
        import tkinter as tk
        from tkinter import ttk
        row = ttk.Frame(parent)
        row.pack(fill="x")
        self.filter_bar = FilterBar(row, self.filter_state)
        self.filter_bar.frame.pack(side="left")
        self.show_non_flights = tk.BooleanVar(value=self.model.show_non_flights)
        self.non_flights_button = ttk.Checkbutton(row, text=tr("Nicht-Flüge anzeigen"), variable=self.show_non_flights,
                                                  command=self._non_flights_toggled)
        self.non_flights_button.pack(side="right")
        self.only_annotated = tk.BooleanVar(value=self.model.only_annotated)
        self.annotated_button = ttk.Checkbutton(row, text=tr("nur mit Notiz oder Auffälligkeit"),
                                                variable=self.only_annotated, command=self._annotated_toggled)
        self.annotated_button.pack(side="right", padx=(0, 12))

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

    def _build_lists(self, parent):
        """The tree on the left and the flight list on the right."""
        from tkinter import ttk
        bottom = ttk.Frame(parent)
        bottom.pack(fill="both", expand=True, pady=(6, 0))
        self.group_tree = GroupTree(bottom, self.model.group_by, self._group_by_changed, self._group_selected)
        self.group_tree.frame.pack(side="left", fill="y", padx=(0, 6))
        self.flight_list = FlightList(bottom, lambda log_id: self.on_open_flight and self.on_open_flight(log_id),
                                      lambda log_id: self.on_switch_flight and self.on_switch_flight(log_id),
                                      hint_lines=self.model.hint_lines)
        self.flight_list.frame.pack(side="left", fill="both", expand=True)
        self.sorter = self.flight_list.sorter
        self.open_row = self.flight_list.open_row

    def _on_destroy(self, event):
        if event.widget is self.frame:
            self.filter_state.remove_listener(self.schedule_show)

    # ---------------- reading the database, showing ----------------
    def refresh(self):
        """Reads the flights from the database again if they or the battery settings changed. If only notes or
        anomalies changed, only the flight list is shown again (quick: no totals, no chart)."""
        changed = self.model.refresh()
        if changed == ANNOTATIONS_CHANGED:
            if not self._show_pending and self.state["view"] is not None:
                self.flight_list.show(self.model.listed(self.filter_state.value))
        elif changed:
            self.filter_state.set_choices(self.model.aircraft_names(), self.model.years())
            self.schedule_show()

    def schedule_show(self):
        """Redraws the page once the window is idle (several changes in a row cause one redraw)."""
        if not self._show_pending:
            self._show_pending = True
            self.frame.after_idle(self._show_if_alive)

    def _show_if_alive(self):
        if self._show_pending and self.frame.winfo_exists():
            self.show()

    def chart_canvas(self):
        """Canvas of the bar chart (for tests)."""
        return self.charts.page_canvases.get(str(self.chart_frame))

    def show(self):
        """Fills the whole page for the current filter."""
        self._show_pending = False
        view = self.model.view(self.filter_state.value)
        book = view.book
        self.state["book"], self.state["view"] = book, view
        self._show_scope(view)
        self._show_totals(book, view.n_aircraft > 1)
        self._show_periods(book)
        self._show_groups_and_list(view)
        self.frame.update_idletasks()            # numbers and lists are on screen before the slower chart is drawn
        figure = figure_logbook(book)
        if not self.charts.replace_fig(self.chart_frame, figure):        # the first time: create the canvas
            self.charts.show_fig(self.chart_frame, figure, builder=lambda: figure_logbook(self.state["book"]),
                                 title=self.title)

    def _show_groups_and_list(self, view):
        self.group_tree.show(view.groups, view.n_flights, view.book.total_s, self.model.group_selector)
        self.flight_list.show(view.listed)

    def _show_scope(self, view):
        if not view.n_total and not len(self.model.table):
            self.scope.set(tr(EMPTY_LOGBOOK))
        else:
            text = tr("{n} von {total} Flügen der Datenbank", n=view.n_flights, total=view.n_total)
            self.scope.set(text + (tr("  ·  Filter aktiv") if self.filter_state.value.is_active else ""))
        book = view.book
        self.missing.set(tr("{n} Flüge ohne Datum oder Log-Dauer – in den Summen nicht enthalten.",
                            n=book.n_missing) if book.n_missing else "")

    def _show_totals(self, book, name_aircraft):
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
            if name_aircraft:             # flight numbers count per aircraft, so name it
                text = tr("{dur}  (Flug {no} der {aircraft}, {date})", dur=fmt_duration(row["dauer_s"]), no=row["Flug"],
                          aircraft=model_label(row["aircraft"]), date=fmt_date(row["datum"]))
            else:
                text = tr("{dur}  (Flug {no}, {date})", dur=fmt_duration(row["dauer_s"]), no=row["Flug"],
                          date=fmt_date(row["datum"]))
            totals[key].set(text)
        mah = tr("{ah:.1f} Ah ({mah:.0f} mAh)", ah=book.mah_total / 1000, mah=book.mah_total)
        if book.n_mah < book.n_counted:
            mah += tr("  – ohne {n} Flüge ohne gültige Akkuwerte", n=book.n_counted - book.n_mah)
        totals["mah"].set(mah)

    def _show_periods(self, book):
        for tree, table, first in ((self.year_tree, book.per_year, lambda k: str(k)),
                                   (self.month_tree, book.per_month, lambda k: month_label(int(k[0]), int(k[1])))):
            tree.delete(*tree.get_children())
            for k, row in table.iterrows():
                tree.insert("", "end", values=(first(k), int(row["Fluege"]), fmt_duration(row["dauer_s"]),
                                               int(row["Flugtage"]), _mah_text(float(row["entnommen_mAh"]))))

    # ---------------- choices on the page ----------------
    def _non_flights_toggled(self):
        self.model.show_non_flights = bool(self.show_non_flights.get())
        self.flight_list.show(self.model.listed(self.filter_state.value))

    def _annotated_toggled(self):
        self.model.only_annotated = bool(self.only_annotated.get())
        self.flight_list.show(self.model.listed(self.filter_state.value))

    def _group_by_changed(self, group_by):
        """Another grouping: the selected row of the old tree no longer exists."""
        self.model.group_by = group_by if group_by in (GROUP_BY_TIME, GROUP_BY_AIRCRAFT) else GROUP_BY_TIME
        self.model.group_selector = None
        view = self.model.view(self.filter_state.value)
        self.state["view"] = view
        self._show_groups_and_list(view)

    def _group_selected(self, selector):
        """A row of the tree was chosen: the flight list shows only its flights."""
        self.model.group_selector = selector
        self.flight_list.show(self.model.listed(self.filter_state.value))
