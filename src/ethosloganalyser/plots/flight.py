# -*- coding: utf-8 -*-
"""Single flight: time series in views of at most 4 charts each."""

import numpy as np

from ..config import SPIKE_CAUSES, SPIKE_COLOR, SPIKE_LABELS, STICK_LABELS, label
from ..i18n import N_, fmt_datetime, tr
from ..plots.common import _note, _style_mpl
from ..utils import _mmss


# views of the single-flight tab: language-neutral code -> user-facing label
FLIGHT_VIEWS = ["battery", "reception", "rx_current", "attitude"]

VIEW_LABELS = {
    "battery": N_("Akku & Antrieb"),
    "reception": N_("Empfang"),
    "rx_current": N_("Empfängerstrom & Steuerung"),
    "attitude": N_("Fluglage"),
}


def _flight_panels(s, view):
    """List of charts: dict(title, unit, note, lines=[(label, y, color, kw)], extra)."""
    rx = s.get("rx")
    P = []
    add = lambda title, unit, note, lines, **kw: P.append(dict(title=title, unit=unit, note=note,
                                                               lines=[l for l in lines if l[1] is not None], **kw))
    alt = (tr("Höhe"), s["alt"], "tab:brown", {})
    if view == "battery":
        add(tr("Akkuspannung"), "V",
            tr("Gestrichelt: geschätzte Spannung ohne Last. Abstand = Spannungsabfall durch den Innenwiderstand."),
            [(tr("Spannung"), s["u"], "tab:blue", {}), (tr("Ruhespannung (geschätzt)"), s["ocv"], "grey", {"ls": "--"})])
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
        sticks = s.get("sticks") or {}
        add(tr("Knüppelwege"), "%", tr("Schnelle, große Ausschläge erzeugen Servolast. Senkrechte Linien: Schalter."),
            [(label(STICK_LABELS, k), v, c, {"lw": 1.1})
             for (k, v), c in zip(sticks.items(), ["tab:blue", "tab:orange", "tab:green"])],
            switches=True)
        add(tr("Gas"), "%", tr("Gasknüppel."), [(tr("Gas"), s["gas"], "tab:green", {})])
        add(tr("Empfängerspannung"), "V", tr("Bricht sie bei Stromspitzen ein, ist die Versorgung zu schwach."),
            [(tr("Empfängerspannung"), s.get("rxu"), "tab:orange", {})])
    else:
        add(tr("Fluglage"), "°", tr("Roll- und Nickwinkel."),
            [(tr("Roll"), s.get("roll"), "tab:blue", {}), (tr("Nick"), s.get("pitch"), "tab:orange", {})])
        add(tr("Drehrate"), "°/s", tr("Wie schnell sich die Lage ändert (aus Roll und Nick)."),
            [(tr("Drehrate"), s.get("rate"), "tab:purple", {})])
        add(tr("G-Last"), "g", tr("Beschleunigung, 1 g = Geradeausflug."), [(tr("G-Last"), s.get("g"), "tab:brown", {})])
        add(tr("Höhe"), "m", tr("Relative Höhe über dem Startpunkt."), [alt])
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
    panels = _flight_panels(s, view)
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
        a.set_ylabel(pn["unit"])
        a.set_title(pn["title"], loc="left")
        _note(a, pn["note"])
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
        a.legend(loc="upper left", bbox_to_anchor=(1.005, 1.0), frameon=False, fontsize=8)
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
    axes[-1].set_xlabel(tr("Zeit seit Motorstart [s]"))
    axes[-1].set_xlim(t[0], t[-1])
    return list(axes)


def figure_flight(res, p, path, view=FLIGHT_VIEWS[0]):
    """Single flight as a standalone figure (for export)."""
    from matplotlib.figure import Figure
    fig = Figure(figsize=(12, 8.5), dpi=100)
    draw_flight(fig, res, p, path, view)
    return fig
