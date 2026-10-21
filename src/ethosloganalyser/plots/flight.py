# -*- coding: utf-8 -*-
"""Single flight: time series in views of at most 4 charts each."""

import numpy as np

from ..config import SPIKE_CAUSES, SPIKE_COLOR
from ..plots.common import _note, _style_mpl
from ..utils import _mmss


FLIGHT_VIEWS = ["Akku & Antrieb", "Empfang", "Empfängerstrom & Steuerung", "Fluglage"]


def _flight_panels(s, view):
    """List of charts: dict(title, unit, note, lines=[(label, y, color, kw)], extra)."""
    rx = s.get("rx")
    P = []
    add = lambda title, unit, note, lines, **kw: P.append(dict(title=title, unit=unit, note=note,
                                                               lines=[l for l in lines if l[1] is not None], **kw))
    if view == FLIGHT_VIEWS[0]:
        add("Akkuspannung", "V", "Gestrichelt: geschätzte Spannung ohne Last. Abstand = Spannungsabfall durch den Innenwiderstand.",
            [("Spannung", s["u"], "tab:blue", {}), ("Ruhespannung (geschätzt)", s["ocv"], "grey", {"ls": "--"})])
        add("Akkustrom", "A", "Strom aus dem Flugakku.", [("Strom", s["i"], "tab:red", {})])
        add("Drehzahl", "1000 U/min", "Drehzahl des Antriebs.",
            [("Drehzahl", s["rpm"] / 1000 if s["rpm"] is not None else None, "tab:purple", {})])
        add("Höhe", "m", "Relative Höhe über dem Startpunkt.", [("Höhe", s["alt"], "tab:brown", {})])
    elif view == FLIGHT_VIEWS[1]:
        add("Empfangsstärke (RSSI)", "dB", "Ethos warnt üblicherweise unter 45.", [("RSSI", s.get("rssi"), "tab:blue", {})])
        add("Telemetrie-Rahmen (VFR)", "%", "Anteil korrekt empfangener Rahmen. Einbrüche = Empfangsstörung.",
            [("VFR", s.get("vfr"), "tab:green", {})])
        add("Höhe", "m", "Zum Abgleich: Einbrüche bei großer Höhe/Entfernung oder in bestimmten Fluglagen?",
            [("Höhe", s["alt"], "tab:brown", {})])
    elif view == FLIGHT_VIEWS[2]:
        add("Empfängerstrom", "A", "Dreiecke: Spitzen über der gestrichelten Schwelle, Farbe = Anlass.",
            [("Empfängerstrom", rx["rs"] if rx else s.get("rxi"), "tab:red", {})], spikes=True)
        sticks = s.get("sticks") or {}
        add("Knüppelwege", "%", "Schnelle, große Ausschläge erzeugen Servolast. Senkrechte Linien: Schalter.",
            [(k, v, c, {"lw": 1.1}) for (k, v), c in zip(sticks.items(), ["tab:blue", "tab:orange", "tab:green"])],
            switches=True)
        add("Gas", "%", "Gasknüppel.", [("Gas", s["gas"], "tab:green", {})])
        add("Empfängerspannung", "V", "Bricht sie bei Stromspitzen ein, ist die Versorgung zu schwach.",
            [("Empfängerspannung", s.get("rxu"), "tab:orange", {})])
    else:
        add("Fluglage", "°", "Roll- und Nickwinkel.",
            [("Roll", s.get("roll"), "tab:blue", {}), ("Nick", s.get("pitch"), "tab:orange", {})])
        add("Drehrate", "°/s", "Wie schnell sich die Lage ändert (aus Roll und Nick).",
            [("Drehrate", s.get("rate"), "tab:purple", {})])
        add("G-Last", "g", "Beschleunigung, 1 g = Geradeausflug.", [("G-Last", s.get("g"), "tab:brown", {})])
        add("Höhe", "m", "Relative Höhe über dem Startpunkt.", [("Höhe", s["alt"], "tab:brown", {})])
    return [pp for pp in P if pp["lines"]]


