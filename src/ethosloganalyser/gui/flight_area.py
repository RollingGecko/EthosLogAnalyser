# -*- coding: utf-8 -*-
"""Area Single flight: the single-flight page filled with the flights of the flight database."""

from ..config import model_label
from ..i18n import N_, tr
from .database_flights import available_views, flight_choice_label, flight_path

EMPTY_DATABASE = N_("Noch keine Flüge in der Datenbank.\n\nLogs importieren: „Daten & Einstellungen“ → Bereich "
                    "„Datenbank“ → „Ordner importieren …“ oder „Dateien importieren …“.")
NO_BATTERY_DATA = N_("Für diesen Flug sind keine Spannungs- und Stromdaten des Flugakkus im Log.\n"
                     "Die Einzelflug-Ansichten brauchen sie bisher.")
PREPARING_FAILED = N_("Die Flüge von {aircraft} konnten nicht aus der Datenbank vorbereitet werden.")
PREPARING = N_("Die Flüge von {aircraft} werden aus der Datenbank vorbereitet …")
PREPARING_PROGRESS = N_("Vorbereitet: {done} von {total} Flügen")


class DatabaseFlightArea:
    """Connects a FlightPage with the FlightCache: flight list, views per flight, preparing in the background."""

    def __init__(self, page, cache, annotations_panel=None):
        self.page = page
        self.cache = cache
        self.annotations_panel = annotations_panel   # FlightAnnotationsPanel: note and anomalies of the flight
        self.waiting_for = None           # aircraft whose preparation the page is waiting for
        page.before_select = self._before_select
        page.message_for = self._message_for
        cache.add_listener(self._on_cache_change)
        page.frame.bind("<Destroy>", lambda event: cache.remove_listener(self._on_cache_change)
                        if event.widget is page.frame else None, add="+")

    def reload(self, force=False):
        """Fills the flight selector from the database (if it changed or force); keeps the selected flight."""
        changed = self.cache.refresh()
        if not (changed or force):
            return
        selected = self.page.current_key()
        choices = [(flight_choice_label(flight, model_label(flight.aircraft)), flight.log_id)
                   for flight in self.cache.flights]
        self.page.set_choices(choices, self._resolve, selected_key=selected, empty_message=tr(EMPTY_DATABASE))
        if not choices and self.annotations_panel is not None:
            self.annotations_panel.show_flight(None)
        if changed:
            self.cache.prepare_newest()

    def open_flight(self, log_id):
        """Selects and shows a flight (e.g. after a double-click in the logbook). False if it is not listed."""
        keys = [key for _label, key in self.page.choices]
        if log_id not in keys:
            return False
        self.page.flight_var.set(self.page.choices[keys.index(log_id)][0])
        self.page.select_flight()
        return True

    def find_flight(self, aircraft, start_time):
        """log_id of the database flight of this aircraft with this start time, None if there is not exactly one."""
        matches = [flight.log_id for flight in self.cache.flights
                   if flight.aircraft == aircraft and flight.start_time == start_time]
        return matches[0] if len(matches) == 1 else None

    # ---------------- callbacks of the page ----------------
    def _resolve(self, log_id):
        flight = self.cache.flight(log_id)
        if flight is None or not flight.has_metrics:
            return None
        prepared = self.cache.result(flight.aircraft)
        if prepared is None:
            return None
        result, params = prepared
        path = flight_path(log_id)
        return (result, params, path) if path in result.series else None

    def _before_select(self, log_id):
        self.waiting_for = None
        if self.annotations_panel is not None and self.annotations_panel.log_id != log_id:
            self.annotations_panel.show_flight(log_id)
        flight = self.cache.flight(log_id)
        views = available_views(self.cache.roles(log_id)) if flight is not None and flight.has_metrics else []
        self.page.show_views(views)

    def _message_for(self, log_id):
        flight = self.cache.flight(log_id)
        if flight is None:
            return ""
        if not flight.has_metrics:
            return tr(NO_BATTERY_DATA)
        if flight.aircraft in self.cache.failed:
            return tr(PREPARING_FAILED, aircraft=model_label(flight.aircraft))
        self.waiting_for = flight.aircraft
        return tr(PREPARING, aircraft=model_label(flight.aircraft))

    def _on_cache_change(self):
        """An aircraft is being prepared or became ready: update the page if it waits for it."""
        if self.waiting_for is None:
            return
        if self.waiting_for in self.cache.prepared:
            self.page.select_flight()
            return
        log_id = self.page.current_key()
        if log_id is None:
            return
        self.page.show_message(self._message_for(log_id))
        progress = self.cache.progress
        if progress is not None and progress[0] == self.waiting_for and progress[2]:
            self.page.readout.set(tr(PREPARING_PROGRESS, done=progress[1], total=progress[2]))
        if self.cache.task_aircraft is None:              # e.g. cancelled: start again
            self.cache.prepare(self.waiting_for)
