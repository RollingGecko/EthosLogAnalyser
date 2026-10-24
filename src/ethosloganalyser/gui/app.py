# -*- coding: utf-8 -*-
"""Main window of the app (Tkinter).

The window content is built by ``build()``. When the user switches the language, the content is destroyed
and built again in the new language; the analysis result, the settings, the selected flight, view, zoom
and tab are kept, so the logs do not have to be analysed again.
"""

import os
import numpy as np

from ..analysis.evaluate import FLAG_LABELS
from ..buildinfo import about_lines, window_title
from ..analysis.quality import QUALITY_LABELS
from ..analysis.fleet import analyse_folder, default_model, find_logs, models_in, parse_date
from ..config import (CHEM, MODEL_UNKNOWN_LABEL, SPIKE_LABELS, VOLTAGE_SOURCE_LABELS, Params, label, load_settings,
                      model_label, save_settings)
from ..gui.style import BG, _setup_style
from ..i18n import LANGUAGES, Msg, N_, detect_language, fmt_datetime, get_language, set_language, tr
from ..plots.flight import FLIGHT_VIEWS, VIEW_LABELS, draw_flight, figure_flight, fit_y
from ..plots.overview import figure_akku, figure_antrieb, figure_belastung, figure_funk
from ..report.text import flight_detail_lines, summary_lines
from ..plots.hover import Hover
from ..plots.single import chart_index, chart_title, single_chart
from ..utils import _mmss, fmt_duration


TABLE_COLS = [
    ("Flug", N_("Flug"), 45), ("datum", N_("Datum"), 120), ("dauer_s", N_("Dauer min:s"), 75),
    ("entnommen_mAh", N_("entnommen mAh"), 90), ("ESC_mAh", N_("ESC mAh"), 65), ("Sensor_Abw_pct", N_("Abw. %"), 55),
    ("energie_Wh", N_("Energie Wh"), 75), ("I_mittel_A", N_("Ø A"), 50), ("I_max_A", N_("max A"), 55),
    ("P_max_W", N_("P max W"), 65), ("C_peak", N_("C Spitze"), 60), ("SoC_start_pct", N_("SoC Start %"), 75),
    ("SoC_ende_pct", N_("SoC Ende %"), 75), ("SoC_ende_U_pct", N_("SoC Ende (U) %"), 90),
    ("SoC_Abw_pct", N_("SoC Abw. Pkt"), 80), ("Kap_gesch_mAh", N_("Kapazität mAh"), 90),
    ("Kap_norm_mAh", N_("Kapazität normiert"), 105),
    ("Ri_Zelle_mOhm", N_("Ri/Zelle mΩ"), 80), ("Ri_Anf_Zelle_mOhm", N_("Ri Anfang"), 70),
    ("Ri_End_Zelle_mOhm", N_("Ri Ende"), 65), ("U_ref_Zelle_V", N_("U Ref V/Z"), 70),
    ("U_min_Zelle_V", N_("U min V/Z"), 70), ("U_ende_Zelle_V", N_("U Ende V/Z"), 75),
    ("U_ende_Quelle", N_("U Ende Quelle"), 85), ("Reserve_Zelle_V", N_("Reserve V/Z"), 80),
    ("Timer_s", N_("Timer min:s"), 75), ("rpm_p90", N_("rpm P90"), 70), ("P_ref_W", N_("P Ref W"), 65),
    ("P_Kurve_Abw_pct", N_("P Abw. Kurve %"), 95),
    ("Hoehe_max_m", N_("Höhe max"), 65), ("Wh_je_100m", N_("Wh/100m"), 65), ("g_max", N_("g max"), 50),
    ("RSSI_min", N_("RSSI min"), 65), ("VFR_min", N_("VFR min"), 60), ("RxBatt_min_V", N_("Rx V min"), 65),
    ("RxStrom_mittel_A", N_("Rx A Ø"), 55), ("RxStrom_max_A", N_("Rx A max"), 65),
    ("RxSpitzen_n", N_("Rx Spitzen"), 70), ("RxSp_Schalter", N_("Sp. Schalter"), 80),
    ("RxSp_ohne", N_("Sp. o. Anlass"), 85), ("Rx_r_Knueppel", N_("r Rx/Knüppel"), 85),
    ("fit_R2", N_("R² Fit"), 50), ("versatz_s", N_("Versatz s"), 60), ("Auffaellig", N_("Auffälligkeiten"), 260),
    ("Datenfehler", N_("Messfehler"), 260),
]


def flag_text(codes):
    """Column "Auffaellig" (comma-separated flag codes) as text in the current language."""
    return ", ".join(label(FLAG_LABELS, c) for c in str(codes).split(", ") if c)


def error_text(codes):
    """Column "Datenfehler" (comma-separated data-error codes) as text in the current language."""
    return ", ".join(label(QUALITY_LABELS, c) for c in str(codes).split(", ") if c)


# durations [s] shown as min:s (table) and exported additionally as min:s text columns (CSV)
DURATION_COLS = ["dauer_s", "Timer_s", "Zeit_80_s", "t_steig_s", "t_reise_s", "t_sink_s"]


def fmt_cell(key, v):
    if key in DURATION_COLS:
        return fmt_duration(v)
    if key == "datum":
        return fmt_datetime(v)
    if key == "U_ende_Quelle":
        return label(VOLTAGE_SOURCE_LABELS, v)
    if key == "Auffaellig":
        return flag_text(v)
    if key == "Datenfehler":
        return error_text(v)
    if isinstance(v, (float, np.floating)):
        return "–" if not np.isfinite(v) else f"{v:.5g}"
    return "" if v is None else str(v)


def export_table(df):
    """Result table for the CSV export: internal columns removed, text columns in the current language.

    Durations stay in seconds (columns ..._s, unchanged for existing evaluations); a text column ..._mmss with
    min:s follows each of them.
    """
    out = df.drop(columns=["pfad", "P_a", "P_n", "k_V_je_Ah"], errors="ignore").copy()
    for col in DURATION_COLS:
        if col in out:
            out.insert(out.columns.get_loc(col) + 1, col[:-2] + "_mmss", [fmt_duration(v, na="") for v in out[col]])
    if "Modell" in out:
        out["Modell"] = [model_label(v) for v in out["Modell"]]
    if "U_ende_Quelle" in out:
        out["U_ende_Quelle"] = [label(VOLTAGE_SOURCE_LABELS, v) for v in out["U_ende_Quelle"]]
    if "Auffaellig" in out:
        out["Auffaellig"] = [flag_text(v) for v in out["Auffaellig"]]
    if "Datenfehler" in out:
        out["Datenfehler"] = [error_text(v) for v in out["Datenfehler"]]
    return out


