# -*- coding: utf-8 -*-
"""Helpers shared by several pages: table columns and cell texts, sortable tables, text boxes, CSV export."""

import numpy as np

from ..analysis.evaluate import FLAG_LABELS
from ..analysis.quality import QUALITY_LABELS
from ..config import VOLTAGE_SOURCE_LABELS, label, model_label
from ..i18n import N_, fmt_datetime
from ..utils import fmt_duration

# columns of the table tab: (key in the flight table, heading, width in pixels)
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

# durations [s] shown as min:s (table) and exported additionally as min:s text columns (CSV)
DURATION_COLS = ["dauer_s", "Timer_s", "Zeit_80_s", "t_steig_s", "t_reise_s", "t_sink_s"]


def flag_text(codes):
    """Column "Auffaellig" (comma-separated flag codes) as text in the current language."""
    return ", ".join(label(FLAG_LABELS, c) for c in str(codes).split(", ") if c)


def error_text(codes):
    """Column "Datenfehler" (comma-separated data-error codes) as text in the current language."""
    return ", ".join(label(QUALITY_LABELS, c) for c in str(codes).split(", ") if c)


def fmt_cell(key, v):
    """Text of one cell of the table tab."""
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


def sort_key(v):
    """Sort key for a table cell: missing values (None, NaN) always last, otherwise the raw value."""
    missing = v is None or (isinstance(v, (float, np.floating)) and not np.isfinite(v))
    return (missing, 0 if missing else v)


def sortable_tree(tree, cols):
    """Makes a ttk.Treeview sortable: a click on a column heading sorts by it, a second click reverses.

    cols: [(key, heading, width)]. Rows are given as (raw values, shown texts) through the returned
    set_rows(rows), optionally followed by the tags of the row; sorting uses the raw values (numbers, dates),
    so "10" sorts after "9". The heading of the sorted column shows ▲/▼.
    Returns {"set_rows", "sort", "state"} (also used by tests).
    """
    st = {"rows": [], "col": None, "desc": False}
    heads = {key: head for key, head, _w in cols}
    keys = [key for key, _h, _w in cols]

    def fill():
        tree.delete(*tree.get_children())
        rows = st["rows"]
        if st["col"] is not None:
            i = keys.index(st["col"])
            ok = [r for r in rows if not sort_key(r[0][i])[0]]
            missing = [r for r in rows if sort_key(r[0][i])[0]]
            rows = sorted(ok, key=lambda r: r[0][i], reverse=st["desc"]) + missing
        for _raw, shown, *tags in rows:
            tree.insert("", "end", values=shown, tags=tags[0] if tags else ())
        for key in keys:
            mark = (" ▼" if st["desc"] else " ▲") if key == st["col"] else ""
            tree.heading(key, text=heads[key] + mark, command=lambda k=key: sort(k))

    def sort(key):
        st["desc"] = (not st["desc"]) if key == st["col"] else False
        st["col"] = key
        fill()

    def set_rows(rows):
        st["rows"] = list(rows)
        fill()

    fill()
    return {"set_rows": set_rows, "sort": sort, "state": st}


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


def make_text(parent, family, height=None):
    """Read-only rich text box with the tags used by reports: h (heading), ok, warn, bad, info."""
    import tkinter as tk
    kw = dict(wrap="word", font=(family, 10), padx=12, pady=8, relief="flat", background="#ffffff",
              borderwidth=0, highlightthickness=0)
    if height:
        kw["height"] = height
    text = tk.Text(parent, **kw)
    text.tag_configure("h", font=(family, 11, "bold"), spacing1=10, spacing3=3, foreground="#1f3b73")
    text.tag_configure("ok", foreground="#1b7f3b")
    text.tag_configure("warn", foreground="#b36b00")
    text.tag_configure("bad", foreground="#b00020")
    text.tag_configure("info")
    return text


def fill_text(text, lines):
    """Replaces the content of a text box by report lines [(tag, line)]."""
    text.configure(state="normal")
    text.delete("1.0", "end")
    for tag, line in lines:
        text.insert("end", line + "\n", tag)
    text.configure(state="disabled")


def scrollable_frame(parent, background):
    """A frame inside parent that scrolls vertically when its content is taller than the window (mouse wheel
    and scrollbar). The frame is as wide as the visible area and at least as tall, so rows with a weight still
    fill the window when there is room. Returns the inner frame; pack or grid nothing else into parent."""
    import tkinter as tk
    from tkinter import ttk

    canvas = tk.Canvas(parent, background=background, highlightthickness=0, borderwidth=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = ttk.Frame(canvas)
    window = canvas.create_window(0, 0, window=inner, anchor="nw")

    def fit(_event=None):
        width, height = canvas.winfo_width(), canvas.winfo_height()
        canvas.itemconfigure(window, width=width, height=max(inner.winfo_reqheight(), height))
        canvas.configure(scrollregion=(0, 0, width, max(inner.winfo_reqheight(), height)))

    def on_wheel(event):
        if inner.winfo_reqheight() > canvas.winfo_height():
            step = -1 if (getattr(event, "delta", 0) > 0 or getattr(event, "num", 0) == 4) else 1
            canvas.yview_scroll(step * 3, "units")

    def bind_wheel(_event):
        # only while the mouse is over the page, so the wheel still zooms charts on other pages
        canvas.bind_all("<MouseWheel>", on_wheel)
        canvas.bind_all("<Button-4>", on_wheel)
        canvas.bind_all("<Button-5>", on_wheel)

    def unbind_wheel(_event):
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            canvas.unbind_all(sequence)

    canvas.bind("<Configure>", fit)
    inner.bind("<Configure>", fit)
    canvas.bind("<Enter>", bind_wheel)
    canvas.bind("<Leave>", unbind_wheel)
    return inner
