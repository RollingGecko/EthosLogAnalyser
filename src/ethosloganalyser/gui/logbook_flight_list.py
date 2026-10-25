# -*- coding: utf-8 -*-
"""The sortable flight list of the logbook.

Columns: number within the aircraft, aircraft, date, time, log duration, drawn charge, "Flug" (a ☑/☐ switch:
a click on it decides by hand whether the log is a flight) and a warning symbol for a possible duplicate
(hover over it for the explanation). A double-click on a row opens the single flight.
"""

import numpy as np
import pandas as pd

from ..config import model_label
from ..i18n import fmt_date, tr
from ..utils import fmt_duration
from .common import sortable_tree

# columns: key, width; the headings are translated when the list is built
COLUMN_KEYS = ("number", "aircraft", "datum", "time", "dauer_s", "entnommen_mAh", "is_flight", "note", "log_id")
FLIGHT_COLUMN, NOTE_COLUMN, ID_COLUMN = "is_flight", "note", "log_id"
CHECKED, UNCHECKED = "☑", "☐"
DUPLICATE_SYMBOL = "⚠"
NON_FLIGHT_TAG = "non_flight"
DOUBLE_CLICK_MS = 500           # a second click on the switch within this time is part of a double-click


def mah_text(value):
    return "–" if not np.isfinite(value) else f"{value:.0f}"


def list_row(flight):
    """(raw values for sorting, shown texts, tags) of one row of the table of listed logs."""
    when = flight["datum"]
    has_date = not pd.isna(when)
    number = None if pd.isna(flight["Flug"]) else int(flight["Flug"])
    is_flight = bool(flight["is_flight"])
    duplicate = bool(flight["possible_duplicate"])
    drawn = float(flight["entnommen_mAh"])
    log_id = int(flight["log_id"])
    raw = (number, flight["aircraft"], when if has_date else None, when.strftime("%H:%M:%S") if has_date else None,
           float(flight["dauer_s"]), drawn, int(is_flight), int(duplicate), log_id)
    shown = ("–" if number is None else number, model_label(flight["aircraft"]),
             fmt_date(when) if has_date else "–", f"{when:%H:%M}" if has_date else "–",
             fmt_duration(flight["dauer_s"]), mah_text(drawn), CHECKED if is_flight else UNCHECKED,
             DUPLICATE_SYMBOL if duplicate else "", log_id)
    return raw, shown, () if is_flight else (NON_FLIGHT_TAG,)


class FlightList:
    """The Treeview with the flights, sorting, the flight switch and the hint for the warning symbol."""

    def __init__(self, parent, on_open_flight, on_switch_flight):
        import tkinter as tk
        from tkinter import ttk

        self.on_open_flight = on_open_flight        # on_open_flight(log_id)
        self.on_switch_flight = on_switch_flight    # on_switch_flight(log_id)
        self._last_switch = (None, 0)               # (log id, event time) of the last switch
        box = ttk.LabelFrame(parent, text=tr("Flüge (Klick auf eine Spaltenüberschrift sortiert, Doppelklick öffnet "
                                             "den Einzelflug)"), padding=4)
        self.frame = box
        headings = {"number": tr("Nr."), "aircraft": tr("Flugzeug"), "datum": tr("Datum"), "time": tr("Uhrzeit"),
                    "dauer_s": tr("Log-Dauer"), "entnommen_mAh": tr("entnommen mAh"), "is_flight": tr("Flug"),
                    "note": "", "log_id": ""}
        widths = {"number": 50, "aircraft": 120, "datum": 95, "time": 70, "dauer_s": 85, "entnommen_mAh": 105,
                  "is_flight": 50, "note": 35, "log_id": 0}
        columns = [(key, headings[key], widths[key]) for key in COLUMN_KEYS]
        self.visible = [key for key in COLUMN_KEYS if key != ID_COLUMN]
        self.tree = ttk.Treeview(box, columns=list(COLUMN_KEYS), displaycolumns=self.visible, show="headings")
        for key, _heading, width in columns:
            self.tree.column(key, width=width, anchor="center", stretch=False)
        self.tree.tag_configure(NON_FLIGHT_TAG, foreground="#888888")
        self.sorter = sortable_tree(self.tree, columns)
        self.hint = tk.StringVar()
        ttk.Label(box, textvariable=self.hint, foreground="#b36b00").pack(side="bottom", anchor="w")
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Leave>", lambda _event: self.hint.set(""))

    # ---------------- content ----------------
    def show(self, listed):
        """Fills the list with the logs of the table `listed` (see db/logbook_table.py)."""
        self.sorter["set_rows"]([list_row(flight) for flight in listed.to_dict("records")])

    def log_ids(self):
        """Log ids of the rows in the order shown (for tests)."""
        return [self.log_id_of(item) for item in self.tree.get_children()]

    def log_id_of(self, item):
        return int(self.tree.set(item, ID_COLUMN))

    # ---------------- mouse ----------------
    def _cell(self, event):
        """(item, column key) under the mouse, (None, None) outside the cells."""
        if self.tree.identify_region(event.x, event.y) != "cell":
            return None, None
        column = int(self.tree.identify_column(event.x).lstrip("#")) - 1
        return self.tree.identify_row(event.y), self.visible[column]

    def _on_click(self, event):
        item, column = self._cell(event)
        if column == FLIGHT_COLUMN and item:
            self.switch_row(item, event.time)

    def switch_row(self, item, event_time=0):
        """Switches the log of a row between flight and no flight (what a click on the switch does)."""
        log_id = self.log_id_of(item)
        last_id, last_time = self._last_switch
        if log_id == last_id and 0 <= event_time - last_time < DOUBLE_CLICK_MS:
            return                                  # the second click of a double-click
        self._last_switch = (log_id, event_time)
        self.on_switch_flight(log_id)

    def _on_double_click(self, event):
        item, column = self._cell(event)
        if item and column != FLIGHT_COLUMN:
            self.open_row(item)

    def open_row(self, item):
        """Opens the log of a row on the single-flight page (what a double-click does)."""
        if item:
            self.on_open_flight(self.log_id_of(item))

    def _on_motion(self, event):
        item, column = self._cell(event)
        if column == NOTE_COLUMN and item and self.tree.set(item, NOTE_COLUMN):
            self.hint.set(tr("Mögliches Duplikat: gleiches Flugzeug und gleiche Startzeit wie ein anderer Flug"))
        else:
            self.hint.set("")
