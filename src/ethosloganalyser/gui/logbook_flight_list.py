# -*- coding: utf-8 -*-
"""The sortable flight list of the logbook.

Columns: number within the aircraft, aircraft, date, time, log duration, drawn charge, "Flug" (a ☑/☐ switch:
a click on it decides by hand whether the log is a flight) and a narrow hint column with symbols: a note (✎),
the highest severity of the anomalies not acknowledged yet (ℹ info, ⚠ warning, ‼ critical) and a possible
duplicate (⚠). Hovering over the hint column shows the texts below the list. A double-click on a row opens the
single flight.

Only characters that Windows shows with its user-interface font are used (no emojis).
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
NOTE_SYMBOL = "✎"
SEVERITY_SYMBOLS = {1: "ℹ", 2: "⚠", 3: "‼"}          # by annotations.SEVERITY_RANK
# the widest text the hint column can show (its width follows the font, so nothing is cut off)
WIDEST_HINT = " ".join((NOTE_SYMBOL, SEVERITY_SYMBOLS[3], DUPLICATE_SYMBOL))
HINT_COLORS = {"note": "#1f3b73", "info": "#1f3b73", "warning": "#b36b00", "critical": "#b00020",
               "duplicate": "#b36b00"}
NON_FLIGHT_TAG = "non_flight"
DOUBLE_CLICK_MS = 500           # a second click on the switch within this time is part of a double-click


def mah_text(value):
    return "–" if not np.isfinite(value) else f"{value:.0f}"


def hint_symbols(has_note, open_rank, duplicate):
    """Text of the hint column: note, highest open severity, possible duplicate."""
    symbols = [NOTE_SYMBOL] if has_note else []
    if open_rank:
        symbols.append(SEVERITY_SYMBOLS[open_rank])
    if duplicate:
        symbols.append(DUPLICATE_SYMBOL)
    return " ".join(symbols)


def list_row(flight):
    """(raw values for sorting, shown texts, tags) of one row of the table of listed logs."""
    when = flight["datum"]
    has_date = not pd.isna(when)
    number = None if pd.isna(flight["Flug"]) else int(flight["Flug"])
    is_flight = bool(flight["is_flight"])
    duplicate = bool(flight["possible_duplicate"])
    drawn = float(flight["entnommen_mAh"])
    log_id = int(flight["log_id"])
    has_note = bool(flight.get("has_note", False))
    open_rank = int(flight.get("open_rank", 0))
    # sorting by the hint column: most severe open anomaly first (descending), then notes, then duplicates
    hint_order = open_rank * 4 + has_note * 2 + int(duplicate)
    raw = (number, flight["aircraft"], when if has_date else None, when.strftime("%H:%M:%S") if has_date else None,
           float(flight["dauer_s"]), drawn, int(is_flight), hint_order, log_id)
    shown = ("–" if number is None else number, model_label(flight["aircraft"]),
             fmt_date(when) if has_date else "–", f"{when:%H:%M}" if has_date else "–",
             fmt_duration(flight["dauer_s"]), mah_text(drawn), CHECKED if is_flight else UNCHECKED,
             hint_symbols(has_note, open_rank, duplicate), log_id)
    return raw, shown, () if is_flight else (NON_FLIGHT_TAG,)


class FlightList:
    """The Treeview with the flights, sorting, the flight switch and the hint for the warning symbol."""

    def __init__(self, parent, on_open_flight, on_switch_flight, hint_lines=None):
        import tkinter as tk
        from tkinter import font as tkfont, ttk

        self.on_open_flight = on_open_flight        # on_open_flight(log_id)
        self.on_switch_flight = on_switch_flight    # on_switch_flight(log_id)
        self.hint_lines = hint_lines or (lambda log_id: [])   # log_id -> [(kind, text)] for the hint
        self._hint_item = None
        self._duplicates = set()                    # log ids of the listed possible duplicates
        self._last_switch = (None, 0)               # (log id, event time) of the last switch
        box = ttk.LabelFrame(parent, text=tr("Flüge (Klick auf eine Spaltenüberschrift sortiert, Doppelklick öffnet "
                                             "den Einzelflug)"), padding=4)
        self.frame = box
        headings = {"number": tr("Nr."), "aircraft": tr("Flugzeug"), "datum": tr("Datum"), "time": tr("Uhrzeit"),
                    "dauer_s": tr("Log-Dauer"), "entnommen_mAh": tr("entnommen mAh"), "is_flight": tr("Flug"),
                    "note": "", "log_id": ""}
        # the hint column is as wide as its widest text in the current font (plus the cell padding)
        hint_width = tkfont.nametofont("TkDefaultFont").measure(WIDEST_HINT + "  ") + 12
        widths = {"number": 50, "aircraft": 120, "datum": 95, "time": 70, "dauer_s": 85, "entnommen_mAh": 105,
                  "is_flight": 50, "note": max(35, hint_width), "log_id": 0}
        columns = [(key, headings[key], widths[key]) for key in COLUMN_KEYS]
        self.visible = [key for key in COLUMN_KEYS if key != ID_COLUMN]
        self.tree = ttk.Treeview(box, columns=list(COLUMN_KEYS), displaycolumns=self.visible, show="headings")
        for key, _heading, width in columns:
            self.tree.column(key, width=width, anchor="center", stretch=False)
        self.tree.tag_configure(NON_FLIGHT_TAG, foreground="#888888")
        self.sorter = sortable_tree(self.tree, columns)
        self.hint = tk.StringVar()
        self.hint_label = ttk.Label(box, textvariable=self.hint, foreground="#b36b00", justify="left")
        self.hint_label.pack(side="bottom", anchor="w", fill="x")
        # long notes wrap instead of being cut off
        box.bind("<Configure>", lambda event: self.hint_label.configure(wraplength=max(200, event.width - 20)))
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Leave>", lambda _event: self._clear_hint())

    # ---------------- content ----------------
    def show(self, listed):
        """Fills the list with the logs of the table `listed` (see db/logbook_table.py)."""
        records = listed.to_dict("records")
        self._duplicates = {int(flight["log_id"]) for flight in records if flight["possible_duplicate"]}
        self._clear_hint()
        self.sorter["set_rows"]([list_row(flight) for flight in records])

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
            if item != self._hint_item:              # read the texts once per row, not on every mouse move
                self._hint_item = item
                self.show_hint(item)
        else:
            self._clear_hint()

    def _clear_hint(self):
        self._hint_item = None
        self.hint.set("")

    def hint_text(self, item):
        """The texts behind the symbols of a row: note, open anomalies, possible duplicate (one per line)."""
        prefixes = {"note": NOTE_SYMBOL, "info": SEVERITY_SYMBOLS[1], "warning": SEVERITY_SYMBOLS[2],
                    "critical": SEVERITY_SYMBOLS[3]}
        lines = [(kind, f"{prefixes.get(kind, '')} {text}") for kind, text in self.hint_lines(self.log_id_of(item))]
        if self.log_id_of(item) in self._duplicates:
            lines.append(("duplicate", f"{DUPLICATE_SYMBOL} " + tr("Mögliches Duplikat: gleiches Flugzeug und "
                                                                   "gleiche Startzeit wie ein anderer Flug")))
        return lines

    def show_hint(self, item):
        """Shows the texts of a row below the list, coloured by the most severe of them."""
        lines = self.hint_text(item)
        order = ("critical", "warning", "duplicate", "info", "note")
        strongest = min((kind for kind, _text in lines), key=order.index, default="note")
        self.hint_label.configure(foreground=HINT_COLORS[strongest])
        self.hint.set("\n".join(text for _kind, text in lines))
