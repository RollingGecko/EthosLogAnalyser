# -*- coding: utf-8 -*-
"""The settings of the window: input fields of Data & settings, battery settings per model, saving.

The settings live as long as the window (they survive a language switch, which rebuilds all widgets).
"""

from ..analysis.fleet import parse_date
from ..config import Params, save_settings
from ..i18n import N_, get_language, tr

# battery settings that are kept per model, with their defaults for a model without stored settings
BATTERY_KEYS = ("chem", "cells", "nominal_mah")
BATTERY_DEFAULTS = {"chem": "LiPo", "cells": "0", "nominal_mah": "0"}
# key in the stored settings of a model whose battery fields still hold only the defaults (nobody has chosen
# the cell chemistry or entered the capacity yet); see AppSettings.battery_unset
BATTERY_UNSET_KEY = "unset"

# input fields of Data & settings: key -> default (as text, like the entry shows it)
FIELD_DEFAULTS = {
    "chem": "LiPo", "cells": "0", "nominal_mah": "0", "min_flight_s": "120", "active_current_a": "1.0",
    "reserve_pct": "20", "col_voltage": "", "col_current": "", "date_from": "", "date_to": "",
}

BATTERY_HINT = N_("Für das Modell {model} sind noch keine Akku-Einstellungen gespeichert: Bitte im Reiter "
                  "„Daten & Einstellungen“ die Zellchemie auswählen und die Nennkapazität eintragen. Bis dahin "
                  "wird LiPo angenommen – Ladezustand, Alterung und Restkapazität können falsch sein.")


def battery_unset_for(model, model_settings, saved):
    """True if the battery settings of model would be only the defaults (no cell chemistry chosen, no capacity
    entered): a model without stored settings while other models have some, a stored model still marked as
    unset, or the very first model when the settings file has no battery settings from before models existed."""
    if model in model_settings:
        return bool(model_settings[model].get(BATTERY_UNSET_KEY))
    if model_settings:
        return True
    return not any(k in saved for k in BATTERY_KEYS)


class AppSettings:
    """Input fields (Tk variables), the battery settings of every model and the folder; saved as JSON."""

    def __init__(self, root, saved):
        import tkinter as tk
        self.saved = saved
        self.fields = {key: tk.StringVar(master=root, value=saved.get(key, default))
                       for key, default in FIELD_DEFAULTS.items()}
        self.folder = tk.StringVar(master=root, value=saved.get("folder", ""))
        # several aircraft: logs are analysed per model (from the file name, see
        # io.ethos_log.model_from_filename); the battery settings are kept per model
        self.model = saved.get("model")                    # model the battery fields belong to
        self.model_settings = dict(saved.get("models") or {})
        # True while the battery fields of the current model hold only the defaults (LiPo, automatic cell
        # count, capacity unknown). The assumed LiPo does not count as a setting; the hint disappears once the
        # user picks the cell chemistry or enters a capacity (confirm_battery).
        self.battery_unset = bool(self.model_settings.get(self.model, {}).get(BATTERY_UNSET_KEY))
        self.on_battery_confirmed = None                   # called when battery_unset becomes False
        self.fields["nominal_mah"].trace_add("write", self._on_capacity)

    def model_battery(self):
        """Battery settings of the current model as they are stored."""
        stored = {k: self.fields[k].get() for k in BATTERY_KEYS}
        if self.battery_unset:
            stored[BATTERY_UNSET_KEY] = True
        return stored

    def store(self, database_path=""):
        """Writes all settings to the settings file."""
        stored = {k: v.get() for k, v in self.fields.items()}
        stored["folder"] = self.folder.get()
        stored["language"] = get_language()
        if self.model is not None:
            self.model_settings[self.model] = self.model_battery()
            stored["model"] = self.model
        stored["models"] = self.model_settings
        if database_path:
            stored["database"] = database_path
        save_settings(stored)

    def use_model(self, model):
        """Makes model the analysed one: the battery fields are kept for the old model and loaded for the new
        one. The settings from before models existed stay with the first model; another model without stored
        settings starts with the defaults."""
        if model == self.model:
            return
        settings = self.model_settings
        if self.model is not None:
            settings[self.model] = self.model_battery()
        unset = battery_unset_for(model, settings, self.saved)
        if model in settings:
            for k in BATTERY_KEYS:
                self.fields[k].set(settings[model].get(k, BATTERY_DEFAULTS[k]))
        elif settings:
            for k in BATTERY_KEYS:
                self.fields[k].set(BATTERY_DEFAULTS[k])
        # else: the first model takes over the settings from before models existed, if any
        self.model = model
        self.battery_unset = unset

    def confirm_battery(self):
        """The user chose the cell chemistry or entered a capacity: the battery hint is no longer needed."""
        if self.battery_unset:
            self.battery_unset = False
            if self.on_battery_confirmed is not None:
                self.on_battery_confirmed()

    def _on_capacity(self, *_):
        try:
            if float(self.fields["nominal_mah"].get().replace(",", ".")) > 0:
                self.confirm_battery()
        except ValueError:
            pass

    def read_params(self, messagebox):
        """The analysis parameters from the input fields, or None after showing an input error."""
        fields = self.fields
        try:
            d0, d1 = parse_date(fields["date_from"].get()), parse_date(fields["date_to"].get())
        except ValueError:
            messagebox.showerror(tr("Eingabefehler"), tr("Bitte ein gültiges Datum eintragen (TT.MM.JJJJ) oder das "
                                                        "Feld leer lassen."))
            return None
        if d0 and d1 and d0 > d1:
            messagebox.showerror(tr("Eingabefehler"), tr("Der Beginn des Zeitraums liegt nach dem Ende."))
            return None
        try:
            num = lambda k: float(fields[k].get().replace(",", "."))
            return Params(cells=int(num("cells")), chem=fields["chem"].get(), nominal_mah=num("nominal_mah"),
                          min_flight_s=num("min_flight_s"), active_current_a=num("active_current_a"),
                          reserve_pct=num("reserve_pct"), col_voltage=fields["col_voltage"].get().strip(),
                          col_current=fields["col_current"].get().strip(),
                          date_from=d0.isoformat() if d0 else "", date_to=d1.isoformat() if d1 else "")
        except ValueError:
            messagebox.showerror(tr("Eingabefehler"), tr("Bitte gültige Zahlen in den Einstellungen eintragen."))
            return None