# battery settings that are kept per model, with their defaults for a model without stored settings
BATTERY_KEYS = ("chem", "cells", "nominal_mah")
BATTERY_DEFAULTS = {"chem": "LiPo", "cells": "0", "nominal_mah": "0"}
# key in the stored settings of a model whose battery fields still hold only the defaults (nobody has chosen
# the cell chemistry or entered the capacity yet); see battery_unset in run_gui
BATTERY_UNSET_KEY = "unset"


def battery_unset_for(model, model_settings, saved):
    """True if the battery settings of model would be only the defaults (no cell chemistry chosen, no capacity
    entered): a model without stored settings while other models have some, a stored model still marked as
    unset, or the very first model when the settings file has no battery settings from before models existed."""
    if model in model_settings:
        return bool(model_settings[model].get(BATTERY_UNSET_KEY))
    if model_settings:
        return True
    return not any(k in saved for k in BATTERY_KEYS)


BATTERY_HINT = N_("Für das Modell {model} sind noch keine Akku-Einstellungen gespeichert: Bitte im Reiter "
                  "„Daten & Einstellungen“ die Zellchemie auswählen und die Nennkapazität eintragen. Bis dahin "
                  "wird LiPo angenommen – Ladezustand, Alterung und Restkapazität können falsch sein.")


