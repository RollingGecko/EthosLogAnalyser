# -*- coding: utf-8 -*-
"""What the logbook shows, worked out from the flight database (no Tkinter here).

``LogbookModel`` reads the flights of the open database into the logbook flight table
(``db/logbook_table.py``) and answers: which flights pass the filter, what are their totals, how do they group
in the tree and which rows does the flight list show. The table is read again only when the database changed
or the battery settings changed (they decide which battery values count).
"""

import dataclasses
from dataclasses import dataclass

import pandas as pd

from ..analysis.logbook import Logbook, logbook
from ..analysis.logbook_groups import GROUP_BY_TIME, all_selectors, build_groups, select_flights
from ..analysis.periods import aircraft_in, apply_filter, years_in
from ..db import flight_store
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
        self.table = empty_logbook_table()
        self._signature = None
        # choices of the logbook page; kept here so they survive rebuilding the window (language switch)
        self.show_non_flights = False
        self.group_by = GROUP_BY_TIME
        self.group_selector = None               # selector of the selected row of the tree, None = all

    # ---------------- reading the database ----------------
    def _connection(self):
        database = self.database.database
        return database.connection if database is not None else None

    def _battery_signature(self):
        """The battery settings of all aircraft in the table; a change makes the battery validity stale."""
        return tuple(dataclasses.astuple(self.params_for(name)) for name in aircraft_in(self.table))

    def refresh(self):
        """Reads the table again if the database or the battery settings changed. True if it did."""
        generation = self.database.generation
        if self._signature == (generation, self._battery_signature()):
            return False
        connection = self._connection()
        rows = flight_store.logbook_rows(connection) if connection is not None else pd.DataFrame()
        self.table = build_logbook_table(rows, self.params_for)
        self._signature = (generation, self._battery_signature())
        return True

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
        """The rows of the flight list: flights (and non-flights if shown) of the selected tree row."""
        return select_flights(filtered if self.show_non_flights else flights, self.group_selector)

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

