# -*- coding: utf-8 -*-
"""Keeps the automatic anomalies of the open flight database up to date.

All flights are judged again in the background (db.annotations.recalculate_anomalies) after the flights changed
(database opened, import, recalculation, a log switched between flight and no flight) and after the rules or the
battery settings changed. Only stored values are used, so this takes well under a second; the window stays
usable all the time. Only one background task runs at a time: a request made while an import runs waits for it.
"""

from ..analysis.anomalies import RuleSettings
from ..db.annotations import recalculate_anomalies
from ..i18n import tr

DEBOUNCE_MS = 300      # several changes in a row (e.g. typing a threshold) cause one recalculation


class AnomalyController:
    """Starts the recalculation of the anomalies whenever it is needed."""

    def __init__(self, root, database, settings):
        self.root = root
        self.database = database          # DatabaseController
        self.settings = settings          # AppSettings (anomaly_rules, battery_for_anomalies)
        self.pending = False
        self.computed_signature = None    # settings the stored anomalies were calculated with
        self.last_count = None            # number of automatic anomalies of the last recalculation
        self._timer = None
        database.content_hooks.append(self.request)
        database.add_listener(self._start_if_pending)

    def _aircraft_names(self):
        connection = self.database.database.connection
        return [row[0] for row in connection.execute("SELECT name FROM aircraft ORDER BY name")]

    def _battery_settings(self):
        """{aircraft: battery settings or None} - read here in the main thread, the background task only uses it."""
        return {name: self.settings.battery_for_anomalies(name) for name in self._aircraft_names()}

    def settings_signature(self):
        """Rules and battery settings of all aircraft; the anomalies are recalculated when it changes."""
        if self.database.database is None:
            return None
        battery = {name: None if params is None else (params.chem, params.cells)
                   for name, params in self._battery_settings().items()}
        return self.settings.anomaly_rules.signature(), tuple(sorted(battery.items()))

    def request(self, delay_ms=0):
        """Judges all flights again as soon as no other background task runs."""
        self.pending = True
        if self._timer is not None:
            self.root.after_cancel(self._timer)
        self._timer = self.root.after(delay_ms, self._on_timer) if delay_ms else None
        if not delay_ms:
            self.root.after_idle(self._start_if_pending)

    def request_after_typing(self):
        """Like request, but waits a moment so that typing a number causes only one recalculation."""
        self.request(DEBOUNCE_MS)

    def check_settings(self):
        """Recalculates if the rules or battery settings changed since the last recalculation."""
        if self.database.database is not None and self.settings_signature() != self.computed_signature:
            self.request()

    def _on_timer(self):
        self._timer = None
        self._start_if_pending()

    def _start_if_pending(self):
        if not self.pending or self._timer is not None or self.database.busy or self.database.database is None:
            return
        self.pending = False
        rules = RuleSettings.from_dict(self.settings.anomaly_rules.to_dict())     # a copy for the other thread
        battery = self._battery_settings()
        self.computed_signature = self.settings_signature()

        def work(database, progress, should_cancel):
            return recalculate_anomalies(database.connection, rules, battery.get,
                                         progress=lambda done, total: progress(done, total, tr("Auffälligkeiten")),
                                         should_cancel=should_cancel)

        def finished(count):
            self.last_count = count

        if not self.database.run_annotation_task(work, finished):
            self.pending = True
