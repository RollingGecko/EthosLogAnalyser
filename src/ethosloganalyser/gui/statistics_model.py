# -*- coding: utf-8 -*-
"""What the statistics show, worked out from the flight database (no Tkinter here).

The statistics cover the flights of the database that pass the shared filter (``flight_filter.FilterState``),
never non-flights, and always exactly one aircraft: models are never mixed in one analysis. If the filtered
flights belong to several aircraft, the statistics ask for an aircraft to be chosen in the filter.

The per-flight analysis of the stored time series is the one the single flight uses (``FlightCache``: prepared
once per aircraft in the background). The cross-flight part (``analysis.fleet.analyse_flights``) is calculated
for the filtered flights only - a fraction of a second - and kept until the filter, the flights or the battery
settings change.
"""

import dataclasses
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from ..analysis.periods import aircraft_in, apply_filter
from ..config import model_label
from ..i18n import N_, fmt_date, tr
from .database_flights import aircraft_result

# states of the statistics
READY = "ready"                       # result is there
EMPTY_DATABASE = "empty_database"     # no flights in the database
NO_MATCH = "no_match"                 # no flight passes the filter
SEVERAL_AIRCRAFT = "several_aircraft" # the filtered flights belong to more than one aircraft
NO_BATTERY_DATA = "no_battery_data"   # the filtered flights have no battery voltage and current (e.g. a glider)
PREPARING = "preparing"               # the flights of the aircraft are being prepared in the background
FAILED = "failed"                     # preparing the aircraft failed

MESSAGES = {
    EMPTY_DATABASE: N_("Noch keine Flüge in der Datenbank. Logs importieren: „Daten & Einstellungen“ → "
                       "„Datenbank“ → „Ordner importieren …“ oder „Dateien importieren …“."),
    NO_MATCH: N_("Kein Flug passt zum Filter."),
    SEVERAL_AIRCRAFT: N_("Bitte im Filter ein Flugzeug wählen: Die Statistik wertet immer genau ein Flugzeug aus "
                         "(gefiltert sind Flüge von {aircraft})."),
    NO_BATTERY_DATA: N_("Für diese Flüge von {aircraft} sind keine Spannungs- und Stromdaten des Flugakkus im Log. "
                        "Die Statistik-Seiten brauchen sie bisher."),
    PREPARING: N_("Die Flüge von {aircraft} werden aus der Datenbank vorbereitet …"),
    FAILED: N_("Die Flüge von {aircraft} konnten nicht aus der Datenbank vorbereitet werden."),
}

# shown at the top of the summary and of the exported report
EXPERIMENTAL_NOTICE = N_("Dieser Bereich ist noch experimentell: Werte und Auswertungen können sich ändern.")


@dataclass
class StatisticsView:
    """Everything the statistics show for the current filter."""
    state: str
    aircraft: Optional[str] = None        # the analysed aircraft (READY, PREPARING, ...)
    n_flights: int = 0                    # flights that pass the filter
    n_total: int = 0                      # flights in the database
    first: object = None                  # date of the first and the last filtered flight
    last: object = None
    result: object = None                 # analysis.fleet.Result (READY)
    params: object = None                 # config.Params used (READY)
    aircraft_names: tuple = ()            # aircraft of the filtered flights

    @property
    def message(self):
        """Text shown instead of the statistics ("" when READY)."""
        if self.state == READY:
            return ""
        names = ", ".join(model_label(name) for name in self.aircraft_names) if self.state == SEVERAL_AIRCRAFT \
            else model_label(self.aircraft)
        return tr(MESSAGES[self.state], aircraft=names)


def flight_table(flights):
    """The database flights (FlightCache.flights) as a table the filter works on: log_id, aircraft, datum,
    has_metrics."""
    return pd.DataFrame({"log_id": [flight.log_id for flight in flights],
                         "aircraft": [flight.aircraft for flight in flights],
                         "datum": pd.to_datetime([flight.start_time for flight in flights]),
                         "has_metrics": [flight.has_metrics for flight in flights]})


MAX_LISTED = 2        # up to this many chosen years or months are named in the filter text, more are counted


