# -*- coding: utf-8 -*-
"""Single flight: time series in views of at most 5 charts each."""

import numpy as np

from ..config import SPIKE_CAUSES, SPIKE_COLOR, SPIKE_LABELS, STICK_LABELS, label
from ..i18n import N_, fmt_datetime, tr
from ..plots.common import _note, _style_mpl, hover_info, time_axis
from ..utils import _mmss, fmt_duration


# views of the single-flight tab: language-neutral code -> user-facing label
FLIGHT_VIEWS = ["battery", "reception", "rx_current", "attitude"]

VIEW_LABELS = {
    "battery": N_("Akku & Antrieb"),
    "reception": N_("Empfang"),
    "rx_current": N_("Empfängerstrom & Steuerung"),
    "attitude": N_("Fluglage"),
}


def cell_count(r):
    """Cell count of the flight (column Zellen of the analysis: setting or automatic), None if unknown."""
    try:
        c = float(r["Zellen"])
    except (KeyError, TypeError, ValueError):
        return None
    return int(c) if np.isfinite(c) and c >= 1 else None


def battery_voltage(u, cells):
    """Battery voltage for the single flight: (values, unit, per_cell) - per cell if the cell count is known."""
    if u is None:
        return None, "V", False
    if cells:
        return np.asarray(u, dtype=float) / cells, tr("V/Zelle"), True
    return np.asarray(u, dtype=float), "V", False


# stick channels of the attitude view: (key in series["sticks"], Ethos channel name)
STICK_CHANNELS = [("aileron", "QR"), ("elevator", "HR"), ("rudder", "SR")]


def _flight_panels(s, view, cells=None, chem=None):
    """List of charts: dict(title, unit, note, lines=[(label, y, color, kw)], twin=dict(unit, lines), extra).

    cells: cell count (battery voltage per cell, see battery_voltage); chem: entry of config.CHEM (limit lines).
    """
    rx = s.get("rx")
    P = []

    def add(title, unit, note, lines, twin=None, **kw):
        pn = dict(title=title, unit=unit, note=note, lines=[l for l in lines if l[1] is not None], **kw)
        if twin:
            twin = dict(twin, lines=[l for l in twin["lines"] if l[1] is not None])
            if twin["lines"] and not pn["lines"]:          # e.g. stick without angle: stick alone
                pn.update(unit=twin["unit"], lines=twin["lines"], sym=twin.get("sym", False))
            elif twin["lines"]:
                pn["twin"] = twin
        P.append(pn)

    alt = (tr("Höhe"), s["alt"], "tab:brown", {})
    sticks = s.get("sticks") or {}
    if view == "battery":
        u, uu, per_cell = battery_voltage(s["u"], cells)
        ocv = battery_voltage(s.get("ocv"), cells)[0]
        note = tr("Gestrichelt: geschätzte Spannung ohne Last. Abstand = Spannungsabfall durch den Innenwiderstand.")
        limits = []
        if per_cell:
            title = tr("Akkuspannung je Zelle")
            note += " " + tr("Mittlere Zellspannung = Gesamtspannung / {cells} Zellen.", cells=cells)
            if chem:
                limits = [(chem["load_min"], tr("Grenze unter Last {v:.2f} V/Zelle", v=chem["load_min"]), "tab:red", "--"),
                          (chem["rest_min"], tr("Mindest-Ruhespannung {v:.2f} V/Zelle", v=chem["rest_min"]),
                           "tab:orange", ":")]
        else:
            title = tr("Akkuspannung (gesamt)")
            note += " " + tr("Zellenzahl unbekannt: Gesamtspannung des Akkus.")
        add(title, uu, note, [(tr("Spannung"), u, "tab:blue", {}),
                               (tr("Ruhespannung (geschätzt)"), ocv, "grey", {"ls": "--"})], limits=limits)
        add(tr("Akkustrom"), "A", tr("Strom aus dem Flugakku."), [(tr("Strom"), s["i"], "tab:red", {})])
        add(tr("Drehzahl"), tr("1000 U/min"), tr("Drehzahl des Antriebs."),
            [(tr("Drehzahl"), s["rpm"] / 1000 if s["rpm"] is not None else None, "tab:purple", {})])
        add(tr("Höhe"), "m", tr("Relative Höhe über dem Startpunkt."), [alt])
    elif view == "reception":
        add(tr("Empfangsstärke (RSSI)"), "dB", tr("Ethos warnt üblicherweise unter 45."),
            [("RSSI", s.get("rssi"), "tab:blue", {})])
        add(tr("Telemetrie-Rahmen (VFR)"), "%", tr("Anteil korrekt empfangener Rahmen. Einbrüche = Empfangsstörung."),
            [("VFR", s.get("vfr"), "tab:green", {})])
        add(tr("Höhe"), "m", tr("Zum Abgleich: Einbrüche bei großer Höhe/Entfernung oder in bestimmten Fluglagen?"), [alt])
    elif view == "rx_current":
        add(tr("Empfängerstrom"), "A", tr("Dreiecke: Spitzen über der gestrichelten Schwelle, Farbe = Anlass."),
            [(tr("Empfängerstrom"), rx["rs"] if rx else s.get("rxi"), "tab:red", {})], spikes=True)
        add(tr("Knüppelwege"), "%", tr("Schnelle, große Ausschläge erzeugen Servolast. Senkrechte Linien: Schalter."),
            [(label(STICK_LABELS, k), v, c, {"lw": 1.1})
             for (k, v), c in zip(sticks.items(), ["tab:blue", "tab:orange", "tab:green"])],
            switches=True)
        add(tr("Gas"), "%", tr("Gasknüppel."), [(tr("Gas"), s["gas"], "tab:green", {})])
        add(tr("Empfängerspannung"), "V", tr("Bricht sie bei Stromspitzen ein, ist die Versorgung zu schwach."),
            [(tr("Empfängerspannung"), s.get("rxu"), "tab:orange", {})])
    else:
        # attitude with the stick that controls it: angle left axis [°], stick right axis [%], both centred on 0
        stick = lambda key, color: (tr("{stick} (Knüppel)", stick=label(STICK_LABELS, key)), sticks.get(key), color,
                                    {"lw": 1.0, "alpha": 0.9})
        add(tr("Rollwinkel und Querruder"), "°",
            tr("Links Rollwinkel [°], rechts Querruder-Knüppel [%] (Ethos-Kanalwert, ±100 % = Vollausschlag)."),
            [(tr("Roll"), s.get("roll"), "tab:blue", {})],
            twin=dict(unit="%", lines=[stick("aileron", "tab:cyan")], sym=True), sym=True)
        add(tr("Nickwinkel und Höhenruder"), "°",
            tr("Links Nickwinkel [°], rechts Höhenruder-Knüppel [%] (Ethos-Kanalwert)."),
            [(tr("Nick"), s.get("pitch"), "tab:orange", {})],
            twin=dict(unit="%", lines=[stick("elevator", "tab:olive")], sym=True), sym=True)
        add(tr("Gas und Seitenruder"), "%", tr("Gas 0–100 %, Seitenruder-Knüppel ±100 %. Senkrechte Linien: Schalter."),
            [(tr("Gas"), s["gas"], "tab:green", {}), stick("rudder", "tab:red")], switches=True)
        add(tr("G-Last"), "g", tr("Beschleunigung, 1 g = Geradeausflug."), [(tr("G-Last"), s.get("g"), "tab:brown", {})])
        add(tr("Höhe"), "m", tr("Relative Höhe über dem Startpunkt."), [alt])
        missing = [ch for key, ch in STICK_CHANNELS if key not in sticks] + ([] if s["gas"] is not None else ["Gas"])
        shown = [pp for pp in P if pp["lines"]]
        if missing and shown:
            shown[0]["note"] += " " + tr("Nicht im Log oder nicht bewegt: {channels}.", channels=", ".join(missing))
    return [pp for pp in P if pp["lines"]]


