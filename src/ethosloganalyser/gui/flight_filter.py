# -*- coding: utf-8 -*-
"""The shared flight filter: aircraft, year and month (each with several values) and a date range.

``FilterState`` holds the one setting and the choices that exist (aircraft, years). ``FilterBar`` is a row of
widgets that shows the state and changes it. The logbook and the statistics each show a bar; both show the same
setting and a change in one is seen in the other at once.

A selection that covers every existing value is no restriction at all: the state stores it as ``None`` ("alle"),
so a new aircraft or year that appears after an import is included as long as the user has not narrowed the
selection.
"""

import dataclasses

from ..analysis.periods import MONTHS, FlightFilter, parse_date
from ..config import model_label
from ..i18n import fmt_date, tr
from .multi_select import MultiSelect

INVALID_DATE_COLOR = "#b00020"
SELECTION_FIELDS = ("aircraft", "year", "month")     # the fields of FlightFilter that hold a selection


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

    def _choices(self, field):
        """The values the user can choose from for a selection field (months are always 1..12)."""
        return {"aircraft": self.aircraft_choices, "year": self.year_choices, "month": MONTHS}[field]

    def _collapsed(self, flight_filter):
        """The filter with every selection that covers all existing values replaced by ``None`` (no
        restriction). Without known choices nothing can be said, so the selection stays."""
        changes = {}
        for field in SELECTION_FIELDS:
            selection, choices = getattr(flight_filter, field), self._choices(field)
            if selection is not None and choices and selection.issuperset(choices):
                changes[field] = None
        return dataclasses.replace(flight_filter, **changes) if changes else flight_filter

    def _without_vanished(self, flight_filter):
        """The filter without aircraft and years that no longer exist. If nothing is left of a restriction
        (all its values vanished), the restriction is dropped; an empty selection the user made on purpose
        stays empty."""
        changes = {}
        for field in ("aircraft", "year"):
            selection = getattr(flight_filter, field)
            if selection is not None:
                kept = selection & frozenset(self._choices(field))
                if kept != selection:
                    changes[field] = kept or None
        return dataclasses.replace(flight_filter, **changes) if changes else flight_filter

    def set(self, **changes):
        """Changes fields of the filter (aircraft, year, month, date_from, date_to); listeners are told if
        something changed. A selection field takes a single value or a collection, ``None`` for "alle"."""
        new_value = self._collapsed(dataclasses.replace(self.value, **changes))
        if new_value != self.value:
            self.value = new_value
            self._notify()

    def reset(self):
        """Removes every restriction."""
        self.set(**{field.name: None for field in dataclasses.fields(FlightFilter)})

    def set_choices(self, aircraft, years):
        """Sets what the user can choose from (after the database changed). Aircraft and years that no longer
        exist are removed from the selection; if every remaining value is then selected, nothing is restricted."""
        aircraft, years = list(aircraft), list(years)
        changed_choices = (aircraft, years) != (self.aircraft_choices, self.year_choices)
        self.aircraft_choices, self.year_choices = aircraft, years
        new_value = self._collapsed(self._without_vanished(self.value))
        if not changed_choices and new_value == self.value:
            return
        self.value = new_value
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
    """Row of widgets for a FilterState: aircraft, year and month (several values each), from and to date,
    reset."""

    def __init__(self, parent, state):
        import tkinter as tk
        from tkinter import ttk

        self.state = state
        self.frame = ttk.Frame(parent)
        self.from_var, self.to_var = tk.StringVar(), tk.StringVar()

        ttk.Label(self.frame, text=tr("Filter:"), font=("", 10, "bold")).pack(side="left", padx=(0, 8))
        self.aircraft_box = self._add_box(tr("Flugzeug"), "aircraft", 16)
        self.year_box = self._add_box(tr("Jahr"), "year", 10)
        self.month_box = self._add_box(tr("Monat"), "month", 10)
        self.from_entry = self._add_date_entry(tr("von"), self.from_var, "date_from")
        self.to_entry = self._add_date_entry(tr("bis"), self.to_var, "date_to")
        self.reset_button = ttk.Button(self.frame, text=tr("Zurücksetzen"), command=state.reset)
        self.reset_button.pack(side="left", padx=(12, 0))

        state.add_listener(self.sync)
        self.frame.bind("<Destroy>", self._on_destroy)
        self.sync()

    # ---------------- building ----------------
    def _add_box(self, title, field, width):
        """A multi-select field for one selection field of the filter ("aircraft", "year" or "month"); a change
        of the ticked values goes to the state."""
        from tkinter import ttk
        ttk.Label(self.frame, text=title + ":").pack(side="left", padx=(8, 3))
        box = MultiSelect(self.frame, width, lambda chosen: self.state.set(**{field: chosen}))
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
        flt = self.state.value
        self.aircraft_box.show([(name, model_label(name)) for name in self.state.aircraft_choices], flt.aircraft)
        self.year_box.show([(year, str(year)) for year in self.state.year_choices], flt.year)
        self.month_box.show([(month, f"{month:02d}") for month in MONTHS], flt.month)
        for entry, variable, value in ((self.from_entry, self.from_var, flt.date_from),
                                       (self.to_entry, self.to_var, flt.date_to)):
            if value is not None or not _is_invalid_input(variable.get()):
                variable.set(fmt_date(value) if value is not None else "")
                entry.configure(foreground="")

    # ---------------- changes made by the user ----------------
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
