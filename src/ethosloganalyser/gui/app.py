# -*- coding: utf-8 -*-
"""Main window of the app (Tkinter).

The window content is built by ``build()``. When the user switches the language, the content is destroyed
and built again in the new language; the analysis result, the settings, the selected flight, view, zoom
and tab are kept, so the logs do not have to be analysed again.
"""

import os
import numpy as np

from ..analysis.evaluate import FLAG_LABELS
from ..analysis.fleet import analyse_folder
from ..config import CHEM, SPIKE_LABELS, VOLTAGE_SOURCE_LABELS, Params, label, load_settings, save_settings
from ..gui.style import BG, _setup_style
from ..i18n import LANGUAGES, Msg, N_, detect_language, fmt_datetime, get_language, set_language, tr
from ..plots.flight import FLIGHT_VIEWS, VIEW_LABELS, draw_flight, figure_flight
from ..plots.overview import figure_akku, figure_antrieb, figure_belastung, figure_funk
from ..report.text import flight_detail_lines, summary_lines
from ..utils import _mmss


TABLE_COLS = [
    ("Flug", N_("Flug"), 45), ("datum", N_("Datum"), 120), ("dauer_s", N_("Dauer s"), 60),
    ("entnommen_mAh", N_("entnommen mAh"), 90), ("ESC_mAh", N_("ESC mAh"), 65), ("Sensor_Abw_pct", N_("Abw. %"), 55),
    ("energie_Wh", N_("Energie Wh"), 75), ("I_mittel_A", N_("Ø A"), 50), ("I_max_A", N_("max A"), 55),
    ("P_max_W", N_("P max W"), 65), ("C_peak", N_("C Spitze"), 60), ("SoC_start_pct", N_("SoC Start %"), 75),
    ("SoC_ende_pct", N_("SoC Ende %"), 75), ("SoC_ende_U_pct", N_("SoC Ende (U) %"), 90),
    ("SoC_Abw_pct", N_("SoC Abw. Pkt"), 80), ("Kap_gesch_mAh", N_("Kapazität mAh"), 90),
    ("Ri_Zelle_mOhm", N_("Ri/Zelle mΩ"), 80), ("Ri_Anf_Zelle_mOhm", N_("Ri Anfang"), 70),
    ("Ri_End_Zelle_mOhm", N_("Ri Ende"), 65), ("U_ref_Zelle_V", N_("U Ref V/Z"), 70),
    ("U_min_Zelle_V", N_("U min V/Z"), 70), ("U_ende_Zelle_V", N_("U Ende V/Z"), 75),
    ("U_ende_Quelle", N_("U Ende Quelle"), 85), ("Reserve_Zelle_V", N_("Reserve V/Z"), 80),
    ("Timer_s", N_("Timer s"), 55), ("rpm_p90", N_("rpm P90"), 70), ("P_ref_W", N_("P Ref W"), 65),
    ("Hoehe_max_m", N_("Höhe max"), 65), ("Wh_je_100m", N_("Wh/100m"), 65), ("g_max", N_("g max"), 50),
    ("RSSI_min", N_("RSSI min"), 65), ("VFR_min", N_("VFR min"), 60), ("RxBatt_min_V", N_("Rx V min"), 65),
    ("RxStrom_mittel_A", N_("Rx A Ø"), 55), ("RxStrom_max_A", N_("Rx A max"), 65),
    ("RxSpitzen_n", N_("Rx Spitzen"), 70), ("RxSp_Schalter", N_("Sp. Schalter"), 80),
    ("RxSp_ohne", N_("Sp. o. Anlass"), 85), ("Rx_r_Knueppel", N_("r Rx/Knüppel"), 85),
    ("fit_R2", N_("R² Fit"), 50), ("versatz_s", N_("Versatz s"), 60), ("Auffaellig", N_("Auffälligkeiten"), 260),
]


def flag_text(codes):
    """Column "Auffaellig" (comma-separated flag codes) as text in the current language."""
    return ", ".join(label(FLAG_LABELS, c) for c in str(codes).split(", ") if c)


def fmt_cell(key, v):
    if key == "datum":
        return fmt_datetime(v)
    if key == "U_ende_Quelle":
        return label(VOLTAGE_SOURCE_LABELS, v)
    if key == "Auffaellig":
        return flag_text(v)
    if isinstance(v, (float, np.floating)):
        return "–" if not np.isfinite(v) else f"{v:.5g}"
    return "" if v is None else str(v)


