# -*- coding: utf-8 -*-
"""Page Data & settings: database, log folder with model selector, battery, analysis, anomaly rules, language,
export, about, skipped files."""

from ..buildinfo import about_lines
from ..config import CHEM, model_label
from ..i18n import LANGUAGES, get_language, tr
from .anomaly_settings_panel import AnomalySettingsPanel
from .common import scrollable_frame
from .database_panel import DatabasePanel
from .style import BG


class SettingsPage:
    """Widgets of Data & settings. actions: run, choose_folder, model_chosen(model), language(code),
    export_csv, export_all - functions of the main window."""

    def __init__(self, parent, window, actions):
        from tkinter import ttk
        self.window = window
        self.actions = actions
        # the page scrolls when the window is not tall enough for all sections (nothing is cut off)
        page = ttk.Frame(scrollable_frame(parent, BG), padding=14)
        page.pack(fill="both", expand=True)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(1, weight=1)
        self.db_panel = DatabasePanel(page, window.database, window.read_params, window.filedialog,
                                      window.messagebox)
        self.db_panel.frame.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 10))
        self._build_log_folder(page)
        self._build_battery(page)
        self._build_analysis(page)
        self.anomaly_panel = AnomalySettingsPanel(page, window.settings, window.anomalies, window.database)
        self.anomaly_panel.frame.grid(row=3, column=0, columnspan=2, sticky="we", pady=(10, 0))
        self._build_language(page)
        self._build_export(page)
        self._build_skipped(page)
        self._build_about(page, window.family)

    # ---------------- sections ----------------
    def _build_log_folder(self, page):
        import tkinter as tk
        from tkinter import ttk
        box = ttk.LabelFrame(page, text=tr("Logdaten"), padding=10)
        box.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 10))
        box.columnconfigure(1, weight=1)
        ttk.Label(box, text=tr("Ordner mit Ethos-CSV-Logs (Unterordner werden mit durchsucht):")).grid(
            row=0, column=0, columnspan=3, sticky="w")
        ttk.Button(box, text=tr("Ordner wählen …"), command=self.actions["choose_folder"]).grid(
            row=1, column=0, padx=(0, 8), pady=4)
        ttk.Entry(box, textvariable=self.window.settings.folder).grid(row=1, column=1, sticky="we", pady=4)
        self.run_button = ttk.Button(box, text=tr("Auswerten"), style="Accent.TButton", command=self.actions["run"])
        self.run_button.grid(row=1, column=2, padx=(8, 0), pady=4)
        self.progress = ttk.Progressbar(box, mode="determinate")
        self.progress.grid(row=2, column=0, columnspan=3, sticky="we", pady=(6, 0))
        # selection bar: which part of the folder is analysed (model; later more selectors fit in this row)
        self.model_bar = ttk.Frame(box)
        self.model_bar.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Label(self.model_bar, text=tr("Modell:")).pack(side="left")
        self.model_var = tk.StringVar()
        self.model_box = ttk.Combobox(self.model_bar, textvariable=self.model_var, width=30, state="readonly")
        self.model_box.pack(side="left", padx=(4, 8))
        ttk.Label(self.model_bar, text=tr("Im Ordner liegen Logs mehrerer Modelle; ausgewertet wird immer eines."),
                  foreground="#666").pack(side="left")
        self.model_keys = []
        self.model_box.bind("<<ComboboxSelected>>", self._on_model)

    def _field(self, parent, row, text, key, hint="", combo=None):
        from tkinter import ttk
        variable = self.window.settings.fields[key]
        ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=3)
        if combo:
            widget = ttk.Combobox(parent, textvariable=variable, values=combo, width=12, state="readonly")
        else:
            widget = ttk.Entry(parent, textvariable=variable, width=14)
        widget.grid(row=row, column=1, sticky="w", padx=8, pady=3)
        if hint:
            ttk.Label(parent, text=hint, foreground="#666").grid(row=row, column=2, sticky="w")
        return widget

    def _build_battery(self, page):
        from tkinter import ttk
        box = ttk.LabelFrame(page, text=tr("Akku"), padding=10)
        box.grid(row=2, column=0, sticky="nwe", padx=(0, 6))
        self.chem_box = self._field(box, 0, tr("Zellchemie"), "chem", tr("LiPo, LiHV oder Li-Ion"), list(CHEM.keys()))
        self._field(box, 1, tr("Zellenzahl"), "cells", tr("0 = automatisch aus der Startspannung"))
        self._field(box, 2, tr("Nennkapazität [mAh]"), "nominal_mah", tr("0 = unbekannt (wird geschätzt)"))
        self.chem_box.bind("<<ComboboxSelected>>", lambda _e: self.window.settings.confirm_battery())
        self.battery_hint = ttk.Label(box, text=tr("Für dieses Modell noch nicht eingestellt: bitte Zellchemie "
                                                   "auswählen und Nennkapazität eintragen (bis dahin wird LiPo "
                                                   "angenommen)."),
                                      foreground="#b00020", wraplength=520, justify="left")
        self.battery_hint.grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))

    def _build_analysis(self, page):
        from tkinter import ttk
        box = ttk.LabelFrame(page, text=tr("Auswertung"), padding=10)
        box.grid(row=2, column=1, sticky="nwe", padx=(6, 0))
        self._field(box, 0, tr("Min. Flugdauer [s]"), "min_flight_s", tr("kürzere Logs werden übersprungen"))
        self._field(box, 1, tr("Motor aktiv ab [A]"), "active_current_a", tr("Strom, ab dem der Flug zählt"))
        self._field(box, 2, tr("Reserve bei Landung [%]"), "reserve_pct", tr("für die Timer-Empfehlung"))
        self._field(box, 3, tr("Spalte Spannung (optional)"), "col_voltage", tr("Teil des Spaltennamens"))
        self._field(box, 4, tr("Spalte Strom (optional)"), "col_current", "")
        self._field(box, 5, tr("Zeitraum von"), "date_from", tr("TT.MM.JJJJ, leer = ohne Grenze"))
        self._field(box, 6, tr("Zeitraum bis"), "date_to", tr("z. B. nur die Flüge eines Akkus"))

    def _build_language(self, page):
        import tkinter as tk
        from tkinter import ttk
        box = ttk.LabelFrame(page, text=tr("Sprache (Language)"), padding=10)
        box.grid(row=4, column=0, sticky="nwe", padx=(0, 6), pady=10)
        self.lang_var = tk.StringVar(value=LANGUAGES[get_language()])
        lang_box = ttk.Combobox(box, textvariable=self.lang_var, values=list(LANGUAGES.values()), width=14,
                                state="readonly")
        lang_box.pack(side="left")
        ttk.Label(box, text=tr("wird gespeichert und beim nächsten Start verwendet"), foreground="#666").pack(
            side="left", padx=8)

        def on_language(*_):
            code = next((c for c, n in LANGUAGES.items() if n == self.lang_var.get()), None)
            # after_idle: do not destroy the combobox while its own event is still being processed
            self.window.root.after_idle(lambda: self.actions["language"](code))

        lang_box.bind("<<ComboboxSelected>>", on_language)

    def _build_export(self, page):
        from tkinter import ttk
        box = ttk.LabelFrame(page, text=tr("Export"), padding=10)
        box.grid(row=4, column=1, sticky="nwe", padx=(6, 0), pady=10)
        ttk.Button(box, text=tr("Tabelle als CSV speichern …"), command=self.actions["export_csv"]).pack(
            side="left", padx=(0, 8))
        ttk.Button(box, text=tr("Bericht + alle Diagramme speichern …"), command=self.actions["export_all"]).pack(
            side="left")

    def _build_skipped(self, page):
        from tkinter import ttk
        box = ttk.LabelFrame(page, text=tr("Übersprungene Dateien"), padding=6)
        box.grid(row=5, column=0, columnspan=2, sticky="nsew")
        page.rowconfigure(5, weight=1)
        self.skip_tree = ttk.Treeview(box, columns=("datei", "grund"), show="headings", height=8)
        self.skip_tree.heading("datei", text=tr("Datei"))
        self.skip_tree.heading("grund", text=tr("Grund"))
        self.skip_tree.column("datei", width=320, stretch=False)
        self.skip_tree.column("grund", width=700)
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=self.skip_tree.yview)
        self.skip_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.skip_tree.pack(fill="both", expand=True)

    @staticmethod
    def _build_about(page, family):
        from tkinter import ttk
        # about: version, and a clear marker on test builds from a pull request (see buildinfo.py)
        box = ttk.LabelFrame(page, text=tr("Über"), padding=10)
        box.grid(row=6, column=0, columnspan=2, sticky="we", pady=(10, 0))
        for kind, text in about_lines():
            ttk.Label(box, text=text, wraplength=900, foreground={"test": "#b00020", "info": "#666"}.get(kind),
                      font=(family, 10, "bold") if kind != "info" else None).pack(anchor="w")

    # ---------------- updates ----------------
    def update_model_box(self, models, current_model):
        """Shows the model selector only if the folder holds logs of more than one model."""
        self.model_keys[:] = sorted(models, key=lambda m: model_label(m).lower())
        self.model_box["values"] = [tr("{model} ({n} Logs)", model=model_label(m), n=models[m])
                                    for m in self.model_keys]
        if current_model in self.model_keys:
            self.model_box.current(self.model_keys.index(current_model))
        if len(models) > 1:
            self.model_bar.grid()
        else:
            self.model_bar.grid_remove()

    def _on_model(self, *_):
        k = self.model_box.current()
        if 0 <= k < len(self.model_keys):
            self.actions["model_chosen"](self.model_keys[k])

    def show_battery_hint(self, visible):
        if visible:
            self.battery_hint.grid()
        else:
            self.battery_hint.grid_remove()

    def show_skipped(self, skipped):
        self.skip_tree.delete(*self.skip_tree.get_children())
        for name, message in skipped:
            self.skip_tree.insert("", "end", values=(name, str(message)))

    def set_progress(self, done, total):
        self.progress["maximum"] = max(total, 1)
        self.progress["value"] = done