def draw_flight(fig, res, p, path, view=FLIGHT_VIEWS[0]):
    """Draws the selected view (a code from FLIGHT_VIEWS) of a flight into fig. Returns the axes (for zoom/crosshair)."""
    _style_mpl()
    fig.clear()
    fig.set_layout_engine("constrained")
    df = res.df
    r = df[df["pfad"] == path].iloc[0]
    s = res.series[path]
    t = s["t"]
    from ..config import CHEM
    panels = _flight_panels(s, view, cells=cell_count(r), chem=CHEM.get(getattr(p, "chem", None)))
    ri = tr("Ri {ri:.2f} mΩ/Zelle", ri=r["Ri_Zelle_mOhm"]) if np.isfinite(r["Ri_Zelle_mOhm"]) else "Ri n/a"
    fig.suptitle(tr("Flug {no} – {date} – {dur} – {drawn:.0f} mAh – {ri}", no=int(r["Flug"]),
                    date=fmt_datetime(r["datum"]), dur=_mmss(r["dauer_s"]), drawn=r["entnommen_mAh"], ri=ri),
                 fontsize=11, fontweight="bold")
    fig._readout = []
    if not panels:
        fig.text(0.5, 0.5, tr("Für diese Ansicht sind keine Daten im Log."), ha="center", va="center", color="grey", fontsize=12)
        return []
    axes = fig.subplots(len(panels), 1, sharex=True, squeeze=False)[:, 0]
    rx = s.get("rx")
    for a, pn in zip(axes, panels):
        for name, y, color, kw in pn["lines"]:
            a.plot(t, y, color=color, label=name, gid="data", **kw)
            fig._readout.append((name, pn["unit"], y))
        for val, txt, color, ls in pn.get("limits", ()):
            a.axhline(val, color=color, ls=ls, lw=1, label=txt, gid="limit")
        a.set_ylabel(pn["unit"])
        a.set_title(pn["title"], loc="left")
        time_axis(a, "x")
        hover_info(a, y=lambda v, u=pn["unit"]: f"{v:.4g} {u}")
        _note(a, pn["note"])
        a._sym = pn.get("sym", False)
        tw = None
        if pn.get("twin"):
            tw = a.twinx()
            tw.grid(False)
            tw.spines["right"].set_visible(True)
            for name, y, color, kw in pn["twin"]["lines"]:
                tw.plot(t, y, color=color, label=name, gid="data", **kw)
                fig._readout.append((name, pn["twin"]["unit"], y))
            tw.set_ylabel(pn["twin"]["unit"])
            tw.set_ylim(-105, 105)
            tw._fixed_ylim = True                       # stick travel: always the full range
            hover_info(tw, x=lambda v: "t = " + fmt_duration(v), y=lambda v, u=pn["twin"]["unit"]: f"{v:.4g} {u}")
        if pn.get("spikes") and rx:
            a.axhline(rx["thr"], color="tab:red", ls="--", lw=0.9, label=tr("Spitzenschwelle {thr:.2f} A", thr=rx["thr"]))
            if s.get("rxi") is not None:
                a.plot(t, s["rxi"], color="tab:red", lw=0.6, alpha=0.25)
            for cause, color in SPIKE_CAUSES:
                pts = [sp for sp in rx["spikes"] if sp["anlass"] == cause]
                if pts:
                    a.plot([sp["t"] for sp in pts], [sp["peak"] for sp in pts], "v", ms=9, color=color,
                           label=tr("Spitze: {cause}", cause=label(SPIKE_LABELS, cause)), ls="none")
        if pn.get("switches"):
            groups = []                                   # merge switch events within 2 s
            for t_, name, _, _ in s.get("switches") or []:
                if groups and t_ - groups[-1][0] < 2.0:
                    groups[-1][1].add(name)
                else:
                    groups.append([t_, {name}])
            for t_, names in groups:
                a.axvline(t_, color="tab:green", lw=0.9, ls=":", alpha=0.9)
                a.text(t_, 0.99, " " + "/".join(sorted(names)), transform=a.get_xaxis_transform(), fontsize=7,
                       color="#1b6e1b", rotation=90, va="top", ha="left", clip_on=True, in_layout=False)
        if tw is None:
            a.legend(loc="upper left", bbox_to_anchor=(1.005, 1.0), frameon=False, fontsize=8)
        else:                                           # one legend for both axes, right of the stick axis
            h1, l1 = a.get_legend_handles_labels()
            h2, l2 = tw.get_legend_handles_labels()
            tw.legend(h1 + h2, l1 + l2, loc="upper left", bbox_to_anchor=(1.07, 1.0), frameon=False, fontsize=8)
    if view in ("rx_current", "attitude") and rx:
        for sp in rx["spikes"]:
            for a in axes:
                a.axvline(sp["t"], color=SPIKE_COLOR[sp["anlass"]], lw=0.8, alpha=0.35)
    if view == "battery" and np.isfinite(r["Timer_s"]) and r["Timer_s"] <= t[-1]:
        for a in axes:
            a.axvline(r["Timer_s"], color="tab:red", ls=":", lw=1.2)
        axes[0].text(r["Timer_s"], 0.02, tr(" Timer-Empfehlung"), transform=axes[0].get_xaxis_transform(),
                     color="tab:red", fontsize=8, va="bottom", clip_on=True, in_layout=False)
    # additional values for the crosshair readout
    extra = [(tr("entnommen"), "mAh", s["q"]), (tr("Leistung"), "kW", s["p"] / 1000)]
    if view != "rx_current" and s["gas"] is not None:
        extra.append((tr("Gas"), "%", s["gas"]))
    fig._readout += extra
    fig._t = t
    axes[-1].set_xlabel(tr("Zeit seit Motorstart [min:s]"))
    axes[-1].set_xlim(t[0], t[-1])
    fit_y(list(axes))
    return list(axes)


