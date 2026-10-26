# -*- coding: utf-8 -*-
"""Overview charts across all flights (tabs battery, load, drive, radio)."""

import numpy as np

from ..config import CHEM, SPIKE_CAUSES, SPIKE_COLS, SPIKE_LABELS, label
from ..i18n import tr
from ..plots.common import (_bottom_labels_only, _empty_fig, _new_fig, _note, _plot_trend, flag_note, flight_hover,
                            time_axis, trend_note)


def figure_akku(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig(tr("Keine Daten"))
    ch = CHEM[p.chem]
    fl = meta["flags"]
    fig, ax = _new_fig(3, 2, size=(11, 9))
    h = []
    cm = meta.get("ageing", {}).get("capacity", {})
    if p.nominal_mah > 0:
        h.append((p.nominal_mah, tr("Nennkapazität"), "grey"))
        h.append((0.8 * p.nominal_mah, tr("80 % der Nennkapazität"), "tab:red"))
    elif cm.get("status") == "ok":
        h.append((0.8 * cm["start"], tr("80 % der Anfangskapazität"), "tab:red"))
    cap_col = "Kap_norm_mAh" if "Kap_norm_mAh" in df.columns else "Kap_gesch_mAh"
    note = tr("Aus entnommener Ladung und Spannungsabfall. Fallender Trend = Alterung.")
    if cm.get("status") == "ok" and cm["depth_coef"]:
        note += " " + tr("Auf {depth:.0f} % Entladetiefe bezogen.", depth=cm["depth_ref"])
    if cm.get("status") == "ok" and cm.get("uncertain"):
        note += " " + tr("Trend unsicher, siehe Bericht.")
    ag = meta.get("ageing", {})
    _plot_trend(ax[0][0], df, cap_col, "tab:green", tr("Geschätzte Gesamtkapazität [mAh]"), fl, "capacity", h,
                note=note + flag_note(), model=cm or None)
    a = ax[0][1]
    ri_title = tr("Innenwiderstand je Zelle [mΩ]")
    _plot_trend(a, df, "Ri_Zelle_mOhm", "tab:red", ri_title, fl, "ri", label=tr("Ø Flug"),
                note=tr("Steigender Trend = Alterung; +50 % gilt als Lebensende.") + trend_note(), model=ag.get("ri"))
    _plot_trend(a, df, "Ri_Anf_Zelle_mOhm", "tab:orange", ri_title, label=tr("Flugbeginn"), trend=False, marker="^")
    _plot_trend(a, df, "Ri_End_Zelle_mOhm", "tab:purple", ri_title, label=tr("Flugende"), trend=False, marker="v")
    a.legend(fontsize=7)
    _plot_trend(ax[1][0], df, "U_ref_Zelle_V", "tab:blue",
                tr("Spannung bei {iref:.0f} A und {qref:.0f} mAh [V/Zelle]", iref=meta["iref"], qref=meta["qref"]),
                fl, "u_ref", note=tr("Vergleich unter gleichen Bedingungen. Fallender Trend = Akku wird schwächer.")
                + trend_note(),
                model=ag.get("u_ref"))
    a = ax[1][1]
    rv_title = tr("Ruhespannung Start / Ende [V/Zelle]")
    _plot_trend(a, df, "U_start_Zelle_V", "tab:blue", rv_title, label=tr("Start"), trend=False,
                note=tr("Start: voll geladen? Ende: sollte über der roten Linie liegen."))
    _plot_trend(a, df, "U_ende_Zelle_V", "tab:orange", rv_title, fl, "soc_implausible",
                label=tr("Ende (rot umkreist: passt nicht zur Ladung)"),
                trend=False, hlines=[(ch["rest_min"], tr("Mindestwert"), "tab:red")])
    a.legend(fontsize=7)
    a = ax[2][0]
    soc_title = tr("Ladezustand Start / Ende [%]")
    _plot_trend(a, df, "SoC_start_pct", "tab:blue", soc_title, label=tr("Start"), trend=False,
                note=tr("Ende sollte über der Reserve-Linie liegen.") + flag_note())
    _plot_trend(a, df, "SoC_ende_pct", "tab:orange", soc_title, fl, "deep_discharge",
                label=tr("Ende (Ladungszählung)"), trend=False, hlines=[(p.reserve_pct, tr("Reserve"), "tab:red")])
    if df["SoC_ende_Q_pct"].notna().any():
        _plot_trend(a, df, "SoC_ende_U_pct", "grey", soc_title, label=tr("Ende (aus Spannung)"), trend=False, marker="x")
    a.legend(fontsize=7)
    _plot_trend(ax[2][1], df, "U_min_Zelle_V", "tab:purple", tr("Min. Spannung unter Last [V/Zelle]"), trend=True,
                hlines=[(ch["load_min"], tr("Grenze"), "tab:red")],
                note=tr("Tiefster Spannungseinbruch bei Volllast. Unter der roten Linie: Zellen überlastet."))
    _bottom_labels_only(ax)
    fig.suptitle(tr("Akku-Zustand und Alterung"), fontsize=12, fontweight="bold")
    return fig


def figure_belastung(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig(tr("Keine Daten"))
    fig, ax = _new_fig(3, 2, size=(11, 9))
    a = ax[0][0]
    hists = [res.series[r["pfad"]]["gas_hist"] for _, r in df.iterrows() if res.series[r["pfad"]]["gas_hist"] is not None]
    if hists:
        tot = np.sum(hists, axis=0)
        centers = np.arange(5, 100, 10)
        a.bar(centers, tot / tot.sum() * 100, width=8, color="tab:blue", alpha=0.6, label=tr("alle Flüge"))
        lastr = hists[-1]
        a.step(np.arange(0, 101, 10), np.append(lastr, lastr[-1]) / lastr.sum() * 100, where="post",
               color="tab:red", lw=1.5, label=tr("letzter Flug"))
        a.legend(fontsize=7)
        a.set_ylabel(tr("Zeitanteil [%]"), fontsize=8)
    else:
        a.text(0.5, 0.5, tr("kein Gaskanal im Log"), transform=a.transAxes, ha="center", color="grey")
    a.set_title(tr("Gas-Histogramm"), loc="left")
    _note(a, tr("Wie viel Prozent der Flugzeit bei welcher Gasstellung geflogen wurde."))
    a.set_xlabel(tr("Gas [%]"), fontsize=8)
    _plot_trend(ax[0][1], df, "C_peak", "tab:red", tr("Spitzen-C-Rate je Flug [C]"), trend=False,
                note=tr("Höchster Strom geteilt durch Kapazität. Dauerhaft hohe Werte altern den Akku schneller."))
    a = ax[1][0]
    xx = df["Flug"].to_numpy(dtype=float)
    if df["E_steig_Wh"].notna().any():
        e1, e2, e3 = (np.nan_to_num(df[c].to_numpy(dtype=float)) for c in ("E_steig_Wh", "E_reise_Wh", "E_sink_Wh"))
        a.bar(xx, e1, color="tab:red", label=tr("Steigflug"))
        a.bar(xx, e2, bottom=e1, color="tab:blue", label=tr("Reise"))
        a.bar(xx, e3, bottom=e1 + e2, color="tab:green", label=tr("Sinkflug"))
        a.legend(fontsize=7)
    else:
        a.text(0.5, 0.5, tr("keine Höhe im Log"), transform=a.transAxes, ha="center", color="grey")
    a.set_title(tr("Energie je Flugphase [Wh]"), loc="left")
    flight_hover(a, df)
    _note(a, tr("Wofür die Energie verbraucht wurde (aus Höhenänderung)."))
    a.set_xlabel(tr("Flug Nr."), fontsize=8)
    _plot_trend(ax[1][1], df, "P_max_W", "tab:blue", tr("Spitzenleistung je Flug [W]"), trend=False,
                note=tr("Höchste elektrische Leistung (Spannung × Strom)."))
    a = ax[2][0]
    g_title = tr("G-Kräfte [g]")
    _plot_trend(a, df, "g_max", "tab:red", g_title, label="max", trend=False,
                note=tr("Maß für die Härte der Flugmanöver."))
    _plot_trend(a, df, "g_p95", "tab:blue", g_title, label=tr("95. Perzentil"), trend=False, marker="s")
    a.legend(fontsize=7)
    a = ax[2][1]
    a.bar(df["Flug"], df["dauer_s"], color="tab:blue", alpha=0.5, label=tr("Flugzeit"))
    a.plot(df["Flug"], df["Timer_s"], "o", color="tab:red", ms=5,
           label=tr("Timer für {reserve:.0f} % Rest", reserve=p.reserve_pct))
    a.legend(fontsize=7)
    a.set_title(tr("Flugzeit und Timer-Empfehlung [min:s]"), loc="left")
    time_axis(a, "y")
    flight_hover(a, df)
    _note(a, tr("Balken über dem roten Punkt: länger geflogen als für die Reserve empfohlen."))
    a.set_xlabel(tr("Flug Nr."), fontsize=8)
    _bottom_labels_only(ax)
    fig.suptitle(tr("Belastung und Flugprofil"), fontsize=12, fontweight="bold")
    return fig


def figure_antrieb(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig(tr("Keine Daten"))
    fig, ax = _new_fig(2, 2, size=(11, 8))
    a = ax[0][0]
    n = len(df)
    import matplotlib
    cm = matplotlib.colormaps["viridis"]
    have = False
    for k, (_, r) in enumerate(df.iterrows()):
        s = res.series[r["pfad"]]
        if s["rpm"] is None:
            continue
        have = True
        c = cm(k / max(n - 1, 1))
        m = (s["rpm"] > 1000) & (s["p"] > 100)
        a.plot(s["rpm"][m][::3] / 1000, s["p"][m][::3] / 1000, ".", ms=2, color=c, alpha=0.5)
        if np.isfinite(r["P_n"]):
            rr = np.linspace(max(s["rpm"][m].min(), 1000) if m.any() else 1000, np.max(s["rpm"]), 50)
            a.plot(rr / 1000, np.exp(r["P_a"] + r["P_n"] * np.log(rr)) / 1000, "-", color=c, lw=1.2)
    curve = meta.get("motor_curve")
    if have and curve is not None:
        import matplotlib.patheffects as pe
        halo = [pe.withStroke(linewidth=4, foreground="white")]
        xr = curve["rpm"] / 1000
        a.fill_between(xr, curve["p25"] / 1000, curve["p75"] / 1000, color="black", alpha=0.18, lw=0, zorder=3)
        for q in ("p25", "p75"):
            a.plot(xr, curve[q] / 1000, "--", color="black", lw=1, zorder=4, path_effects=halo,
                   label=tr("Streuband 25–75 %") if q == "p25" else None)
        a.plot(xr, curve["p50"] / 1000, "o-", color="black", ms=4, lw=2.2, zorder=5, path_effects=halo,
               label=tr("Gesamtkennlinie (Median aller Flüge)"))
        a.legend(fontsize=7, loc="upper left")
    if not have:
        a.text(0.5, 0.5, tr("keine Drehzahl im Log"), transform=a.transAxes, ha="center", color="grey")
    a.set_title(tr("Kennlinie: Leistung gegen Drehzahl"), loc="left")
    _note(a, tr("Farbe: frühe Flüge violett → späte gelb. Schwarz: Gesamtkennlinie aller Flüge mit Streuband. "
                "Liegt ein Flug darüber, braucht er mehr Leistung bei gleicher Drehzahl: Verschleiß/Fremdkörper."))
    a.set_xlabel(tr("Drehzahl [1000 U/min]"), fontsize=8)
    a.set_ylabel(tr("Leistung [kW]"), fontsize=8)
    rr_txt = f"{meta['rpm_ref']:.0f}" if np.isfinite(meta["rpm_ref"]) else "–"
    _plot_trend(ax[0][1], df, "P_ref_W", "tab:red", tr("Leistungsbedarf bei {rpm} U/min [W]", rpm=rr_txt), meta["flags"],
                "p_ref", note=tr("Steigt der Bedarf bei gleicher Drehzahl, läuft der Antrieb schwerer."))
    _plot_trend(ax[1][0], df, "rpm_p90", "tab:blue", tr("Drehzahl, 90. Perzentil [U/min]"),
                note=tr("Typische Höchstdrehzahl im Flug. Fallender Trend: Akku oder Antrieb lassen nach."))
    a = ax[1][1]
    _plot_trend(a, df, "Sensor_Abw_pct", "tab:purple", tr("Plausibilität: eigene mAh-Berechnung gegen ESC-Zähler [%]"),
                meta["flags"], "sensor_outlier",
                hlines=[(5, "+5 %", "tab:red"), (-5, "-5 %", "tab:red")], trend=False,
                note=tr("Innerhalb ±5 %: Verbrauchswerte verlässlich (Grundlage für Ladezustand und Timer)."))
    sd = df["Sensor_Abw_pct"].dropna()
    if len(sd):
        med = float(sd.median())
        a.axhline(med, color="tab:purple", lw=1, alpha=0.6)
        ok = abs(med) <= 5
        verdict = tr("verlässlich") if ok else tr("Sensor prüfen")
        a.text(0.99, 0.95, f"Median {med:+.1f} % – {verdict}", transform=a.transAxes,
               ha="right", va="top", fontsize=9, color="#1b7f3b" if ok else "#b00020", fontweight="bold")
        a.set_ylim(min(-6.5, sd.min() - 1), max(6.5, sd.max() + 1))
    _bottom_labels_only(ax)
    fig.suptitle(tr("Antrieb und Sensor-Plausibilität"), fontsize=12, fontweight="bold")
    return fig


def figure_funk(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig(tr("Keine Daten"))
    fig, ax = _new_fig(3, 2, size=(11, 9))
    fl = meta["flags"]
    _plot_trend(ax[0][0], df, "RSSI_min", "tab:blue", tr("RSSI-Minimum im Flug"), fl, "rssi", trend=False,
                note=tr("Schlechteste Empfangsstärke je Flug. Ethos warnt üblicherweise unter 45.") + flag_note())
    _plot_trend(ax[0][1], df, "VFR_min", "tab:green", tr("VFR-Minimum im Flug [%]"), fl, "vfr", trend=False,
                note=tr("Anteil korrekt empfangener Telemetrie-Rahmen. Unter ca. 80 % wird es kritisch."))
    _plot_trend(ax[1][0], df, "RxBatt_min_V", "tab:orange", tr("Empfängerakku: Minimum im Flug [V]"),
                fl, "rx_voltage", trend=False,
                note=tr("Tiefster Wert der Empfängerversorgung. Einbrüche deuten auf Akku, Kabel oder Servolast.")
                + flag_note())
    a = ax[1][1]
    rx_title = tr("Empfängerstrom [A]")
    _plot_trend(a, df, "RxStrom_max_A", "tab:red", rx_title, fl, "rx_current",
                label=tr("Maximum"), trend=False, marker="s",
                note=tr("Grundlast (grau) und Spitzen (rot) der Servoversorgung."))
    _plot_trend(a, df, "RxStrom_mittel_A", "grey", rx_title, label=tr("Mittelwert"), trend=False)
    a.legend(fontsize=7)
    a = ax[2][0]
    xx = df["Flug"].to_numpy(dtype=float)
    if df["RxSpitzen_n"].notna().any():
        bottom = np.zeros(len(df))
        for (cause, color), col in zip(SPIKE_CAUSES, SPIKE_COLS):
            if col not in df.columns:
                continue
            v = np.nan_to_num(df[col].to_numpy(dtype=float))
            if v.any():
                a.bar(xx, v, bottom=bottom, color=color, alpha=0.8 if color != "black" else 0.6,
                      label=label(SPIKE_LABELS, cause))
                bottom += v
        a.legend(fontsize=7)
    else:
        a.text(0.5, 0.5, tr("kein Empfängerstrom im Log"), transform=a.transAxes, ha="center", color="grey")
    a.set_title(tr("Empfängerstrom-Spitzen je Flug nach Anlass"), loc="left")
    flight_hover(a, df)
    _note(a, tr("Schwarz = ohne erkennbaren Anlass: Servos prüfen. Details im Einzelflug (Doppelklick im Logbuch)."))
    a.set_xlabel(tr("Flug Nr."), fontsize=8)
    _plot_trend(ax[2][1], df, "TxBat_min_V", "tab:purple", tr("Senderakku min. [V]"), trend=False,
                note=tr("Tiefster Wert des Senderakkus im Flug."))
    _bottom_labels_only(ax)
    fig.suptitle(tr("Funk und Bordnetz"), fontsize=12, fontweight="bold")
    return fig