def run_gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure

    try:                                         # sharp rendering on Windows
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()
    root.geometry("1400x950")
    root.configure(background=BG)
    fam = _setup_style(root)

    # ---------------- state that survives a language switch ----------------
    saved = load_settings()
    set_language(saved.get("language") or detect_language())
    state = {"res": None, "p": None, "figs": {}, "path": None, "folder": "",
             "status": Msg("Noch nicht ausgewertet – Ordner und Akku im Reiter „Daten & Einstellungen“ festlegen.")}
    folder_var = tk.StringVar(value=saved.get("folder", ""))
    V = {
        "chem": tk.StringVar(value=saved.get("chem", "LiPo")), "cells": tk.StringVar(value=saved.get("cells", "0")),
        "nominal_mah": tk.StringVar(value=saved.get("nominal_mah", "0")),
        "min_flight_s": tk.StringVar(value=saved.get("min_flight_s", "120")),
        "active_current_a": tk.StringVar(value=saved.get("active_current_a", "1.0")),
        "reserve_pct": tk.StringVar(value=saved.get("reserve_pct", "20")),
        "col_voltage": tk.StringVar(value=saved.get("col_voltage", "")),
        "col_current": tk.StringVar(value=saved.get("col_current", "")),
        "date_from": tk.StringVar(value=saved.get("date_from", "")),
        "date_to": tk.StringVar(value=saved.get("date_to", "")),
    }
    ui = {"frame": None}
    # several aircraft: the logs of one folder are analysed per model (from the file name, see
    # io.ethos_log.model_from_filename). The battery settings are kept per model.
    state["models"] = {}                                   # {model: number of logs} of the last analysed folder
    state["model"] = saved.get("model")                    # model the battery fields in V belong to
    state["model_settings"] = dict(saved.get("models") or {})
    # True while the battery fields of the current model hold only the defaults (LiPo, automatic cell count,
    # capacity unknown): a model without stored settings, or a first start without any battery settings.
    # The assumed LiPo does not count as a setting; the hint disappears once the user picks the cell chemistry
    # or enters a capacity (confirm_battery).
    state["battery_unset"] = bool(state["model_settings"].get(state["model"], {}).get(BATTERY_UNSET_KEY))

    def model_battery():
        """Battery settings of the current model as they are stored."""
        d = {k: V[k].get() for k in BATTERY_KEYS}
        if state["battery_unset"]:
            d[BATTERY_UNSET_KEY] = True
        return d

    def store_settings():
        d = {k: v.get() for k, v in V.items()}
        d["folder"] = folder_var.get()
        d["language"] = get_language()
        if state["model"] is not None:
            state["model_settings"][state["model"]] = model_battery()
            d["model"] = state["model"]
        d["models"] = state["model_settings"]
        save_settings(d)

    def use_model(model):
        """Makes model the analysed one: the battery fields are kept for the old model and loaded for the new
        one. The settings from before models existed stay with the first model; another model without stored
        settings starts with the defaults."""
        if model == state["model"]:
            return
        ms = state["model_settings"]
        if state["model"] is not None:
            ms[state["model"]] = model_battery()
        unset = battery_unset_for(model, ms, saved)
        if model in ms:
            for k in BATTERY_KEYS:
                V[k].set(ms[model].get(k, BATTERY_DEFAULTS[k]))
        elif ms:
            for k in BATTERY_KEYS:
                V[k].set(BATTERY_DEFAULTS[k])
        # else: the first model takes over the settings from before models existed, if any
        state["model"] = model
        state["battery_unset"] = unset

    def confirm_battery():
        """The user chose the cell chemistry or entered a capacity: the battery hint is no longer needed."""
        if state["battery_unset"]:
            state["battery_unset"] = False
            if ui.get("battery_hint"):
                ui["battery_hint"]()

    def on_capacity(*_):
        try:
            if float(V["nominal_mah"].get().replace(",", ".")) > 0:
                confirm_battery()
        except ValueError:
            pass

    V["nominal_mah"].trace_add("write", on_capacity)

    def change_language(code):
        """Switches the language and builds the window content again (the analysis result is kept)."""
        if code == get_language() or code not in LANGUAGES:
            return
        snap = ui["snapshot"]()
        set_language(code)
        store_settings()
        build(snap)

    def build(snap=None):
        """Builds the complete window content in the current language."""
        if ui["frame"] is not None:
            ui["frame"].destroy()
        root.title(window_title())
        main = ttk.Frame(root)
        main.pack(fill="both", expand=True)
        ui["frame"] = main

        # ---------------- status bar ----------------
        status = tk.StringVar(value=str(state["status"]))
        ttk.Label(main, textvariable=status, style="Status.TLabel").pack(fill="x")

        def set_status(msg):
            state["status"] = msg
            status.set(str(msg))

        nb = ttk.Notebook(main)
        nb.pack(fill="both", expand=True, padx=6, pady=(4, 6))
        tabs, tab_titles, fullscreen = {}, {}, []
        page_canvases = {}
        for key, title in [("settings", tr("Daten & Einstellungen")), ("summary", tr("Zusammenfassung")),
                           ("akku", tr("Akku")), ("belastung", tr("Belastung & Flugprofil")), ("antrieb", tr("Antrieb")),
                           ("funk", tr("Funk & Bordnetz")), ("flight", tr("Einzelflug")), ("table", tr("Tabelle"))]:
            fr = ttk.Frame(nb)
            nb.add(fr, text=title)
            tabs[key] = fr
            tab_titles[key] = title

        def make_text(parent, height=None):
            kw = dict(wrap="word", font=(fam, 10), padx=12, pady=8, relief="flat", background="#ffffff",
                      borderwidth=0, highlightthickness=0)
            if height:
                kw["height"] = height
            t_ = tk.Text(parent, **kw)
            t_.tag_configure("h", font=(fam, 11, "bold"), spacing1=10, spacing3=3, foreground="#1f3b73")
            t_.tag_configure("ok", foreground="#1b7f3b")
            t_.tag_configure("warn", foreground="#b36b00")
            t_.tag_configure("bad", foreground="#b00020")
            t_.tag_configure("info")
            return t_

        def fill_text(t_, lines):
            t_.configure(state="normal")
            t_.delete("1.0", "end")
            for tag, line in lines:
                t_.insert("end", line + "\n", tag)
            t_.configure(state="disabled")

        # ---------------- tab: data & settings ----------------
        st_tab = ttk.Frame(tabs["settings"], padding=14)
        st_tab.pack(fill="both", expand=True)
        st_tab.columnconfigure(0, weight=1)
        st_tab.columnconfigure(1, weight=1)

        lf = ttk.LabelFrame(st_tab, text=tr("Logdaten"), padding=10)
        lf.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 10))
        lf.columnconfigure(1, weight=1)
        ttk.Label(lf, text=tr("Ordner mit Ethos-CSV-Logs (Unterordner werden mit durchsucht):")).grid(
            row=0, column=0, columnspan=3, sticky="w")
        ttk.Button(lf, text=tr("Ordner wählen …"), command=lambda: choose()).grid(row=1, column=0, padx=(0, 8), pady=4)
        ttk.Entry(lf, textvariable=folder_var).grid(row=1, column=1, sticky="we", pady=4)
        run_btn = ttk.Button(lf, text=tr("Auswerten"), style="Accent.TButton", command=lambda: run())
        run_btn.grid(row=1, column=2, padx=(8, 0), pady=4)
        prog = ttk.Progressbar(lf, mode="determinate")
        prog.grid(row=2, column=0, columnspan=3, sticky="we", pady=(6, 0))
        # selection bar: which part of the folder is analysed (model; later more selectors fit in this row)
        selbar = ttk.Frame(lf)
        selbar.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Label(selbar, text=tr("Modell:")).pack(side="left")
        model_var = tk.StringVar()
        model_box = ttk.Combobox(selbar, textvariable=model_var, width=30, state="readonly")
        model_box.pack(side="left", padx=(4, 8))
        ttk.Label(selbar, text=tr("Im Ordner liegen Logs mehrerer Modelle; ausgewertet wird immer eines."),
                  foreground="#666").pack(side="left")
        model_keys = []

        def update_model_box():
            """Shows the model selector only if the folder holds logs of more than one model."""
            models = state["models"]
            model_keys[:] = sorted(models, key=lambda m: model_label(m).lower())
            model_box["values"] = [tr("{model} ({n} Logs)", model=model_label(m), n=models[m]) for m in model_keys]
            if state["model"] in model_keys:
                model_box.current(model_keys.index(state["model"]))
            if len(models) > 1:
                selbar.grid()
            else:
                selbar.grid_remove()

        def on_model(*_):
            k = model_box.current()
            if 0 <= k < len(model_keys) and model_keys[k] != state["model"]:
                model = model_keys[k]
                root.after_idle(lambda: (use_model(model), run()))

        model_box.bind("<<ComboboxSelected>>", on_model)
        update_model_box()

        def field(parent, row, text, key, hint="", combo=None):
            ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=3)
            if combo:
                w = ttk.Combobox(parent, textvariable=V[key], values=combo, width=12, state="readonly")
            else:
                w = ttk.Entry(parent, textvariable=V[key], width=14)
            w.grid(row=row, column=1, sticky="w", padx=8, pady=3)
            if hint:
                ttk.Label(parent, text=hint, foreground="#666").grid(row=row, column=2, sticky="w")
            return w

        lf = ttk.LabelFrame(st_tab, text=tr("Akku"), padding=10)
        lf.grid(row=1, column=0, sticky="nwe", padx=(0, 6))
        chem_box = field(lf, 0, tr("Zellchemie"), "chem", tr("LiPo, LiHV oder Li-Ion"), list(CHEM.keys()))
        field(lf, 1, tr("Zellenzahl"), "cells", tr("0 = automatisch aus der Startspannung"))
        field(lf, 2, tr("Nennkapazität [mAh]"), "nominal_mah", tr("0 = unbekannt (wird geschätzt)"))
        chem_box.bind("<<ComboboxSelected>>", lambda _e: confirm_battery())
        battery_hint = ttk.Label(lf, text=tr("Für dieses Modell noch nicht eingestellt: bitte Zellchemie auswählen "
                                             "und Nennkapazität eintragen (bis dahin wird LiPo angenommen)."),
                                 foreground="#b00020", wraplength=520, justify="left")
        battery_hint.grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))

        lf = ttk.LabelFrame(st_tab, text=tr("Auswertung"), padding=10)
        lf.grid(row=1, column=1, sticky="nwe", padx=(6, 0))
        field(lf, 0, tr("Min. Flugdauer [s]"), "min_flight_s", tr("kürzere Logs werden übersprungen"))
        field(lf, 1, tr("Motor aktiv ab [A]"), "active_current_a", tr("Strom, ab dem der Flug zählt"))
        field(lf, 2, tr("Reserve bei Landung [%]"), "reserve_pct", tr("für die Timer-Empfehlung"))
        field(lf, 3, tr("Spalte Spannung (optional)"), "col_voltage", tr("Teil des Spaltennamens"))
        field(lf, 4, tr("Spalte Strom (optional)"), "col_current", "")
        field(lf, 5, tr("Zeitraum von"), "date_from", tr("TT.MM.JJJJ, leer = ohne Grenze"))
        field(lf, 6, tr("Zeitraum bis"), "date_to", tr("z. B. nur die Flüge eines Akkus"))

        lf = ttk.LabelFrame(st_tab, text=tr("Sprache (Language)"), padding=10)
        lf.grid(row=2, column=0, sticky="nwe", padx=(0, 6), pady=10)
        names = list(LANGUAGES.values())
        lang_var = tk.StringVar(value=LANGUAGES[get_language()])
        lang_box = ttk.Combobox(lf, textvariable=lang_var, values=names, width=14, state="readonly")
        lang_box.pack(side="left")
        ttk.Label(lf, text=tr("wird gespeichert und beim nächsten Start verwendet"), foreground="#666").pack(
            side="left", padx=8)

        def on_language(*_):
            code = next((c for c, n in LANGUAGES.items() if n == lang_var.get()), None)
            # after_idle: do not destroy the combobox while its own event is still being processed
            root.after_idle(lambda: change_language(code))

        lang_box.bind("<<ComboboxSelected>>", on_language)

        lf = ttk.LabelFrame(st_tab, text=tr("Export"), padding=10)
        lf.grid(row=2, column=1, sticky="nwe", padx=(6, 0), pady=10)
        ttk.Button(lf, text=tr("Tabelle als CSV speichern …"), command=lambda: export_csv()).pack(side="left", padx=(0, 8))
        ttk.Button(lf, text=tr("Bericht + alle Diagramme speichern …"), command=lambda: export_all()).pack(side="left")

        # about: version, and a clear marker on test builds from a pull request (see buildinfo.py)
        lf = ttk.LabelFrame(st_tab, text=tr("Über"), padding=10)
        lf.grid(row=4, column=0, columnspan=2, sticky="we", pady=(10, 0))
        for kind, text in about_lines():
            ttk.Label(lf, text=text, wraplength=900, foreground={"test": "#b00020", "info": "#666"}.get(kind),
                      font=(fam, 10, "bold") if kind != "info" else None).pack(anchor="w")

        lf = ttk.LabelFrame(st_tab, text=tr("Übersprungene Dateien"), padding=6)
        lf.grid(row=3, column=0, columnspan=2, sticky="nsew")
        st_tab.rowconfigure(3, weight=1)
        skip_tree = ttk.Treeview(lf, columns=("datei", "grund"), show="headings", height=8)
        skip_tree.heading("datei", text=tr("Datei"))
        skip_tree.heading("grund", text=tr("Grund"))
        skip_tree.column("datei", width=320, stretch=False)
        skip_tree.column("grund", width=700)
        sk_sb = ttk.Scrollbar(lf, orient="vertical", command=skip_tree.yview)
        skip_tree.configure(yscrollcommand=sk_sb.set)
        sk_sb.pack(side="right", fill="y")
        skip_tree.pack(fill="both", expand=True)

        # ---------------- tab: summary ----------------
        txt = make_text(tabs["summary"])
        sb = ttk.Scrollbar(tabs["summary"], orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)

        # ---------------- tab: single flight ----------------
        ft = tabs["flight"]
        bar = ttk.Frame(ft, padding=(6, 6, 6, 2))
        bar.pack(fill="x")
        ttk.Label(bar, text=tr("Flug:")).pack(side="left")
        flight_var = tk.StringVar()
        flight_box = ttk.Combobox(bar, textvariable=flight_var, width=46, state="readonly")
        flight_box.pack(side="left", padx=(4, 4))
        ttk.Button(bar, text=tr("‹ zurück"), command=lambda: step_flight(-1)).pack(side="left")
        ttk.Button(bar, text=tr("vor ›"), command=lambda: step_flight(1)).pack(side="left", padx=(2, 14))
        details_btn = ttk.Button(bar, text=tr("Details ausblenden"), command=lambda: toggle_details())
        details_btn.pack(side="right")
        ttk.Button(bar, text=tr("Bild speichern …"), command=lambda: save_flight_png()).pack(side="right", padx=6)
        ttk.Button(bar, text=tr("Ganze Seite vergrößern"),
                   command=lambda: open_fullscreen(flight_builder, tr("Einzelflug"), flight=True)).pack(side="right")

        # views in a row of their own: the labels are much longer in some languages
        vbar = ttk.Frame(ft, padding=(6, 0, 6, 4))
        vbar.pack(fill="x")
        ttk.Label(vbar, text=tr("Ansicht:")).pack(side="left", padx=(0, 4))
        view_var = tk.StringVar(value=FLIGHT_VIEWS[0])
        for v_ in FLIGHT_VIEWS:
            ttk.Radiobutton(vbar, text=label(VIEW_LABELS, v_), value=v_, variable=view_var, style="View.TRadiobutton",
                            command=lambda: redraw_flight()).pack(side="left", padx=1)

        zbar = ttk.Frame(ft, padding=(6, 0, 6, 4))
        zbar.pack(fill="x")
        ttk.Label(zbar, text=tr("Zeit:")).pack(side="left")
        for txt_, cmd in [(tr("Ganzer Flug"), lambda: zoom_to(None)), (tr("Start (60 s)"), lambda: zoom_to("start")),
                          (tr("Landung (60 s)"), lambda: zoom_to("end")), (tr("Zoom +"), lambda: zoom_by(1 / 1.5)),
                          (tr("Zoom −"), lambda: zoom_by(1.5)), (tr("‹ früher"), lambda: pan_by(-0.3)),
                          (tr("später ›"), lambda: pan_by(0.3))]:
            ttk.Button(zbar, text=txt_, command=cmd).pack(side="left", padx=1)
        ttk.Label(zbar, text="   " + tr("Stromspitze:")).pack(side="left")
        spike_var = tk.StringVar()
        spike_box = ttk.Combobox(zbar, textvariable=spike_var, width=44, state="readonly")
        spike_box.pack(side="left", padx=4)

        readout = tk.StringVar(value=tr("Maus über das Diagramm bewegen: Werte zum Zeitpunkt.   Mausrad: zoomen  ·  "
                                        "Ziehen mit linker Maustaste: verschieben  ·  Doppelklick oder Rechtsklick: Diagramm "
                                        "vergrößern"))
        ttk.Label(ft, textvariable=readout, style="Readout.TLabel").pack(fill="x", padx=6)

        paned = ttk.PanedWindow(ft, orient="vertical")
        paned.pack(fill="both", expand=True, padx=6, pady=4)
        plot_frame = ttk.Frame(paned)
        det_frame = ttk.Frame(paned)
        paned.add(plot_frame, weight=4)
        paned.add(det_frame, weight=1)
        det_txt = make_text(det_frame, height=10)
        dsb = ttk.Scrollbar(det_frame, orient="vertical", command=det_txt.yview)
        det_txt.configure(yscrollcommand=dsb.set)
        dsb.pack(side="right", fill="y")
        det_txt.pack(side="left", fill="both", expand=True)

        flight_fig = Figure(figsize=(12, 7), dpi=100)
        fs = {"axes": [], "drag": None, "details": True, "spikes": []}

        def flight_builder():
            """Current flight, view and zoom as a new figure (for the full-screen window)."""
            fig = Figure(figsize=(12, 7), dpi=100)
            path = current_path()
            if path is not None:
                axes = draw_flight(fig, state["res"], state["p"], path, view_var.get())
                if axes and fs["axes"]:
                    axes[0].set_xlim(fs["axes"][0].get_xlim())
            return fig

        def show_readout(x):
            t = getattr(flight_fig, "_t", None)
            if x is None or t is None:
                return
            k = int(np.clip(np.searchsorted(t, x), 0, len(t) - 1))
            parts = [f"t = {fmt_duration(t[k])}"]
            for name, unit, y in flight_fig._readout:
                if y is not None and k < len(y) and np.isfinite(y[k]):
                    parts.append(f"{name} {y[k]:.4g} {unit}")
            readout.set("   ·   ".join(parts))

        flight_canvas = FigureCanvasTkAgg(flight_fig, master=plot_frame)
        flight_canvas._hover = Hover(flight_canvas, crosshair=True, on_move=show_readout)
        flight_canvas.get_tk_widget().pack(fill="both", expand=True)

        # ---------------- tab: table ----------------
        cols = [c[0] for c in TABLE_COLS]
        tree = ttk.Treeview(tabs["table"], columns=cols, show="headings")
        for key, head, w in TABLE_COLS:
            tree.heading(key, text=tr(head))
            tree.column(key, width=w, anchor="center", stretch=False)
        ysb = ttk.Scrollbar(tabs["table"], orient="vertical", command=tree.yview)
        xsb = ttk.Scrollbar(tabs["table"], orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        ysb.pack(side="right", fill="y")
        xsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        # ---------------- functions ----------------
        def choose():
            d = filedialog.askdirectory(title=tr("Ordner mit Ethos-Logfiles wählen"), initialdir=folder_var.get() or None)
            if d:
                folder_var.set(d)

        def read_params():
            try:
                d0, d1 = parse_date(V["date_from"].get()), parse_date(V["date_to"].get())
            except ValueError:
                messagebox.showerror(tr("Eingabefehler"), tr("Bitte ein gültiges Datum eintragen (TT.MM.JJJJ) oder das "
                                                            "Feld leer lassen."))
                return None
            if d0 and d1 and d0 > d1:
                messagebox.showerror(tr("Eingabefehler"), tr("Der Beginn des Zeitraums liegt nach dem Ende."))
                return None
            try:
                num = lambda k: float(V[k].get().replace(",", "."))
                return Params(cells=int(num("cells")), chem=V["chem"].get(), nominal_mah=num("nominal_mah"),
                              min_flight_s=num("min_flight_s"), active_current_a=num("active_current_a"),
                              reserve_pct=num("reserve_pct"), col_voltage=V["col_voltage"].get().strip(),
                              col_current=V["col_current"].get().strip(),
                              date_from=d0.isoformat() if d0 else "", date_to=d1.isoformat() if d1 else "")
            except ValueError:
                messagebox.showerror(tr("Eingabefehler"), tr("Bitte gültige Zahlen in den Einstellungen eintragen."))
                return None

        def chart_canvas(parent, fig, builder, title, crosshair=False, on_move=None, flight=False, whole_page=True):
            """Canvas with toolbar and tooltip (plots/hover.py) - the same for every chart.

            With a builder (function that draws the page again): a double-click or the context menu (right-click)
            enlarges the chart under the mouse on its own; the toolbar button enlarges the whole page.
            whole_page=False: the canvas already shows the whole page (full-screen window) - no button and no menu
            entry for it, but double-click and "Enlarge this chart" still work. flight: single-flight page.
            """
            canvas = FigureCanvasTkAgg(fig, master=parent)
            toolbar = NavigationToolbar2Tk(canvas, parent)
            if builder is not None and whole_page:
                ttk.Button(toolbar, text=tr("Ganze Seite vergrößern"), command=lambda: open_fullscreen(builder, title)).pack(
                    side="left", padx=6)
                ttk.Label(toolbar, text=tr("Doppelklick oder Rechtsklick auf ein Diagramm: allein vergrößern"),
                          foreground="#666", background=toolbar.cget("background")).pack(side="left", padx=6)
            toolbar.update()
            canvas._hover = Hover(canvas, crosshair=crosshair, on_move=on_move)     # keep a reference
            if builder is not None:
                def on_press(ev):
                    if ev.inaxes is None or getattr(toolbar.mode, "name", "NONE") != "NONE":
                        return                            # zoom/pan mode of the toolbar uses the mouse buttons
                    if ev.dblclick:
                        open_chart(canvas, builder, title, ev.inaxes, flight=flight)
                    elif ev.button == 3:
                        chart_menu(ev, canvas, builder, title, flight=flight, whole_page=whole_page)
                canvas.mpl_connect("button_press_event", on_press)
            canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
            return canvas

        def chart_menu(ev, canvas, builder, title, flight=False, whole_page=True):
            """Context menu of a chart: enlarge this chart or (whole_page) the whole page."""
            if ev.inaxes is None:
                return
            ax = ev.inaxes
            menu = tk.Menu(root, tearoff=0)
            menu.add_command(label=tr("Dieses Diagramm vergrößern"),
                             command=lambda: open_chart(canvas, builder, title, ax, flight=flight))
            if whole_page:
                menu.add_command(label=tr("Ganze Seite vergrößern"),
                                 command=lambda: open_fullscreen(builder, title, flight=flight))
            gui = getattr(ev, "guiEvent", None)
            x, y = (gui.x_root, gui.y_root) if gui is not None and hasattr(gui, "x_root") else (
                root.winfo_pointerx(), root.winfo_pointery())
            try:
                menu.tk_popup(x, y)
            finally:
                menu.grab_release()

        def open_chart(canvas, builder, title, ax, flight=False):
            """The chart ax of the page shown in canvas on its own in a full-screen window."""
            return open_fullscreen(builder, title, index=chart_index(canvas.figure, ax), flight=flight)

        def open_fullscreen(builder, title, index=None, flight=False):
            """A page (index None) or one chart of it (index of its axes) in its own window filling the screen.

            The page is drawn again by builder; for one chart all other charts are removed (plots/single.py).
            flight: single-flight chart - the window gets the button "Whole flight". Esc closes the window.
            """
            fig = builder()
            axes = []
            if index is not None and index < len(fig.axes):
                axes = single_chart(fig, index)
                name = chart_title(axes[0])
                if name:
                    title = f"{name} – {title}"
            elif flight:
                axes = [a for a in fig.axes if a.get_subplotspec() is not None]
            win = tk.Toplevel(root)
            win.title(tr("{title} – Vollbild (Esc schließt)", title=title))
            win.configure(background=BG)
            try:
                win.state("zoomed")                       # Windows
            except tk.TclError:
                try:
                    win.attributes("-zoomed", True)       # Linux
                except tk.TclError:
                    win.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
            bar = ttk.Frame(win)
            bar.pack(side="top", fill="x")

            def close(*_):
                if win in fullscreen:
                    fullscreen.remove(win)
                win.destroy()

            ttk.Button(bar, text=tr("Schließen (Esc)"), command=close).pack(side="right", padx=6, pady=2)
            is_flight = flight and getattr(fig, "_t", None) is not None and axes
            if is_flight:
                def whole_flight():
                    t = fig._t
                    axes[0].set_xlim(t[0], t[-1])
                    fit_y(axes)
                    canvas.draw_idle()
                ttk.Button(bar, text=tr("Ganzer Flug"), command=whole_flight).pack(side="right", padx=6, pady=2)
                fit_y(axes)                               # y range of the zoomed time window, as in the tab
            ttk.Label(bar, text=tr("Maus über einen Datenpunkt: Wert.  Werkzeugleiste unten: zoomen, verschieben, "
                                   "speichern."), foreground="#666").pack(side="left", padx=6)
            page_builder = None
            if index is None:
                # whole page: a double-click (or right-click) on one of its charts enlarges that chart on its own,
                # as on the normal page. Single-flight pages keep the time window zoomed in this window.
                def page_builder():
                    f = builder()
                    if getattr(f, "_t", None) is not None and f.axes and fig.axes:
                        f.axes[0].set_xlim(fig.axes[0].get_xlim())
                    return f
            canvas = chart_canvas(win, fig, page_builder, title, crosshair=getattr(fig, "_t", None) is not None,
                                  flight=flight, whole_page=False)
            canvas.draw()
            win.bind("<Escape>", close)
            win.protocol("WM_DELETE_WINDOW", close)
            win.focus_set()
            fullscreen.append(win)
            win._fig = fig                                # for tests
            return win

        def show_fig(frame, fig, builder=None, title=""):
            for w in frame.winfo_children():
                w.destroy()
            canvas = chart_canvas(frame, fig, builder, title)
            canvas.draw()
            page_canvases[str(frame)] = canvas

        def tab_canvas(key):
            """Canvas of the chart page in tab key (for tests)."""
            return page_canvases.get(str(tabs[key]))

        def flight_label(r):
            return f"{int(r['Flug'])} | {fmt_datetime(r['datum'])} | {_mmss(r['dauer_s'])} | {r['entnommen_mAh']:.0f} mAh"

        # --- single flight: drawing, zoom, crosshair ---
        def current_path():
            res = state["res"]
            if res is None or res.df.empty or not flight_var.get():
                return None
            no = int(flight_var.get().split("|")[0])
            return res.df.loc[res.df["Flug"] == no, "pfad"].iloc[0]

        def redraw_flight(*_, keep_zoom=True):
            path = current_path()
            if path is None:
                return
            old = fs["axes"][0].get_xlim() if (keep_zoom and fs["axes"] and state["path"] == path) else None
            fs["axes"] = draw_flight(flight_fig, state["res"], state["p"], path, view_var.get())
            if old and fs["axes"]:
                fs["axes"][0].set_xlim(old)
                autoscale_y()
            state["path"] = path
            flight_canvas.draw_idle()

        def select_flight(*_):
            path = current_path()
            if path is None:
                return
            res = state["res"]
            state["path"] = None
            redraw_flight(keep_zoom=False)
            fill_text(det_txt, flight_detail_lines(res, state["p"], path))
            rx = res.series[path].get("rx")
            items = []
            if rx:
                items = [f"{fmt_duration(sp['t'])} – {sp['peak']:.2f} A – {label(SPIKE_LABELS, sp['anlass'])}"
                         + (f" ({sp['schalter']})" if sp["schalter"] else "") for sp in rx["spikes"]]
            fs["spikes"] = [sp["t"] for sp in rx["spikes"]] if rx else []
            spike_box["values"] = items
            spike_var.set("" if items else tr("keine Spitzen"))

        def step_flight(d):
            vals = list(flight_box["values"])
            if not vals:
                return
            i = vals.index(flight_var.get()) if flight_var.get() in vals else len(vals) - 1
            flight_var.set(vals[max(0, min(len(vals) - 1, i + d))])
            select_flight()

        def full_range():
            path = current_path()
            t = state["res"].series[path]["t"]
            return float(t[0]), float(t[-1])

        def set_xlim(lo, hi):
            if not fs["axes"]:
                return
            t0, t1 = full_range()
            span = min(max(hi - lo, 3.0), t1 - t0)
            lo = max(t0, min(lo, t1 - span))
            fs["axes"][0].set_xlim(lo, lo + span)
            autoscale_y()
            flight_canvas.draw_idle()

        def autoscale_y():
            """Fit the y axes to the visible time window."""
            fit_y(fs["axes"])

        def zoom_to(where):
            if not fs["axes"]:
                return
            t0, t1 = full_range()
            if where is None:
                set_xlim(t0, t1)
            elif where == "start":
                set_xlim(t0, t0 + 60)
            else:
                set_xlim(t1 - 60, t1)

        def zoom_by(f, center=None):
            if not fs["axes"]:
                return
            lo, hi = fs["axes"][0].get_xlim()
            c = (lo + hi) / 2 if center is None else center
            set_xlim(c - (c - lo) * f, c + (hi - c) * f)

        def pan_by(frac):
            if not fs["axes"]:
                return
            lo, hi = fs["axes"][0].get_xlim()
            d = (hi - lo) * frac
            set_xlim(lo + d, hi + d)

        def goto_spike(*_):
            vals = list(spike_box["values"])
            if spike_var.get() not in vals:
                return
            t_ = fs["spikes"][vals.index(spike_var.get())]
            set_xlim(t_ - 10, t_ + 10)

        spike_box.bind("<<ComboboxSelected>>", goto_spike)

        def on_scroll(ev):
            if ev.inaxes is None or ev.xdata is None:
                return
            zoom_by(1 / 1.25 if ev.button == "up" else 1.25, center=ev.xdata)

        def on_press(ev):
            if ev.inaxes is None or ev.xdata is None:
                return
            if ev.dblclick:
                fs["drag"] = None
                open_chart(flight_canvas, flight_builder, tr("Einzelflug"), ev.inaxes, flight=True)
                return
            if ev.button == 3:
                chart_menu(ev, flight_canvas, flight_builder, tr("Einzelflug"), flight=True)
                return
            if ev.button == 1:
                fs["drag"] = (ev.x, fs["axes"][0].get_xlim())

        def on_release(ev):
            fs["drag"] = None

        def on_motion(ev):
            if fs["drag"] is not None and ev.x is not None and fs["axes"]:
                x0, (lo, hi) = fs["drag"]
                bbox = fs["axes"][0].get_window_extent()
                dt = (ev.x - x0) / max(bbox.width, 1) * (hi - lo)
                set_xlim(lo - dt, hi - dt)
                return
            # tooltip, crosshair and read-out: plots/hover.py (show_readout)

        for ev_name, fn in [("scroll_event", on_scroll), ("button_press_event", on_press),
                            ("button_release_event", on_release), ("motion_notify_event", on_motion)]:
            flight_canvas.mpl_connect(ev_name, fn)

        def toggle_details():
            if fs["details"]:
                paned.forget(det_frame)
                details_btn.configure(text=tr("Details einblenden"))
            else:
                paned.add(det_frame, weight=1)
                details_btn.configure(text=tr("Details ausblenden"))
            fs["details"] = not fs["details"]

        def save_flight_png():
            path = current_path()
            if path is None:
                return
            f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
            if f:
                flight_fig.savefig(f, dpi=150)

        flight_box.bind("<<ComboboxSelected>>", select_flight)

        # --- analysis and display of the result ---
        def run():
            folder = folder_var.get()
            if not folder or not os.path.isdir(folder):
                messagebox.showwarning(tr("Ordner"), tr("Bitte zuerst einen gültigen Ordner wählen."))
                return
            groups = models_in(find_logs(folder))
            model = state["model"] if state["model"] in groups else default_model(groups)
            use_model(model)                              # battery settings of that model
            show_battery_hint()
            p = read_params()
            if p is None:
                return
            store_settings()
            set_status(Msg("Werte aus …"))
            run_btn.state(["disabled"])
            root.update_idletasks()

            def cb(n, tot):
                prog["maximum"] = max(tot, 1)
                prog["value"] = n
                root.update_idletasks()

            try:
                res = analyse_folder(folder, p, cb, model=model)
            except Exception as e:                       # unexpected error: report it understandably
                messagebox.showerror(tr("Fehler bei der Auswertung"), f"{type(e).__name__}: {e}")
                set_status(Msg("Fehler bei der Auswertung."))
                return
            finally:
                run_btn.state(["!disabled"])
            state["res"], state["p"], state["folder"] = res, p, folder
            state["models"] = res.meta.get("models", {})
            update_model_box()
            cells = res.meta.get("cells", p.cells)
            cap = f", {p.nominal_mah:.0f} mAh" if p.nominal_mah > 0 else Msg(", Kapazität unbekannt")
            status_args = dict(folder=os.path.basename(os.path.normpath(folder)), n=len(res.df),
                               skipped=len(res.skipped), total=res.total, cells=cells, chem=p.chem, cap=cap)
            if len(state["models"]) > 1:
                set_main_status(Msg("{folder}  ·  Modell {model}  ·  {n} Flüge ausgewertet, {skipped} von {total} Dateien "
                               "übersprungen  ·  Akku {cells}S {chem}{cap}",
                               model=model if model else Msg(MODEL_UNKNOWN_LABEL), **status_args))
            else:
                set_main_status(Msg("{folder}  ·  {n} Flüge ausgewertet, {skipped} von {total} Dateien "
                                    "übersprungen  ·  Akku {cells}S {chem}{cap}", **status_args))
            show_results()
            nb.select(tabs["summary"])

        def set_main_status(msg):
            """Status line after an analysis; while the battery of the model is not set up it names that."""
            state["status_main"] = msg
            shown = Msg("{status}  ·  {hint}", status=msg, hint=Msg("Akku-Einstellungen für dieses Modell fehlen")) \
                if state["battery_unset"] else msg
            state["status_shown"] = shown
            set_status(shown)

        def summary_with_hint():
            lines = summary_lines(state["res"], state["p"])
            if state["battery_unset"]:
                hint = tr(BATTERY_HINT, model=model_label(state["res"].meta.get("model", state["model"])))
                lines = [("bad", hint)] + lines
            return lines

        def show_battery_hint():
            """Shows or hides the battery hint next to the battery fields, in the status line and the summary."""
            if state["battery_unset"]:
                battery_hint.grid()
            else:
                battery_hint.grid_remove()
            if state.get("status_shown") is not None and state["status"] is state["status_shown"]:
                set_main_status(state["status_main"])          # still the status of the last analysis
            if state["res"] is not None:
                fill_text(txt, summary_with_hint())

        ui["battery_hint"] = show_battery_hint

        def show_results():
            """Fills all tabs with the analysis result in the current language."""
            res, p = state["res"], state["p"]
            df = res.df
            skip_tree.delete(*skip_tree.get_children())
            for nme, msg in res.skipped:
                skip_tree.insert("", "end", values=(nme, str(msg)))
            fill_text(txt, summary_with_hint())
            tree.delete(*tree.get_children())
            for _, r in df.iterrows():
                tree.insert("", "end", values=[fmt_cell(k, r[k]) for k in cols])
            state["figs"] = {}
            if not df.empty:
                for key, fn in [("akku", figure_akku), ("belastung", figure_belastung),
                                ("antrieb", figure_antrieb), ("funk", figure_funk)]:
                    fig = fn(res, p)
                    state["figs"][key] = fig
                    show_fig(tabs[key], fig, builder=lambda fn=fn: fn(state["res"], state["p"]), title=tab_titles[key])
                labels = [flight_label(r) for _, r in df.iterrows()]
                flight_box["values"] = labels
                flight_var.set(labels[-1])
                select_flight()

        def export_csv():
            res = state["res"]
            if res is None or res.df.empty:
                messagebox.showinfo(tr("Export"), tr("Bitte zuerst auswerten."))
                return
            f = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
            if f:
                export_table(res.df).to_csv(f, index=False, sep=";", decimal=",", encoding="utf-8-sig")

        def export_all():
            res = state["res"]
            if res is None or res.df.empty:
                messagebox.showinfo(tr("Export"), tr("Bitte zuerst auswerten."))
                return
            d = filedialog.askdirectory(title=tr("Zielordner für Bericht und Diagramme"))
            if not d:
                return
            with open(os.path.join(d, tr("zusammenfassung.txt")), "w", encoding="utf-8") as fh:
                for _, line in summary_lines(res, state["p"]):
                    fh.write(line + "\n")
            for name, fig in state["figs"].items():
                fig.savefig(os.path.join(d, f"{name}.png"), dpi=150)
            path = current_path()
            if path is not None:
                no = int(res.df.loc[res.df["pfad"] == path, "Flug"].iloc[0])
                with open(os.path.join(d, tr("flug{no}_details.txt", no=no)), "w", encoding="utf-8") as fh:
                    for _, line in flight_detail_lines(res, state["p"], path):
                        fh.write(line + "\n")
                for k, v_ in enumerate(FLIGHT_VIEWS):
                    figure_flight(res, state["p"], path, v_).savefig(
                        os.path.join(d, tr("flug{no}_{view}.png", no=no, view=k + 1)), dpi=130)
            export_table(res.df).to_csv(os.path.join(d, tr("fluege.csv")), index=False, sep=";", decimal=",",
                                        encoding="utf-8-sig")
            messagebox.showinfo(tr("Gespeichert"), tr("Bericht, Tabelle und Diagramme wurden in\n{folder}\ngespeichert.",
                                                      folder=d))

        def snapshot():
            """What the user is looking at - restored after a language switch."""
            snap = {"tab": nb.index("current"), "view": view_var.get(), "details": fs["details"],
                    "flight": flight_var.get().split("|")[0].strip() if flight_var.get() else None,
                    "xlim": fs["axes"][0].get_xlim() if fs["axes"] else None}
            return snap

        def restore(snap):
            view_var.set(snap["view"])
            if snap["flight"]:
                match = [v for v in flight_box["values"] if v.split("|")[0].strip() == snap["flight"]]
                if match:
                    flight_var.set(match[0])
            select_flight()
            if snap["xlim"] and fs["axes"]:
                set_xlim(*snap["xlim"])
            if not snap["details"]:
                toggle_details()
            nb.select(snap["tab"])

        ui["snapshot"] = snapshot
        show_battery_hint()
        if state["res"] is not None:
            show_results()
        if snap is not None:
            if state["res"] is not None:
                restore(snap)
            else:
                nb.select(snap["tab"])
        else:
            nb.select(tabs["settings"])
        # for tests
        root._akku = dict(fbox=flight_box, run=run, model_box=model_box, model_bar=selbar, use_model=use_model, folder_var=folder_var,
                          battery_hint=battery_hint, chem_box=chem_box, state=state, params=V, status=status, nb=nb, tabs=tabs,
                          flight_var=flight_var, view_var=view_var, select_flight=select_flight, redraw=redraw_flight,
                          set_xlim=set_xlim, goto_spike=goto_spike, spike_var=spike_var, lang_var=lang_var,
                          set_language=change_language, summary=txt, details=det_txt, table=tree,
                          fullscreen=fullscreen, open_fullscreen=open_fullscreen, open_chart=open_chart,
                          flight_builder=flight_builder, flight_canvas=flight_canvas, tab_canvas=tab_canvas,
                          tab_builder=lambda key: (lambda: dict(akku=figure_akku, belastung=figure_belastung,
                                                                antrieb=figure_antrieb, funk=figure_funk)[key](
                                                       state["res"], state["p"])))

    def on_close():
        store_settings()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    build()
    return root


def main():
    """Starts the user interface."""
    run_gui().mainloop()
