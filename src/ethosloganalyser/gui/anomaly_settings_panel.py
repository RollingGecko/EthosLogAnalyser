# -*- coding: utf-8 -*-
"""Section "Anomalies" on the page Data & settings: every rule on or off, its threshold, and the receiver
minimum voltage per aircraft.

A change is stored in the settings (AppSettings.anomaly_rules) at once and the anomalies are judged again in the
background a moment later (AnomalyController).
"""

from ..analysis.anomalies import RULES, THRESHOLD_HINTS
from ..config import model_label
from ..i18n import tr

RULES_PER_COLUMN = 5


def number_or_none(text):
    """A number typed by the user (decimal comma allowed); None if the text is not a number of 0 or more."""
    try:
        value = float(str(text).strip().replace(",", "."))
    except ValueError:
        return None
    return value if value >= 0 else None


def format_number(value):
    return f"{value:g}"


class AnomalySettingsPanel:
    """Widgets of the section; settings: AppSettings, controller: AnomalyController, database: DatabaseController."""

    def __init__(self, parent, settings, controller, database):
        import tkinter as tk
        from tkinter import ttk

        self.settings = settings
        self.controller = controller
        self.database = database
        rules = settings.anomaly_rules
        self._showing = False                 # True while the panel fills a field itself
        self.frame = ttk.LabelFrame(parent, text=tr("Auffälligkeiten"), padding=10)
        ttk.Label(self.frame, text=tr("Regeln für die automatischen Hinweise je Flug (immer nur Hinweise, keine "
                                      "Diagnose). Vergleiche mit dem Median gelten ab 5 Flügen eines Flugzeugs."),
                  foreground="#666").grid(row=0, column=0, columnspan=8, sticky="w", pady=(0, 6))
        self.enabled, self.thresholds = {}, {}
        for position, rule in enumerate(RULES):
            row, column = 1 + position % RULES_PER_COLUMN, 4 * (position // RULES_PER_COLUMN)
            self.enabled[rule.code] = tk.BooleanVar(value=rules.is_enabled(rule.code))
            ttk.Checkbutton(self.frame, text=tr(rule.label), variable=self.enabled[rule.code],
                            command=self._changed).grid(row=row, column=column, sticky="w", pady=1)
            if rule.threshold is not None:
                variable = tk.StringVar(value=format_number(rules.threshold(rule.code)))
                variable.trace_add("write", lambda *_args: self._changed())
                self.thresholds[rule.code] = variable
                ttk.Entry(self.frame, textvariable=variable, width=6).grid(row=row, column=column + 1, padx=(6, 2))
                ttk.Label(self.frame, text=f"{rule.unit} {tr(THRESHOLD_HINTS[rule.code])}".strip(),
                          foreground="#666").grid(row=row, column=column + 2, sticky="w", padx=(0, 20))
            elif rule.code == "rx_voltage_limit":
                self._build_receiver_limit(row, column)
        self.status = tk.StringVar()
        ttk.Label(self.frame, textvariable=self.status, foreground="#666").grid(
            row=1 + RULES_PER_COLUMN, column=0, columnspan=8, sticky="w", pady=(6, 0))
        database.add_listener(self.refresh)
        self.frame.bind("<Destroy>", lambda event: database.remove_listener(self.refresh)
                        if event.widget is self.frame else None)
        self.refresh()

    def _build_receiver_limit(self, row, column):
        """Aircraft selector and minimum voltage of that aircraft (empty or 0 = off)."""
        import tkinter as tk
        from tkinter import ttk
        cell = ttk.Frame(self.frame)
        cell.grid(row=row, column=column + 1, columnspan=2, sticky="w", padx=(6, 0))
        self.aircraft_names = []
        self.aircraft_box = ttk.Combobox(cell, state="readonly", width=16)
        self.aircraft_box.pack(side="left")
        self.aircraft_box.bind("<<ComboboxSelected>>", lambda _event: self._show_receiver_limit())
        self.receiver_limit = tk.StringVar()
        ttk.Entry(cell, textvariable=self.receiver_limit, width=6).pack(side="left", padx=(6, 2))
        ttk.Label(cell, text=tr("V (leer = aus)"), foreground="#666").pack(side="left")
        self.receiver_limit.trace_add("write", lambda *_args: self._receiver_limit_changed())

    # ---------------- display ----------------
    def refresh(self):
        """Aircraft of the database in the selector, and the state of the anomalies."""
        names = []
        if self.database.database is not None:
            names = [row[0] for row in self.database.database.connection.execute(
                "SELECT name FROM aircraft ORDER BY name")]
        if names != self.aircraft_names:
            selected = self.selected_aircraft()
            self.aircraft_names = names
            self.aircraft_box["values"] = [model_label(name) for name in names]
            if names:
                self.aircraft_box.current(names.index(selected) if selected in names else 0)
            self._show_receiver_limit()
        count = self.controller.last_count
        self.status.set(tr("Zuletzt gefunden: {n} automatische Hinweise.", n=count) if count is not None else "")

    def selected_aircraft(self):
        position = self.aircraft_box.current() if self.aircraft_names else -1
        return self.aircraft_names[position] if 0 <= position < len(self.aircraft_names) else None

    def _show_receiver_limit(self):
        value = self.settings.anomaly_rules.rx_min_voltage.get(self.selected_aircraft(), 0.0)
        self._showing = True                 # filling the field is no change by the user
        self.receiver_limit.set(format_number(value) if value > 0 else "")
        self._showing = False

    # ---------------- changes ----------------
    def _changed(self):
        rules = self.settings.anomaly_rules
        for code, variable in self.enabled.items():
            rules.enabled[code] = bool(variable.get())
        for code, variable in self.thresholds.items():
            value = number_or_none(variable.get())
            if value is not None:                     # an incomplete number keeps the last valid one
                rules.thresholds[code] = value
        self.controller.request_after_typing()

    def _receiver_limit_changed(self):
        aircraft = self.selected_aircraft()
        if self._showing or aircraft is None:
            return
        text = self.receiver_limit.get().strip()
        value = number_or_none(text) if text else 0.0
        if value is None:
            return
        self.settings.anomaly_rules.rx_min_voltage[aircraft] = value
        self.controller.request_after_typing()
