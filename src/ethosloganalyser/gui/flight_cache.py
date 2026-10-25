# -*- coding: utf-8 -*-
"""Keeps the database flights ready for the single-flight page.

Preparing an aircraft (analysing the stored time series of all its flights, database_flights.prepare_aircraft)
takes a few seconds, so it runs in the background, once per aircraft until the database changes. The
cross-flight result is then calculated on demand for the current battery settings (fast).
"""

import dataclasses

from ..db import flight_store
from . import database_flights
from .database_panel import BackgroundTask


class FlightCache:
    """Database flights, sensor roles and prepared aircraft of the open database."""

    def __init__(self, root, database, params_for):
        self.root = root
        self.database = database              # DatabaseController
        self.params_for = params_for          # aircraft -> config.Params (battery settings of that aircraft)
        self.generation = None
        self.flights = []
        self.prepared = {}                    # aircraft -> {log_id: (row, series)}
        self.results = {}                     # aircraft -> (params, Result)
        self.failed = set()                   # aircraft whose preparation raised an error (not tried again)
        self.task = None
        self.task_aircraft = None
        self.progress = None                  # (aircraft, done, total) while an aircraft is prepared
        self.listeners = []                   # called when an aircraft is being prepared or became ready
        # while paused (program start), a preparation is only noted and starts on resume(): the background
        # work would otherwise slow down drawing the window for the first time
        self.paused = False
        self.pending = None

    # ---------------- database state ----------------
    def refresh(self):
        """Reads the flight list again if the database changed. Returns True if it did."""
        if self.generation == self.database.generation:
            return False
        self.generation = self.database.generation
        self._cancel_task()
        self.prepared, self.results, self.failed = {}, {}, set()
        connection = self._connection()
        self.flights = database_flights.stored_flights(connection) if connection is not None else []
        return True

    def _connection(self):
        database = self.database.database
        return database.connection if database is not None else None

    def flight(self, log_id):
        return next((flight for flight in self.flights if flight.log_id == log_id), None)

    def roles(self, log_id):
        connection = self._connection()
        return flight_store.sensor_roles_of(connection, log_id) if connection is not None else {}

    # ---------------- prepared aircraft ----------------
    def result(self, aircraft):
        """(Result, params) of an aircraft if it is prepared, otherwise None (and the preparation starts)."""
        prepared = self.prepared.get(aircraft)
        if prepared is None:
            self.prepare(aircraft)
            return None
        params = self.params_for(aircraft)
        cached = self.results.get(aircraft)
        if cached is None or dataclasses.astuple(cached[0]) != dataclasses.astuple(params):
            cached = (params, database_flights.aircraft_result(prepared, params, aircraft))
            self.results[aircraft] = cached
        return cached[1], params

    def prepare(self, aircraft):
        """Starts preparing an aircraft in the background (nothing happens if it is ready or running)."""
        if (aircraft in self.prepared or aircraft in self.failed or self.task_aircraft == aircraft
                or self.database.path == ""):
            return
        if self.paused:
            self.pending = aircraft
            return
        self._cancel_task()
        params = self.params_for(aircraft)
        generation = self.generation

        def work(database, progress, should_cancel):
            return database_flights.prepare_aircraft(database.connection, aircraft, params, progress=progress,
                                                     should_cancel=should_cancel)

        def on_progress(done, total, *_):
            self.progress = (aircraft, done, total)
            self._notify()

        def on_done(kind, value):
            if self.task is not task:
                return                                  # cancelled meanwhile
            self.task, self.task_aircraft, self.progress = None, None, None
            if kind == "error":
                self.failed.add(aircraft)
            elif value is not None and generation == self.generation:
                self.prepared[aircraft] = value
            self._notify()

        task = BackgroundTask(self.root, self.database.path, work, on_progress, on_done)
        self.task, self.task_aircraft, self.progress = task, aircraft, (aircraft, 0, 0)
        task.start()

    def resume(self):
        """Ends the pause of the program start and starts the noted preparation."""
        self.paused = False
        pending, self.pending = self.pending, None
        if pending is not None:
            self.prepare(pending)

    def prepare_newest(self):
        """Prepares the aircraft of the newest flight, so that opening a flight is quick."""
        if self.flights:
            self.prepare(self.flights[-1].aircraft)

    def _cancel_task(self):
        if self.task is not None:
            self.task.cancel_requested.set()
        self.task, self.task_aircraft, self.progress = None, None, None

    def close(self):
        if self.task is not None:
            self.task.cancel_and_wait()
        self.task = None

    def add_listener(self, listener):
        """listener() is called while an aircraft is prepared and when it became ready."""
        self.listeners.append(listener)

    def remove_listener(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)

    def _notify(self):
        for listener in list(self.listeners):
            listener()