def fit_y(axes):
    """Fits the y axes of single-flight charts to the visible time window.

    Only data lines and limit lines count (not helper lines such as thresholds of spikes or markers). All axes of
    the figure are fitted, twin axes included; axes marked _fixed_ylim keep their range (stick travel), axes
    marked _sym get a range symmetric around 0 (angle next to a stick axis, so both zero lines meet).
    """
    if not axes:
        return
    lo, hi = axes[0].get_xlim()
    for a in axes[0].figure.axes:
        if getattr(a, "_fixed_ylim", False):
            continue
        ys = []
        for ln in a.get_lines():
            gid = ln.get_gid()
            if gid == "limit":
                v = float(np.asarray(ln.get_ydata(), dtype=float)[0])
                ys.append((v, v))
                continue
            if gid != "data":
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
            if getattr(a, "_sym", False):
                y1 = max(abs(y0), abs(y1))
                y0 = -y1
            pad = (y1 - y0) * 0.08 or 0.5
            a.set_ylim(y0 - pad, y1 + pad)


def figure_flight(res, p, path, view=FLIGHT_VIEWS[0]):
    """Single flight as a standalone figure (for export)."""
    from matplotlib.figure import Figure
    fig = Figure(figsize=(12, 8.5), dpi=100)
    draw_flight(fig, res, p, path, view)
    return fig
