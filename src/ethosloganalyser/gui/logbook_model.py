# -*- coding: utf-8 -*-
"""What the logbook shows, worked out from the flight database (no Tkinter here).

``LogbookModel`` reads the flights of the open database into the logbook flight table
(``db/logbook_table.py``) and answers: which flights pass the filter, what are their totals, how do they group
in the tree and which rows does the flight list show. The table is read again only when the database changed
or the battery settings changed (they decide which battery values count). Notes and anomalies only add two
columns (``has_note``, ``open_rank``); when only they changed, just these columns are read again.
"""

import dataclasses
from dataclasses import dataclass

import pandas as pd

from ..analysis.logbook import Logbook, logbook
from ..analysis.logbook_groups import GROUP_BY_TIME, all_selectors, build_groups, select_flights
from ..analysis.periods import aircraft_in, apply_filter, years_in
from ..db import annotations, flight_store
from ..db.logbook_table import build_logbook_table, empty_logbook_table, manual_value_after_switch


@dataclass
class LogbookView:
    """Everything the logbook page shows for one filter."""
    book: Logbook                    # totals and tables per year and month of the flights that pass the filter
    groups: list                     # GroupNode tree of these flights
    n_flights: int                   # flights that pass the filter
    n_aircraft: int                  # different aircraft among them
    n_total: int                     # flights in the database
    listed: pd.DataFrame             # rows of the flight list (flights, and non-flights if they are shown)


# what LogbookModel.refresh found changed
FLIGHTS_CHANGED = "flights"
ANNOTATIONS_CHANGED = "annotations"


def with_annotations(table, summary):
    """The logbook table with the columns has_note (bool) and open_rank (highest severity of the anomalies not
    acknowledged, 0 = none) from ``annotations.annotation_summary``."""
    table = table.drop(columns=["has_note", "open_rank"], errors="ignore")
    if summary is None or not len(table):
        merged = table.assign(has_note=False, open_rank=0)
    else:
        merged = table.merge(summary, on="log_id", how="left")
    merged["has_note"] = merged["has_note"].fillna(False).astype(bool)
    merged["open_rank"] = merged["open_rank"].fillna(0).astype(int)
    merged.index = table.index
    return merged


@dataclass
class DatabaseSummary:
    """The state of the database in a few numbers (status line)."""
    n_flights: int
    n_non_flights: int
    n_aircraft: int
    first: object                    # date of the first and the last flight, None without flights
    last: object


class LogbookModel:
    """The logbook flight table of the open database plus the choices the user made in the logbook."""

    def __init__(self, database, params_for):
        self.database = database                 # gui.database_panel.DatabaseController
        self.params_for = params_for             # aircraft name -> config.Params (battery settings of that aircraft)
        self.table = with_annotations(empty_logbook_table(), None)
        self._signature = None
        self._annotations_signature = None
        # choices of the logbook page; kept here so they survive rebuilding the window (language switch)
        self.show_non_flights = False
        self.group_by = GROUP_BY_TIME
        self.group_selector = None               # selector of the selected row of the tree, None = all
        self.only_annotated = False              # list only flights with a note or an open anomaly

    # ---------------- reading the database ----------------
    def _connection(self):
        database = self.database.database
        return database.connection if database is not None else None

    def _battery_signature(self):
        """The battery settings of all aircraft in the table; a change makes the battery validity stale."""
        return tuple(dataclasses.astuple(self.params_for(name)) for name in aircraft_in(self.table))

    def refresh(self):
        """Reads the table again if the database or the battery settings changed (FLIGHTS_CHANGED), only the note
        and anomaly columns if only they changed (ANNOTATIONS_CHANGED). None if nothing changed."""
        generation = self.database.generation
        annotations_generation = self.database.annotations_generation
        connection = self._connection()
        if self._signature != (generation, self._battery_signature()):
            rows = flight_store.logbook_rows(connection) if connection is not None else pd.DataFrame()
            self.table = build_logbook_table(rows, self.params_for)
            self._signature = (generation, self._battery_signature())
            changed = FLIGHTS_CHANGED
        elif self._annotations_signature != annotations_generation:
            changed = ANNOTATIONS_CHANGED
        else:
            return None
        summary = annotations.annotation_summary(connection) if connection is not None else None
        self.table = with_annotations(self.table, summary)
        self._annotations_signature = annotations_generation
        return changed

    # ---------------- what to show ----------------
    @property
    def flights(self):
        """The logs that are flights (by detection or by hand)."""
        return self.table[self.table["is_flight"].astype(bool)]

    def aircraft_names(self):
        return aircraft_in(self.flights)

    def years(self):
        return years_in(self.flights)

    def view(self, flight_filter):
        """The logbook for a filter and the current choices (non-flights shown or not, grouping, tree row).

        A selected tree row that does not exist for this filter any more is dropped (everything is listed).
        """
        filtered = apply_filter(self.table, flight_filter)
        flights = filtered[filtered["is_flight"].astype(bool)]
        groups = build_groups(flights, self.group_by)
        if self.group_selector is not None and self.group_selector not in all_selectors(groups):
            self.group_selector = None
        listed = self._listed(filtered, flights)
        return LogbookView(book=logbook(flights), groups=groups,
                           n_flights=len(flights), n_aircraft=len(aircraft_in(flights)), n_total=len(self.flights),
                           listed=listed)

    def listed(self, flight_filter):
        """Only the rows of the flight list (quick: no totals, no tree), e.g. after a click on a row of the tree."""
        filtered = apply_filter(self.table, flight_filter)
        return self._listed(filtered, filtered[filtered["is_flight"].astype(bool)])

    def _listed(self, filtered, flights):
        """The rows of the flight list: flights (and non-flights if shown) of the selected tree row; only those
        with a note or an open anomaly if that is chosen."""
        listed = select_flights(filtered if self.show_non_flights else flights, self.group_selector)
        if self.only_annotated:
            listed = listed[listed["has_note"] | (listed["open_rank"] > 0)]
        return listed

    def hint_lines(self, log_id):
        """The note and the open anomalies of a log, for the hint under the flight list: [(severity or "note",
        text)]."""
        connection = self._connection()
        if connection is None:
            return []
        lines = []
        note = annotations.note_of(connection, log_id)
        if note:
            lines.append(("note", note))
        lines += [(anomaly.severity, anomaly.text) for anomaly in annotations.anomalies_of(connection, log_id)
                  if not anomaly.acknowledged]
        return lines

    def summary(self):
        """Flights, non-flights, aircraft and period of the whole database."""
        flights = self.flights
        return DatabaseSummary(
            n_flights=len(flights), n_non_flights=len(self.table) - len(flights), n_aircraft=len(aircraft_in(flights)),
            first=flights["datum"].min() if len(flights) else None, last=flights["datum"].max() if len(flights) else None)

    # ---------------- changing the database ----------------
    def switch_flight(self, log_id):
        """Switches a log between flight and no flight by hand (a second switch undoes it).

        The page has to tell the database controller afterwards (``flights_changed``). Returns False if the
        log is not in the table or there is no database.
        """
        connection = self._connection()
        match = self.table[self.table["log_id"] == log_id]
        if connection is None or match.empty:
            return False
        row = match.iloc[0]
        flight_store.set_flight_manual(connection, int(log_id),
                                       manual_value_after_switch(bool(row["is_flight"]), bool(row["auto_flight"])))
        return True