def export_table(df):
    """Result table for the CSV export: internal columns removed, text columns in the current language."""
    out = df.drop(columns=["pfad", "P_a", "P_n", "k_V_je_Ah"], errors="ignore").copy()
    if "U_ende_Quelle" in out:
        out["U_ende_Quelle"] = [label(VOLTAGE_SOURCE_LABELS, v) for v in out["U_ende_Quelle"]]
    if "Auffaellig" in out:
        out["Auffaellig"] = [flag_text(v) for v in out["Auffaellig"]]
    return out


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
    }
    ui = {"frame": None}

    def store_settings():
        d = {k: v.get() for k, v in V.items()}
        d["folder"] = folder_var.get()
        d["language"] = get_language()
        save_settings(d)

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
        root.title(tr("EthosLogAnalyser – Flug- und Akku-Analyse (FrSky Ethos Logs)"))
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
        tabs = {}
        for key, title in [("settings", tr("Daten & Einstellungen")), ("summary", tr("Zusammenfassung")),
                           ("akku", tr("Akku")), ("belastung", tr("Belastung & Flugprofil")), ("antrieb", tr("Antrieb")),
                           ("funk", tr("Funk & Bordnetz")), ("flight", tr("Einzelflug")), ("table", tr("Tabelle"))]:
            fr = ttk.Frame(nb)
            nb.add(fr, text=title)
            tabs[key] = fr

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

        def field(parent, row, text, key, hint="", combo=None):
            ttk.Label(parent, text=text).grid(row=row, column=0, sticky="w", pady=3)
            if combo:
                w = ttk.Combobox(parent, textvariable=V[key], values=combo, width=12, state="readonly")
            else:
                w = ttk.Entry(parent, textvariable=V[key], width=14)
            w.grid(row=row, column=1, sticky="w", padx=8, pady=3)
            if hint:
                ttk.Label(parent, text=hint, foreground="#666").grid(row=row, column=2, sticky="w")

        lf = ttk.LabelFrame(st_tab, text=tr("Akku"), padding=10)
        lf.grid(row=1, column=0, sticky="nwe", padx=(0, 6))
        field(lf, 0, tr("Zellchemie"), "chem", tr("LiPo, LiHV oder Li-Ion"), list(CHEM.keys()))
        field(lf, 1, tr("Zellenzahl"), "cells", tr("0 = automatisch aus der Startspannung"))
        field(lf, 2, tr("Nennkapazität [mAh]"), "nominal_mah", tr("0 = unbekannt (wird geschätzt)"))

        lf = ttk.LabelFrame(st_tab, text=tr("Auswertung"), padding=10)
        lf.grid(row=1, column=1, sticky="nwe", padx=(6, 0))
        field(lf, 0, tr("Min. Flugdauer [s]"), "min_flight_s", tr("kürzere Logs werden übersprungen"))
        field(lf, 1, tr("Motor aktiv ab [A]"), "active_current_a", tr("Strom, ab dem der Flug zählt"))
        field(lf, 2, tr("Reserve bei Landung [%]"), "reserve_pct", tr("für die Timer-Empfehlung"))
        field(lf, 3, tr("Spalte Spannung (optional)"), "col_voltage", tr("Teil des Spaltennamens"))
        field(lf, 4, tr("Spalte Strom (optional)"), "col_current", "")

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
                                        "Ziehen mit linker Maustaste: verschieben  ·  Doppelklick: ganzer Flug"))
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
        flight_canvas = FigureCanvasTkAgg(flight_fig, master=plot_frame)
        flight_canvas.get_tk_widget().pack(fill="both", expand=True)
        fs = {"axes": [], "cross": [], "drag": None, "details": True}

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
                num = lambda k: float(V[k].get().replace(",", "."))
                return Params(cells=int(num("cells")), chem=V["chem"].get(), nominal_mah=num("nominal_mah"),
                              min_flight_s=num("min_flight_s"), active_current_a=num("active_current_a"),
                              reserve_pct=num("reserve_pct"), col_voltage=V["col_voltage"].get().strip(),
                              col_current=V["col_current"].get().strip())
            except ValueError:
                messagebox.showerror(tr("Eingabefehler"), tr("Bitte gültige Zahlen in den Einstellungen eintragen."))
                return None

        def show_fig(frame, fig):
            for w in frame.winfo_children():
                w.destroy()
            canvas = FigureCanvasTkAgg(fig, master=frame)
            toolbar = NavigationToolbar2Tk(canvas, frame)
            toolbar.update()
            canvas.draw()
            canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

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
            fs["cross"] = [a.axvline(np.nan, color="#333", lw=0.8, alpha=0.7) for a in fs["axes"]]
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
                items = [f"{sp['t']:.0f} s – {sp['peak']:.2f} A – {label(SPIKE_LABELS, sp['anlass'])}"
                         + (f" ({sp['schalter']})" if sp["schalter"] else "") for sp in rx["spikes"]]
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
            lo, hi = fs["axes"][0].get_xlim()
            for a in fs["axes"]:
                ys = []
                for ln in a.get_lines():
                    if ln.get_gid() != "data":          # ignore helper lines (thresholds, markers)
                        continue
                    x = np.asarray(ln.get_xdata(), dtype=float)
                    if len(x) < 2:
                        continue
                    y = np.asarray(ln.get_ydata(), dtype=float)
                    m = (x >= lo) & (x <= hi) & np.isfinite(y)
                    if m.any():
                        ys.append((y[m].min(), y[m].max()))
                if ys:
                    y0, y1 = min(v[0] for v in ys), max(v[1] for v in ys)
                    pad = (y1 - y0) * 0.08 or 0.5
                    a.set_ylim(y0 - pad, y1 + pad)

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
            sel = spike_var.get()
            if not sel or not sel[0].isdigit():
                return
            t_ = float(sel.split(" s")[0])
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
                zoom_to(None)
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
            if ev.inaxes is None or ev.xdata is None or not fs["axes"]:
                return
            t = getattr(flight_fig, "_t", None)
            if t is None:
                return
            k = int(np.clip(np.searchsorted(t, ev.xdata), 0, len(t) - 1))
            for ln in fs["cross"]:
                ln.set_xdata([t[k], t[k]])
            parts = [f"t = {t[k]:.1f} s"]
            for name, unit, y in flight_fig._readout:
                if y is not None and k < len(y) and np.isfinite(y[k]):
                    parts.append(f"{name} {y[k]:.4g} {unit}")
            readout.set("   ·   ".join(parts))
            flight_canvas.draw_idle()

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
                res = analyse_folder(folder, p, cb)
            except Exception as e:                       # unexpected error: report it understandably
                messagebox.showerror(tr("Fehler bei der Auswertung"), f"{type(e).__name__}: {e}")
                set_status(Msg("Fehler bei der Auswertung."))
                return
            finally:
                run_btn.state(["!disabled"])
            state["res"], state["p"], state["folder"] = res, p, folder
            cells = res.meta.get("cells", p.cells)
            cap = f", {p.nominal_mah:.0f} mAh" if p.nominal_mah > 0 else Msg(", Kapazität unbekannt")
            set_status(Msg("{folder}  ·  {n} Flüge ausgewertet, {skipped} von {total} Dateien übersprungen  ·  "
                           "Akku {cells}S {chem}{cap}", folder=os.path.basename(os.path.normpath(folder)),
                           n=len(res.df), skipped=len(res.skipped), total=res.total, cells=cells, chem=p.chem, cap=cap))
            show_results()
            nb.select(tabs["summary"])

        def show_results():
            """Fills all tabs with the analysis result in the current language."""
            res, p = state["res"], state["p"]
            df = res.df
            skip_tree.delete(*skip_tree.get_children())
            for nme, msg in res.skipped:
                skip_tree.insert("", "end", values=(nme, str(msg)))
            fill_text(txt, summary_lines(res, p))
            tree.delete(*tree.get_children())
            for _, r in df.iterrows():
                tree.insert("", "end", values=[fmt_cell(k, r[k]) for k in cols])
            state["figs"] = {}
            if not df.empty:
                for key, fn in [("akku", figure_akku), ("belastung", figure_belastung),
                                ("antrieb", figure_antrieb), ("funk", figure_funk)]:
                    fig = fn(res, p)
                    state["figs"][key] = fig
                    show_fig(tabs[key], fig)
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
        root._akku = dict(fbox=flight_box, run=run, folder_var=folder_var, params=V, status=status, nb=nb, tabs=tabs,
                          flight_var=flight_var, view_var=view_var, select_flight=select_flight, redraw=redraw_flight,
                          set_xlim=set_xlim, goto_spike=goto_spike, spike_var=spike_var, lang_var=lang_var,
                          set_language=change_language, summary=txt, details=det_txt, table=tree)

    def on_close():
        store_settings()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    build()
    return root


def main():
    """Starts the user interface."""
    run_gui().mainloop()