def years_description(years):
    """The chosen years in words: "2025", "2024, 2025", "3 Jahre" (counted when there are many), "keine Jahre"."""
    if not years:
        return tr("keine Jahre")
    if len(years) > MAX_LISTED:
        return tr("{count} Jahre", count=len(years))
    return ", ".join(str(year) for year in sorted(years))


def months_description(months):
    """The chosen months in words: "Monat 06", "Monate 06, 07", "3 Monate" (counted when there are many),
    "keine Monate"."""
    if not months:
        return tr("keine Monate")
    if len(months) > MAX_LISTED:
        return tr("{count} Monate", count=len(months))
    if len(months) == 1:
        return tr("Monat {month:02d}", month=next(iter(months)))
    return tr("Monate {months}", months=", ".join(f"{month:02d}" for month in sorted(months)))


def filter_description(flight_filter):
    """The filter in words, without the aircraft (for the status line and the report); "" without a filter."""
    parts = []
    if flight_filter.year is not None:
        parts.append(years_description(flight_filter.year))
    if flight_filter.month is not None:
        parts.append(months_description(flight_filter.month))
    if flight_filter.date_from is not None or flight_filter.date_to is not None:
        start = fmt_date(flight_filter.date_from) if flight_filter.date_from is not None else "…"
        end = fmt_date(flight_filter.date_to) if flight_filter.date_to is not None else "…"
        parts.append(f"{start} – {end}")
    return ", ".join(parts)


class StatisticsModel:
    """The statistics of the open database for the shared filter."""

    def __init__(self, cache, filter_state, params_for):
        self.cache = cache                  # FlightCache
        self.filter_state = filter_state    # FilterState shared with the logbook
        self.params_for = params_for        # aircraft -> config.Params (battery settings of that aircraft)
        self._table = flight_table([])
        self._table_generation = None
        self._result_key = None
        self._result = None

    def table(self):
        """The flights of the database as a filter table (read again when the flight list of the cache changed;
        the cache itself is refreshed by the single-flight area when the database changes)."""
        if self._table_generation != self.cache.generation:
            self._table = flight_table(self.cache.flights)
            self._table_generation = self.cache.generation
        return self._table

    def view(self, prepare=True):
        """The statistics for the current filter. prepare: start preparing the aircraft if it is not ready yet
        (only while the statistics are shown, so the single flight is not slowed down otherwise)."""
        table = self.table()
        filtered = apply_filter(table, self.filter_state.value)
        view = StatisticsView(state=READY, n_flights=len(filtered), n_total=len(table),
                              first=filtered["datum"].min() if len(filtered) else None,
                              last=filtered["datum"].max() if len(filtered) else None,
                              aircraft_names=tuple(aircraft_in(filtered)))
        if not len(table):
            return dataclasses.replace(view, state=EMPTY_DATABASE)
        if not len(filtered):
            return dataclasses.replace(view, state=NO_MATCH)
        if len(view.aircraft_names) > 1:
            return dataclasses.replace(view, state=SEVERAL_AIRCRAFT)
        aircraft = view.aircraft_names[0]
        view.aircraft = aircraft
        if not filtered["has_metrics"].any():
            return dataclasses.replace(view, state=NO_BATTERY_DATA)
        prepared = self.cache.prepared.get(aircraft)
        if prepared is None:
            if aircraft in self.cache.failed:
                return dataclasses.replace(view, state=FAILED)
            if prepare:
                self.cache.prepare(aircraft)
            return dataclasses.replace(view, state=PREPARING)
        params = self.params_for(aircraft)
        log_ids = tuple(int(log_id) for log_id in filtered["log_id"])
        view.result, view.params = self._result_for(prepared, params, aircraft, log_ids), params
        return view

    def _result_for(self, prepared, params, aircraft, log_ids):
        """The cross-flight analysis of these flights, calculated again only when something changed."""
        key = (id(prepared), aircraft, log_ids, dataclasses.astuple(params))
        if key != self._result_key:
            self._result = aircraft_result(prepared, params, aircraft, log_ids)
            self._result_key = key
        return self._result
