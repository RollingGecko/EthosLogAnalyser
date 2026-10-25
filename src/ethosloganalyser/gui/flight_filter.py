# -*- coding: utf-8 -*-
"""The shared flight filter: aircraft, year, month and a date range.

``FilterState`` holds the one setting and the choices that exist (aircraft, years). ``FilterBar`` is a row of
widgets that shows the state and changes it. The logbook and the statistics each show a bar; both show the same
setting and a change in one is seen in the other at once.
"""

import dataclasses

from ..analysis.periods import MONTHS, FlightFilter, parse_date
from ..config import model_label
from ..i18n import fmt_date, tr

INVALID_DATE_COLOR = "#b00020"


class FilterState:
    """The current FlightFilter and the aircraft and years the user can choose from."""

    def __init__(self):
        self.value = FlightFilter()
        self.aircraft_choices = []               # aircraft names that exist
        self.year_choices = []                   # years with flights
        self._listeners = []

    def add_listener(self, listener):
        """listener() is called whenever the filter or the choices change."""
        self._listeners.append(listener)

    def remove_listener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify(self):
        for listener in list(self._listeners):
            listener()

    def set(self, **changes):
        """Changes fields of the filter (aircraft, year, month, date_from, date_to); listeners are told if
        something changed."""
        new_value = dataclasses.replace(self.value, **changes)
        if new_value != self.value:
            self.value = new_value
            self._notify()

    def reset(self):
        """Removes every restriction."""
        self.set(**{field.name: None for field in dataclasses.fields(FlightFilter)})

    def set_choices(self, aircraft, years):
        """Sets what the user can choose from (after the database changed). A restriction to an aircraft or
        a year that no longer exists is removed."""
        aircraft, years = list(aircraft), list(years)
        stale = {}
        if self.value.aircraft is not None and self.value.aircraft not in aircraft:
            stale["aircraft"] = None
        if self.value.year is not None and self.value.year not in years:
            stale["year"] = None
        if (aircraft, years) == (self.aircraft_choices, self.year_choices) and not stale:
            return
        self.aircraft_choices, self.year_choices = aircraft, years
        self.value = dataclasses.replace(self.value, **stale)
        self._notify()


def _is_invalid_input(text):
    """True for a typed text that is no date (it stays visible and marked until the user corrects it)."""
    if not text.strip():
        return False
    try:
        parse_date(text)
    except ValueError:
        return True
    return False


class FilterBar:
    """Row of widgets for a FilterState: aircraft, year, month, from and to date, reset."""

    def __init__(self, parent, state):
        import tkinter as tk
        from tkinter import ttk

        self.state = state
        self.frame = ttk.Frame(parent)
        self._aircraft_names = []                # aircraft names in the order of the aircraft box
        self.aircraft_var, self.year_var, self.month_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.from_var, self.to_var = tk.StringVar(), tk.StringVar()

        ttk.Label(self.frame, text=tr("Filter:"), font=("", 10, "bold")).pack(side="left", padx=(0, 8))
        self.aircraft_box = self._add_box(tr("Flugzeug"), self.aircraft_var, 16)
        self.year_box = self._add_box(tr("Jahr"), self.year_var, 6)
        self.month_box = self._add_box(tr("Monat"), self.month_var, 5)
        self.from_entry = self._add_date_entry(tr("von"), self.from_var, "date_from")
        self.to_entry = self._add_date_entry(tr("bis"), self.to_var, "date_to")
        self.reset_button = ttk.Button(self.frame, text=tr("Zurücksetzen"), command=state.reset)
        self.reset_button.pack(side="left", padx=(12, 0))

        self.aircraft_box.bind("<<ComboboxSelected>>", self._aircraft_chosen)
        self.year_box.bind("<<ComboboxSelected>>", self._year_chosen)
        self.month_box.bind("<<ComboboxSelected>>", self._month_chosen)
        state.add_listener(self.sync)
        self.frame.bind("<Destroy>", self._on_destroy)
        self.sync()

    # ---------------- building ----------------
    def _add_box(self, title, variable, width):
        from tkinter import ttk
        ttk.Label(self.frame, text=title + ":").pack(side="left", padx=(8, 3))
        box = ttk.Combobox(self.frame, textvariable=variable, state="readonly", width=width)
        box.pack(side="left")
        return box

    def _add_date_entry(self, title, variable, field):
        from tkinter import ttk
        ttk.Label(self.frame, text=title + ":").pack(side="left", padx=(8, 3))
        entry = ttk.Entry(self.frame, textvariable=variable, width=11)
        entry.pack(side="left")
        entry.bind("<Return>", lambda _event: self._date_entered(entry, variable, field))
        entry.bind("<FocusOut>", lambda _event: self._date_entered(entry, variable, field))
        return entry

    def _on_destroy(self, event):
        if event.widget is self.frame:
            self.state.remove_listener(self.sync)

    # ---------------- showing the state ----------------
    def sync(self):
        """Shows the current filter and choices (called when the state changes)."""
        everything = tr("alle")
        flt = self.state.value
        self._aircraft_names = list(self.state.aircraft_choices)
        self.aircraft_box["values"] = [everything] + [model_label(name) for name in self._aircraft_names]
        self.year_box["values"] = [everything] + [str(year) for year in self.state.year_choices]
        self.month_box["values"] = [everything] + [f"{month:02d}" for month in MONTHS]
        self.aircraft_var.set(model_label(flt.aircraft) if flt.aircraft is not None else everything)
        self.year_var.set(str(flt.year) if flt.year is not None else everything)
        self.month_var.set(f"{flt.month:02d}" if flt.month is not None else everything)
        for entry, variable, value in ((self.from_entry, self.from_var, flt.date_from),
                                       (self.to_entry, self.to_var, flt.date_to)):
            if value is not None or not _is_invalid_input(variable.get()):
                variable.set(fmt_date(value) if value is not None else "")
                entry.configure(foreground="")

    # ---------------- changes made by the user ----------------
    def _aircraft_chosen(self, _event=None):
        index = self.aircraft_box.current()
        self.state.set(aircraft=self._aircraft_names[index - 1] if index > 0 else None)

    def _year_chosen(self, _event=None):
        index = self.year_box.current()
        self.state.set(year=self.state.year_choices[index - 1] if index > 0 else None)

    def _month_chosen(self, _event=None):
        index = self.month_box.current()
        self.state.set(month=MONTHS[index - 1] if index > 0 else None)

    def _date_entered(self, entry, variable, field):
        """Takes over a typed date (empty = no limit); an input that is no date is marked and ignored."""
        try:
            value = parse_date(variable.get())
        except ValueError:
            entry.configure(foreground=INVALID_DATE_COLOR)
            return
        entry.configure(foreground="")
        self.state.set(**{field: value})
        self.sync()
