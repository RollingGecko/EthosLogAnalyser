# -*- coding: utf-8 -*-
"""Übersichtsdiagramme über alle Flüge (Reiter Akku, Belastung, Antrieb, Funk)."""

import numpy as np

from ..config import CHEM, SPIKE_CAUSES, SPIKE_COLS
from ..plots.common import FLAG_NOTE, _bottom_labels_only, _empty_fig, _new_fig, _note, _plot_trend


def figure_akku(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig("Keine Daten")
    ch = CHEM[p.chem]
    fl = meta["flags"]
    fig, ax = _new_fig(3, 2, size=(11, 9))
    h = []
    if p.nominal_mah > 0:
        h.append((p.nominal_mah, "Nennkapazität", "grey"))
    kv = df["Kap_gesch_mAh"].dropna()
    if len(kv) >= 4:
        ref = float(np.median(kv.iloc[:max(1, min(3, len(kv) // 3))]))
        h.append((0.8 * ref, "80 % der Anfangskapazität", "tab:red"))
    _plot_trend(ax[0][0], df, "Kap_gesch_mAh", "tab:green", "Geschätzte Gesamtkapazität [mAh]", fl, "geschätzte Kapazität", h,
                note="Aus entnommener Ladung und Spannungsabfall. Fallender Trend = Alterung." + FLAG_NOTE)
    a = ax[0][1]
    _plot_trend(a, df, "Ri_Zelle_mOhm", "tab:red", "Innenwiderstand je Zelle [mΩ]", fl, "Innenwiderstand", label="Ø Flug",
                note="Steigender Trend = Alterung; +50 % gilt als Lebensende.")
    _plot_trend(a, df, "Ri_Anf_Zelle_mOhm", "tab:orange", "Innenwiderstand je Zelle [mΩ]", label="Flugbeginn", trend=False, marker="^")
    _plot_trend(a, df, "Ri_End_Zelle_mOhm", "tab:purple", "Innenwiderstand je Zelle [mΩ]", label="Flugende", trend=False, marker="v")
    a.legend(fontsize=7)
    _plot_trend(ax[1][0], df, "U_ref_Zelle_V", "tab:blue",
                f"Spannung bei {meta['iref']:.0f} A und {meta['qref']:.0f} mAh [V/Zelle]", fl, "Spannung bei Referenzlast",
                note="Vergleich unter gleichen Bedingungen. Fallender Trend = Akku wird schwächer.")
    a = ax[1][1]
    _plot_trend(a, df, "U_start_Zelle_V", "tab:blue", "Ruhespannung Start / Ende [V/Zelle]", label="Start", trend=False,
                note="Start: voll geladen? Ende: sollte über der roten Linie liegen.")
    _plot_trend(a, df, "U_ende_Zelle_V", "tab:orange", "Ruhespannung Start / Ende [V/Zelle]", fl,
                "Ladezustand unplausibel", label="Ende (rot umkreist: passt nicht zur Ladung)",
                trend=False, hlines=[(ch["rest_min"], "Mindestwert", "tab:red")])
    a.legend(fontsize=7)
    a = ax[2][0]
    _plot_trend(a, df, "SoC_start_pct", "tab:blue", "Ladezustand Start / Ende [%]", label="Start", trend=False,
                note="Ende sollte über der Reserve-Linie liegen." + FLAG_NOTE)
    _plot_trend(a, df, "SoC_ende_pct", "tab:orange", "Ladezustand Start / Ende [%]", fl, "Tiefentladung",
                label="Ende (Ladungszählung)", trend=False, hlines=[(p.reserve_pct, "Reserve", "tab:red")])
    if df["SoC_ende_Q_pct"].notna().any():
        _plot_trend(a, df, "SoC_ende_U_pct", "grey", "Ladezustand Start / Ende [%]", label="Ende (aus Spannung)",
                    trend=False, marker="x")
    a.legend(fontsize=7)
    _plot_trend(ax[2][1], df, "U_min_Zelle_V", "tab:purple", "Min. Spannung unter Last [V/Zelle]", trend=True,
                hlines=[(ch["load_min"], "Grenze", "tab:red")],
                note="Tiefster Spannungseinbruch bei Volllast. Unter der roten Linie: Zellen überlastet.")
    _bottom_labels_only(ax)
    fig.suptitle("Akku-Zustand und Alterung", fontsize=12, fontweight="bold")
    return fig


def figure_belastung(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig("Keine Daten")
    fig, ax = _new_fig(3, 2, size=(11, 9))
    a = ax[0][0]
    hists = [res.series[r["pfad"]]["gas_hist"] for _, r in df.iterrows() if res.series[r["pfad"]]["gas_hist"] is not None]
    if hists:
        tot = np.sum(hists, axis=0)
        centers = np.arange(5, 100, 10)
        a.bar(centers, tot / tot.sum() * 100, width=8, color="tab:blue", alpha=0.6, label="alle Flüge")
        lastr = hists[-1]
        a.step(np.arange(0, 101, 10), np.append(lastr, lastr[-1]) / lastr.sum() * 100, where="post",
               color="tab:red", lw=1.5, label="letzter Flug")
        a.legend(fontsize=7)
        a.set_ylabel("Zeitanteil [%]", fontsize=8)
    else:
        a.text(0.5, 0.5, "kein Gaskanal im Log", transform=a.transAxes, ha="center", color="grey")
    a.set_title("Gas-Histogramm", loc="left")
    _note(a, "Wie viel Prozent der Flugzeit bei welcher Gasstellung geflogen wurde.")
    a.set_xlabel("Gas [%]", fontsize=8)
    _plot_trend(ax[0][1], df, "C_peak", "tab:red", "Spitzen-C-Rate je Flug [C]", trend=False,
                note="Höchster Strom geteilt durch Kapazität. Dauerhaft hohe Werte altern den Akku schneller.")
    a = ax[1][0]
    xx = df["Flug"].to_numpy(dtype=float)
    if df["E_steig_Wh"].notna().any():
        e1, e2, e3 = (np.nan_to_num(df[c].to_numpy(dtype=float)) for c in ("E_steig_Wh", "E_reise_Wh", "E_sink_Wh"))
        a.bar(xx, e1, color="tab:red", label="Steigflug")
        a.bar(xx, e2, bottom=e1, color="tab:blue", label="Reise")
        a.bar(xx, e3, bottom=e1 + e2, color="tab:green", label="Sinkflug")
        a.legend(fontsize=7)
    else:
        a.text(0.5, 0.5, "keine Höhe im Log", transform=a.transAxes, ha="center", color="grey")
    a.set_title("Energie je Flugphase [Wh]", loc="left")
    _note(a, "Wofür die Energie verbraucht wurde (aus Höhenänderung).")
    a.set_xlabel("Flug Nr.", fontsize=8)
    _plot_trend(ax[1][1], df, "P_max_W", "tab:blue", "Spitzenleistung je Flug [W]", trend=False,
                note="Höchste elektrische Leistung (Spannung × Strom).")
    a = ax[2][0]
    _plot_trend(a, df, "g_max", "tab:red", "G-Kräfte [g]", label="max", trend=False,
                note="Maß für die Härte der Flugmanöver.")
    _plot_trend(a, df, "g_p95", "tab:blue", "G-Kräfte [g]", label="95. Perzentil", trend=False, marker="s")
    a.legend(fontsize=7)
    a = ax[2][1]
    a.bar(df["Flug"], df["dauer_s"], color="tab:blue", alpha=0.5, label="Flugzeit")
    a.plot(df["Flug"], df["Timer_s"], "o", color="tab:red", ms=5, label=f"Timer für {p.reserve_pct:.0f} % Rest")
    a.legend(fontsize=7)
    a.set_title("Flugzeit und Timer-Empfehlung [s]", loc="left")
    _note(a, "Balken über dem roten Punkt: länger geflogen als für die Reserve empfohlen.")
    a.set_xlabel("Flug Nr.", fontsize=8)
    _bottom_labels_only(ax)
    fig.suptitle("Belastung und Flugprofil", fontsize=12, fontweight="bold")
    return fig


def figure_antrieb(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig("Keine Daten")
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
    if not have:
        a.text(0.5, 0.5, "keine Drehzahl im Log", transform=a.transAxes, ha="center", color="grey")
    a.set_title("Kennlinie: Leistung gegen Drehzahl", loc="left")
    _note(a, "Farbe: frühe Flüge violett → späte gelb. Wandert die Kurve nach oben: Verschleiß/Fremdkörper.")
    a.set_xlabel("Drehzahl [1000 U/min]", fontsize=8)
    a.set_ylabel("Leistung [kW]", fontsize=8)
    rr_txt = f"{meta['rpm_ref']:.0f}" if np.isfinite(meta["rpm_ref"]) else "–"
    _plot_trend(ax[0][1], df, "P_ref_W", "tab:red", f"Leistungsbedarf bei {rr_txt} U/min [W]", meta["flags"],
                "Antriebsleistung bei Referenzdrehzahl",
                note="Steigt der Bedarf bei gleicher Drehzahl, läuft der Antrieb schwerer.")
    _plot_trend(ax[1][0], df, "rpm_p90", "tab:blue", "Drehzahl, 90. Perzentil [U/min]",
                note="Typische Höchstdrehzahl im Flug. Fallender Trend: Akku oder Antrieb lassen nach.")
    a = ax[1][1]
    _plot_trend(a, df, "Sensor_Abw_pct", "tab:purple", "Plausibilität: eigene mAh-Berechnung gegen ESC-Zähler [%]",
                meta["flags"], "Abweichung Strommessung/ESC-Zähler",
                hlines=[(5, "+5 %", "tab:red"), (-5, "-5 %", "tab:red")], trend=False,
                note="Innerhalb ±5 %: Verbrauchswerte verlässlich (Grundlage für Ladezustand und Timer).")
    sd = df["Sensor_Abw_pct"].dropna()
    if len(sd):
        med = float(sd.median())
        a.axhline(med, color="tab:purple", lw=1, alpha=0.6)
        ok = abs(med) <= 5
        a.text(0.99, 0.95, f"Median {med:+.1f} % – {'verlässlich' if ok else 'Sensor prüfen'}", transform=a.transAxes,
               ha="right", va="top", fontsize=9, color="#1b7f3b" if ok else "#b00020", fontweight="bold")
        a.set_ylim(min(-6.5, sd.min() - 1), max(6.5, sd.max() + 1))
    _bottom_labels_only(ax)
    fig.suptitle("Antrieb und Sensor-Plausibilität", fontsize=12, fontweight="bold")
    return fig


def figure_funk(res, p):
    df, meta = res.df, res.meta
    if df.empty:
        return _empty_fig("Keine Daten")
    fig, ax = _new_fig(3, 2, size=(11, 9))
    fl = meta["flags"]
    _plot_trend(ax[0][0], df, "RSSI_min", "tab:blue", "RSSI-Minimum im Flug", fl, "RSSI-Minimum", trend=False,
                note="Schlechteste Empfangsstärke je Flug. Ethos warnt üblicherweise unter 45." + FLAG_NOTE)
    _plot_trend(ax[0][1], df, "VFR_min", "tab:green", "VFR-Minimum im Flug [%]", fl, "VFR-Minimum", trend=False,
                note="Anteil korrekt empfangener Telemetrie-Rahmen. Unter ca. 80 % wird es kritisch.")
    _plot_trend(ax[1][0], df, "RxBatt_min_V", "tab:orange", "Empfängerakku: Minimum im Flug [V]",
                fl, "Empfängerspannung", trend=False,
                note="Tiefster Wert der Empfängerversorgung. Einbrüche deuten auf Akku, Kabel oder Servolast." + FLAG_NOTE)
    a = ax[1][1]
    _plot_trend(a, df, "RxStrom_max_A", "tab:red", "Empfängerstrom [A]", fl, "Empfängerstrom-Maximum",
                label="Maximum", trend=False, marker="s", note="Grundlast (grau) und Spitzen (rot) der Servoversorgung.")
    _plot_trend(a, df, "RxStrom_mittel_A", "grey", "Empfängerstrom [A]", label="Mittelwert", trend=False)
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
                a.bar(xx, v, bottom=bottom, color=color, alpha=0.8 if color != "black" else 0.6, label=cause)
                bottom += v
        a.legend(fontsize=7)
    else:
        a.text(0.5, 0.5, "kein Empfängerstrom im Log", transform=a.transAxes, ha="center", color="grey")
    a.set_title("Empfängerstrom-Spitzen je Flug nach Anlass", loc="left")
    _note(a, "Schwarz = ohne erkennbaren Anlass: Servos prüfen. Details im Reiter Einzelflug.")
    a.set_xlabel("Flug Nr.", fontsize=8)
    _plot_trend(ax[2][1], df, "TxBat_min_V", "tab:purple", "Senderakku min. [V]", trend=False,
                note="Tiefster Wert des Senderakkus im Flug.")
    _bottom_labels_only(ax)
    fig.suptitle("Funk und Bordnetz", fontsize=12, fontweight="bold")
    return fig