def draw_flight(fig, res, p, path, view=FLIGHT_VIEWS[0]):
    """Draws the selected view of a flight into fig. Returns the axes (for zoom/crosshair)."""
    _style_mpl()
    fig.clear()
    fig.set_layout_engine("constrained")
    df = res.df
    r = df[df["pfad"] == path].iloc[0]
    s = res.series[path]
    t = s["t"]
    panels = _flight_panels(s, view)
    ri = f"Ri {r['Ri_Zelle_mOhm']:.2f} mΩ/Zelle" if np.isfinite(r["Ri_Zelle_mOhm"]) else "Ri n/a"
    fig.suptitle(f"Flug {int(r['Flug'])} – {r['datum']:%d.%m.%Y %H:%M} – {_mmss(r['dauer_s'])} – "
                 f"{r['entnommen_mAh']:.0f} mAh – {ri}", fontsize=11, fontweight="bold")
    fig._readout = []
    if not panels:
        fig.text(0.5, 0.5, "Für diese Ansicht sind keine Daten im Log.", ha="center", va="center", color="grey", fontsize=12)
        return []
    axes = fig.subplots(len(panels), 1, sharex=True, squeeze=False)[:, 0]
    rx = s.get("rx")
    for a, pn in zip(axes, panels):
        for label, y, color, kw in pn["lines"]:
            a.plot(t, y, color=color, label=label, gid="data", **kw)
            fig._readout.append((label, pn["unit"], y))
        a.set_ylabel(pn["unit"])
        a.set_title(pn["title"], loc="left")
        _note(a, pn["note"])
        if pn.get("spikes") and rx:
            a.axhline(rx["thr"], color="tab:red", ls="--", lw=0.9, label=f"Spitzenschwelle {rx['thr']:.2f} A")
            if s.get("rxi") is not None:
                a.plot(t, s["rxi"], color="tab:red", lw=0.6, alpha=0.25)
            for cause, color in SPIKE_CAUSES:
                pts = [sp for sp in rx["spikes"] if sp["anlass"] == cause]
                if pts:
                    a.plot([sp["t"] for sp in pts], [sp["peak"] for sp in pts], "v", ms=9, color=color,
                           label=f"Spitze: {cause}", ls="none")
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
    if view in (FLIGHT_VIEWS[2], FLIGHT_VIEWS[3]) and rx:
        for sp in rx["spikes"]:
            for a in axes:
                a.axvline(sp["t"], color=SPIKE_COLOR[sp["anlass"]], lw=0.8, alpha=0.35)
    if view == FLIGHT_VIEWS[0] and np.isfinite(r["Timer_s"]) and r["Timer_s"] <= t[-1]:
        for a in axes:
            a.axvline(r["Timer_s"], color="tab:red", ls=":", lw=1.2)
        axes[0].text(r["Timer_s"], 0.02, " Timer-Empfehlung", transform=axes[0].get_xaxis_transform(),
                     color="tab:red", fontsize=8, va="bottom", clip_on=True, in_layout=False)
    # additional values for the crosshair readout
    extra = [("entnommen", "mAh", s["q"]), ("Leistung", "kW", s["p"] / 1000)]
    if view != FLIGHT_VIEWS[2] and s["gas"] is not None:
        extra.append(("Gas", "%", s["gas"]))
    fig._readout += extra
    fig._t = t
    axes[-1].set_xlabel("Zeit seit Motorstart [s]")
    axes[-1].set_xlim(t[0], t[-1])
    return list(axes)


def figure_flight(res, p, path, view=FLIGHT_VIEWS[0]):
    """Single flight as a standalone figure (for export)."""
    from matplotlib.figure import Figure
    fig = Figure(figsize=(12, 8.5), dpi=100)
    draw_flight(fig, res, p, path, view)
    return fig
