# -*- coding: utf-8 -*-
"""Text reports (user-facing, German): summary across all flights and single-flight details."""

import numpy as np
import pandas as pd

from ..config import CHEM, SOC_TOL_PCT, SPIKE_CAUSES, SPIKE_COLS
from ..utils import _f, _mmss, _trend, _window_change


def soc_lines(r, meta):
    """Lines about the state of charge of one flight (summary and single flight)."""
    L = []
    q = r["SoC_ende_Q_pct"]
    if np.isfinite(q):
        tag = "bad" if q < 5 else ("warn" if q < 20 else "info")
        L.append((tag, f"Ladezustand: Start ≈ {_f(r['SoC_start_pct'])} %, Ende ≈ {q:.0f} %  "
                       f"(Ladungszählung: {r['entnommen_mAh']:.0f} mAh entnommen von {meta['cap_ref']:.0f} mAh "
                       f"{meta['cap_src']})"))
        txt = (f"  Gegenprobe Ruhespannung: {_f(r['U_start_Zelle_V'], '{:.2f}')} → "
               f"{_f(r['U_ende_Zelle_V'], '{:.2f}')} V/Zelle ({r['U_ende_Quelle']}) ≙ {_f(r['SoC_ende_U_pct'])} %")
        if np.isfinite(r["SoC_Abw_pct"]) and abs(r["SoC_Abw_pct"]) > SOC_TOL_PCT:
            L.append(("warn", txt + f" - passt nicht zur entnommenen Ladung ({r['SoC_Abw_pct']:+.0f} Pkt.), verworfen"))
        else:
            L.append(("info", txt + " - passt"))
    else:
        L.append(("warn", f"Ladezustand: Start ≈ {_f(r['SoC_start_pct'])} %, Ende ≈ {_f(r['SoC_ende_U_pct'])} % "
                          f"nur aus Ruhespannung ({_f(r['U_ende_Zelle_V'], '{:.2f}')} V/Zelle, {r['U_ende_Quelle']}) - "
                          "ohne Gegenprobe. Nennkapazität eintragen für die Ladungszählung."))
    return L


def summary_lines(res, p):
    df, meta = res.df, res.meta
    L = []
    if df.empty:
        return [("bad", "Keine auswertbaren Flüge gefunden.")]
    n = len(df)
    ch = CHEM[p.chem]
    cells = meta["cells"]
    x = df["Flug"].to_numpy(dtype=float)
    k = max(1, min(3, n // 3))
    last = df.iloc[-1]

    L.append(("h", "ÜBERSICHT"))
    L.append(("info", f"{n} Flüge ausgewertet ({df['datum'].min():%d.%m.%Y} – {df['datum'].max():%d.%m.%Y}), "
                      f"{len(res.skipped)} Dateien übersprungen"))
    L.append(("info", f"Akku: {cells}S {p.chem}" + ("  (Zellenzahl automatisch erkannt)" if p.cells <= 0 else "")
             + (f", Nennkapazität {p.nominal_mah:.0f} mAh" if p.nominal_mah > 0 else "")))
    L.append(("info", f"Gesamt entnommen: {df['entnommen_mAh'].sum() / 1000:.1f} Ah"
                      + (f"  (≈ {df['Vollzyklen_kum'].iloc[-1]:.1f} Vollzyklen)" if np.isfinite(df['Vollzyklen_kum'].iloc[-1]) else "")))

    # ---------------- battery ----------------
    L.append(("h", "AKKU ÜBER ALLE FLÜGE"))
    L.append(("info", "Details zu jedem einzelnen Flug (auch zum letzten) stehen im Reiter Einzelflug."))
    med = lambda c: float(df[c].median()) if df[c].notna().any() else np.nan
    L.append(("info", f"Typischer Flug (Median): {_mmss(med('dauer_s'))}, {_f(med('entnommen_mAh'))} mAh entnommen, "
                      f"Ladezustand am Ende ≈ {_f(med('SoC_ende_pct'))} %, Spitze {_f(med('I_max_A'))} A / "
                      f"{_f(med('P_max_W'))} W, min. {_f(med('U_min_Zelle_V'), '{:.2f}')} V/Zelle unter Last"))
    L.append(("info", f"Innenwiderstand je Zelle: Median {_f(med('Ri_Zelle_mOhm'), '{:.2f}')} mΩ, "
                      f"Spanne {_f(df['Ri_Zelle_mOhm'].min(), '{:.2f}')} – {_f(df['Ri_Zelle_mOhm'].max(), '{:.2f}')} mΩ"))
    fit = meta.get("chem_fit", {})
    if p.chem in fit:
        best = min(fit, key=fit.get)
        if fit[p.chem] > SOC_TOL_PCT and best != p.chem and fit[best] < 10:
            L.append(("bad", f"Zellchemie prüfen: Mit {p.chem} passen Ruhespannung und entnommene Ladung nicht zusammen "
                             f"(Abweichung im Median {fit[p.chem]:.0f} Prozentpunkte), mit {best} sehr gut "
                             f"({fit[best]:.0f} Pkt.). Ist der Akku ein {best}-Akku? Falls es wirklich {p.chem} ist, liefert "
                             f"er deutlich weniger als die eingetragenen {p.nominal_mah:.0f} mAh "
                             f"(geschätzt ca. {_f(meta['cap_est'])} mAh)."))
        elif fit[p.chem] <= SOC_TOL_PCT:
            L.append(("ok", f"Ruhespannung und entnommene Ladung passen zur Einstellung {p.chem} / "
                            f"{p.nominal_mah:.0f} mAh (Abweichung im Median {fit[p.chem]:.0f} Pkt.)."))
    elif p.nominal_mah <= 0:
        L.append(("warn", "Nennkapazität nicht eingetragen: Ladezustand und Timer beruhen nur auf der Spannungskennlinie."))

    # ---------------- ageing ----------------
    L.append(("h", "ALTERUNG UND RESTKAPAZITÄT"))
    if n < 4:
        L.append(("warn", "Für Trend, Restkapazität (SoH) und Lebensdauer-Prognose werden mindestens 4 Flüge "
                          "mit gültigen Werten benötigt."))
    else:
        life = []
        cw = _window_change(df, "Kap_gesch_mAh", k)
        if cw:
            first, cur = cw
            soh = cur / first * 100
            tag = "ok" if soh >= 90 else ("warn" if soh >= 80 else "bad")
            fit = meta.get("chem_fit", {})
            shaky = p.chem in fit and fit[p.chem] > SOC_TOL_PCT
            L.append(("warn" if shaky else tag,
                      f"Restkapazität (SoH): ca. {soh:.0f} % der Anfangskapazität  ({first:.0f} → {cur:.0f} mAh)"
                      + ("  - unzuverlässig, solange die Zellchemie nicht passt (siehe oben)" if shaky else "")))
            if p.nominal_mah > 0:
                L.append(("info", f"  absolut: ca. {cur:.0f} mAh = {cur / p.nominal_mah * 100:.0f} % der Nennkapazität"))
            tr = _trend(x, df["Kap_gesch_mAh"].to_numpy(dtype=float))
            if tr and tr[0] < 0:
                fl = max((0.8 * first - (tr[0] * x[-1] + tr[1])) / tr[0], 0)
                life.append(fl)
                L.append(("info", f"  Prognose: 80 % SoH in ca. {fl:.0f} weiteren Flügen"))
        else:
            L.append(("warn", "Kapazitäts-SoH nicht bestimmbar: zu wenige Flüge mit ≥ 40 % Entladetiefe."))
        rw = _window_change(df, "Ri_Zelle_mOhm", k)
        if rw:
            r0, r1 = rw
            ch_pct = (r1 / r0 - 1) * 100
            tag = "ok" if ch_pct < 20 else ("warn" if ch_pct < 50 else "bad")
            L.append((tag, f"Innenwiderstand je Zelle: {r0:.2f} → {r1:.2f} mΩ ({ch_pct:+.0f} %)"))
            tr = _trend(x, df["Ri_Zelle_mOhm"].to_numpy(dtype=float))
            if tr and tr[0] > 0:
                fl = max((1.5 * r0 - (tr[0] * x[-1] + tr[1])) / tr[0], 0)
                life.append(fl)
                L.append(("info", f"  Prognose: +50 % Ri (Faustregel Lebensende) in ca. {fl:.0f} weiteren Flügen"))
        uw = _window_change(df, "U_ref_Zelle_V", k)
        if uw:
            L.append(("info", f"Spannung bei {meta['iref']:.0f} A / {meta['qref']:.0f} mAh: "
                              f"{uw[0]:.3f} → {uw[1]:.3f} V/Zelle ({(uw[1] - uw[0]) * 1000:+.0f} mV)"))
        if life:
            fl = min(life)
            avg = float(df["entnommen_mAh"].mean())
            cap = meta["cap_ref"]
            cyc = f", ≈ {fl * avg / cap:.0f} Vollzyklen" if np.isfinite(cap) and cap > 0 else ""
            L.append(("info", f"Restlebensdauer (früheres Kriterium): ca. {fl:.0f} Flüge{cyc}"))
        if meta["corr"]:
            L.append(("info", "Zusammenhang Nutzung ↔ Ri-Abweichung (Hinweis, keine Kausalität):"))
            for label, r in meta["corr"][:3]:
                L.append(("info", f"  {label}: r = {r:+.2f}"))

    # ---------------- Timer ----------------
    L.append(("h", "TIMER-EMPFEHLUNG"))
    if np.isfinite(meta["timer_s"]):
        L.append(("ok", f"Landung bei {p.reserve_pct:.0f} % Restkapazität: Timer ca. {_mmss(meta['timer_s'])} "
                        f"(Median der letzten Flüge; geflogen: {_mmss(float(df['dauer_s'].iloc[-5:].median()))})"))
        L.append(("info", f"Basis: Kapazität ≈ {meta['cap_timer']:.0f} mAh, Leistungsprofil der letzten Flüge."))
    else:
        L.append(("warn", "Nicht bestimmbar (Kapazität unbekannt: Nennkapazität eintragen oder Flüge mit ≥ 40 % Entladetiefe)."))

    # ---------------- drive ----------------
    L.append(("h", "ANTRIEB UND SENSOREN"))
    pw = _window_change(df, "P_ref_W", k)
    if pw:
        d = (pw[1] / pw[0] - 1) * 100
        tag = "ok" if d < 5 else ("warn" if d < 10 else "bad")
        L.append((tag, f"Leistungsbedarf bei {meta['rpm_ref']:.0f} U/min: {pw[0]:.0f} → {pw[1]:.0f} W ({d:+.0f} %)"
                       + ("  - Anstieg kann auf Verschleiß/Lagerschaden/Fremdkörper hindeuten" if d >= 10 else "")))
    elif np.isfinite(meta["rpm_ref"]):
        L.append(("info", "Antriebs-Trend: ab 4 Flügen verfügbar."))
    else:
        L.append(("info", "Antriebs-Kennlinie nicht verfügbar (keine Drehzahl im Log)."))
    sd = df["Sensor_Abw_pct"].dropna()
    if len(sd):
        med = float(sd.median())
        L.append(("ok" if abs(med) <= 3 else "warn",
                  f"Strommessung vs. ESC-Zähler: Median {med:+.1f} % Abweichung"))

    # ---------------- radio ----------------
    L.append(("h", "FUNK UND BORDNETZ (schlechtester Wert über alle Flüge)"))
    parts = []
    for col, lab, unit in [("RSSI_min", "RSSI", ""), ("VFR_min", "VFR", " %"), ("RxBatt_min_V", "Empfängerakku", " V"),
                           ("RxStrom_max_A", "Empfängerstrom max", " A"), ("TxBat_min_V", "Senderakku", " V")]:
        v = df[col].dropna()
        if len(v):
            val = v.max() if col == "RxStrom_max_A" else v.min()
            fl_no = int(df.loc[v.idxmax() if col == "RxStrom_max_A" else v.idxmin(), "Flug"])
            parts.append(f"{lab} {val:.4g}{unit} (Flug {fl_no})")
    L.append(("info", "; ".join(parts) if parts else "keine Funkwerte im Log"))
    if df["RxSpitzen_n"].notna().any():
        L.extend(rx_summary_lines(df))

    # ---------------- warnings ----------------
    L.append(("h", "WARNUNGEN UND AUFFÄLLIGKEITEN"))
    if meta["warnings"]:
        for tag, text in meta["warnings"][:60]:
            L.append((tag, "• " + text))
        if len(meta["warnings"]) > 60:
            L.append(("info", f"… und {len(meta['warnings']) - 60} weitere"))
    else:
        L.append(("ok", "Keine Auffälligkeiten festgestellt."
                        + (" (Ausreißer-Erkennung erst ab 6 Flügen aktiv.)" if n < 6 else "")))

    L.append(("h", "GRENZEN DER AUSWERTUNG"))
    for s in ["Ohne Temperaturdaten: Ri hängt stark von der Akku-Temperatur ab - kalte Flüge wirken schlechter, als der Akku ist.",
              "Keine Einzelzellspannungen: schwache Zellen/Balancing sind nicht erkennbar.",
              "Ladezustand am Ende: Ladungszählung, abhängig von der richtigen Nennkapazität bzw. Kapazitätsschätzung. "
              "Die Ruhespannung ist nur eine Gegenprobe (Näherungskennlinie, Akku erholt sich nach der Landung).",
              "Empfängerstrom-Spitzen: Zuordnung über Schalterbetätigung, Knüppelbewegung, Drehrate (Roll/Nick), "
              "G-Last, Flugzeit und Höhe - soweit diese Werte im Log stehen. Welcher Schalter z. B. das Fahrwerk "
              "schaltet, weiß die App nicht; sie nennt den Namen der Ethos-Quelle.",
              "Flugphasen und Wh je 100 m Steigen sind indikativ (Höhenwerte geglättet)."]:
        L.append(("info", "• " + s))
    if res.skipped:
        L.append(("h", "ÜBERSPRUNGENE DATEIEN"))
        for nme, msg in res.skipped[:40]:
            L.append(("info", f"• {nme}: {msg}"))
        if len(res.skipped) > 40:
            L.append(("info", f"… und {len(res.skipped) - 40} weitere"))
    return L


def rx_summary_lines(df):
    L = []
    base = df["RxStrom_mittel_A"].dropna()
    peak = df["RxStrom_max_A"].dropna()
    if len(base):
        L.append(("info", f"Empfängerstrom: Grundlast Ø {base.median():.2f} A (Median der Flüge)"
                          + (f", Spitzen bis {peak.max():.2f} A" if len(peak) else "")))
    tot = {c: int(np.nansum(df[col])) for (c, _), col in zip(SPIKE_CAUSES, SPIKE_COLS) if col in df.columns}
    n = sum(tot.values())
    if n:
        txt = ", ".join(f"{c} {v / n * 100:.0f} %" for c, v in tot.items() if v)
        share_ohne = tot.get("ohne erkennbaren Anlass", 0) / n
        L.append(("warn" if share_ohne > 0.3 and n >= 5 else "info",
                  f"Stromspitzen (alle Flüge): {n} - {txt}"))
    for col, label in [("Rx_r_Knueppel", "Knüppelaktivität"), ("Rx_r_Drehrate", "Drehrate")]:
        r = df[col].dropna() if col in df.columns else pd.Series(dtype=float)
        if len(r):
            med = float(r.median())
            interp = ("Strom folgt deutlich den Steuerausschlägen (Servolast)" if med >= 0.5 else
                      "mäßiger Zusammenhang mit den Steuerausschlägen" if med >= 0.3 else
                      "kaum Zusammenhang mit den Steuerausschlägen")
            L.append(("info", f"Zusammenhang Empfängerstrom ↔ {label}: r = {med:+.2f} (Median) - {interp}"))
            break
    return L


def flight_detail_lines(res, p, path):
    """All detail values of one flight compared with the median of all flights."""
    df, meta = res.df, res.meta
    r = df[df["pfad"] == path].iloc[0]
    s = res.series[path]
    no = int(r["Flug"])
    ch = CHEM[p.chem]

    def cmp(col, fmt="{:.0f}", unit=""):
        v = r[col]
        med = df[col].median() if df[col].notna().any() else np.nan
        return f"{_f(v, fmt)}{unit} (Median {_f(med, fmt)}{unit})"

    L = [("h", f"Flug {no} – {r['datum']:%d.%m.%Y %H:%M} – {_mmss(r['dauer_s'])} – {r['entnommen_mAh']:.0f} mAh – "
               f"{r['datei']}")]

    # warnings for this flight first
    own = [name for name, fl in meta["flags"].items() if no in fl]
    if own:
        L.append(("h", "AUFFÄLLIGKEITEN IN DIESEM FLUG"))
        for name in own:
            tag = "bad" if name in ("Tiefentladung", "Spannungseinbruch") else "warn"
            L.append((tag, f"• {name}"))

    L.append(("h", "AKKU"))
    if np.isfinite(r["Ri_mOhm"]):
        L.append(("info", f"Innenwiderstand je Zelle: {cmp('Ri_Zelle_mOhm', '{:.2f}', ' mΩ')}"))
        if np.isfinite(r["Ri_Anfang_mOhm"]) and np.isfinite(r["Ri_Ende_mOhm"]):
            L.append(("info", f"  im Flugverlauf: Anfang {r['Ri_Anf_Zelle_mOhm']:.2f} → Ende {r['Ri_End_Zelle_mOhm']:.2f} mΩ "
                              f"({(r['Ri_Ende_mOhm'] / r['Ri_Anfang_mOhm'] - 1) * 100:+.0f} %)"))
    else:
        L.append(("info", "Innenwiderstand: nicht bestimmbar (zu gleichmäßige Last)"))
    L += soc_lines(r, meta)
    if np.isfinite(r["Reserve_Zelle_V"]):
        tag = "ok" if r["Reserve_Zelle_V"] >= 0.05 else ("warn" if r["Reserve_Zelle_V"] >= 0 else "bad")
        L.append((tag, f"Reserve zur Mindest-Ruhespannung ({ch['rest_min']:.2f} V/Zelle): {r['Reserve_Zelle_V']:+.2f} V/Zelle"))
    if np.isfinite(r["Kap_gesch_mAh"]):
        L.append(("info", f"Geschätzte Gesamtkapazität: {cmp('Kap_gesch_mAh', unit=' mAh')}"))
    tag = "bad" if r["U_min_Zelle_V"] < ch["load_min"] else "info"
    L.append((tag, f"Minimale Spannung unter Last: {cmp('U_min_Zelle_V', '{:.2f}', ' V/Zelle')} bei {r['I_max_A']:.0f} A Spitze"))
    if np.isfinite(r["U_ref_Zelle_V"]):
        L.append(("info", f"Spannung bei {meta['iref']:.0f} A / {meta['qref']:.0f} mAh: {cmp('U_ref_Zelle_V', '{:.3f}', ' V/Zelle')}"))

    L.append(("h", "BELASTUNG UND FLUGPROFIL"))
    cp = f"C-Rate Spitze {cmp('C_peak', '{:.1f}', ' C')}, " if np.isfinite(r["C_peak"]) else ""
    L.append(("info", f"{cp}Spitzenleistung {cmp('P_max_W', unit=' W')}"))
    L.append(("info", f"Mittlere Leistung {cmp('P_mittel_W', unit=' W')}, {r['Zeit_80_s']:.0f} s über 80 % des Spitzenstroms, "
                      f"mittleres Gas {_f(r['Gas_mittel_pct'])} %"))
    if np.isfinite(r["E_steig_Wh"]):
        tot = r["E_steig_Wh"] + r["E_reise_Wh"] + r["E_sink_Wh"]
        L.append(("info", f"Energie nach Phase: Steigflug {r['E_steig_Wh']:.0f} Wh ({r['E_steig_Wh'] / tot * 100:.0f} %), "
                          f"Reise {r['E_reise_Wh']:.0f} Wh, Sinkflug {r['E_sink_Wh']:.0f} Wh"))
        L.append(("info", f"Max. Höhe {cmp('Hoehe_max_m', unit=' m')}"
                          + (f", {_f(r['Wh_je_100m'], '{:.1f}')} Wh je 100 m Steigen" if np.isfinite(r["Wh_je_100m"]) else "")))
    if np.isfinite(r["g_max"]):
        L.append(("info", f"G-Kräfte: max {cmp('g_max', '{:.1f}', ' g')}, 95. Perzentil {r['g_p95']:.1f} g"))

    L.append(("h", "TIMER"))
    if np.isfinite(r["Timer_s"]):
        diff = r["dauer_s"] - r["Timer_s"]
        tag = "warn" if diff > 15 else "ok"
        L.append((tag, f"Empfehlung für {p.reserve_pct:.0f} % Rest bei diesem Flugprofil: {_mmss(r['Timer_s'])}, "
                       f"geflogen {_mmss(r['dauer_s'])} "
                       + (f"({_mmss(diff)} länger als empfohlen)" if diff > 15 else "(innerhalb der Empfehlung)")))
    else:
        L.append(("info", "Keine Timer-Empfehlung (Kapazität unbekannt)."))

    L.append(("h", "ANTRIEB UND SENSOREN"))
    L.append(("info", f"Drehzahl (90. Perzentil): {cmp('rpm_p90', unit=' U/min')}"
                      + (f"; Leistung bei {meta['rpm_ref']:.0f} U/min: {cmp('P_ref_W', unit=' W')}" if np.isfinite(r["P_ref_W"]) else "")))
    if np.isfinite(r["Sensor_Abw_pct"]):
        tag = "ok" if abs(r["Sensor_Abw_pct"]) <= 5 else "warn"
        L.append((tag, f"Eigene mAh-Berechnung gegen ESC-Zähler: {r['entnommen_mAh']:.0f} gegen {r['ESC_mAh']:.0f} mAh "
                       f"({r['Sensor_Abw_pct']:+.1f} %)"))

    L.append(("h", "FUNK UND BORDNETZ"))
    L.append(("info", f"RSSI min. {cmp('RSSI_min')}, VFR min. {cmp('VFR_min', unit=' %')}"))
    L.append(("info", f"Empfängerakku min. {cmp('RxBatt_min_V', '{:.2f}', ' V')}, Senderakku min. {_f(r['TxBat_min_V'], '{:.2f}')} V"))
    rx = s.get("rx")
    if rx:
        L.append(("info", f"Empfängerstrom: Grundlast {rx['base']:.2f} A, Maximum {cmp('RxStrom_max_A', '{:.2f}', ' A')}, "
                          f"Spitzenschwelle {rx['thr']:.2f} A"))
        if rx["corr"]:
            L.append(("info", "Zusammenhang mit dem Empfängerstrom: "
                              + ", ".join(f"{k} r = {v:+.2f}" for k, v in rx["corr"].items())))
        L.append(("h", f"EMPFÄNGERSTROM-SPITZEN ({len(rx['spikes'])})"))
        if not rx["spikes"]:
            L.append(("ok", "Keine Spitzen über der Schwelle."))
        for sp in rx["spikes"]:
            tag = "warn" if sp["anlass"] == "ohne erkennbaren Anlass" else "info"
            why = sp["anlass"] + (f" ({sp['schalter']})" if sp["schalter"] else "")
            L.append((tag, f"  t = {sp['t']:6.1f} s  {sp['peak']:.2f} A, {sp['dauer']:.1f} s  →  {why}:  "
                           f"Knüppel {_f(sp['stick'])} %/s, Drehrate {_f(sp['rate'])} °/s, {_f(sp['g'], '{:.1f}')} g, "
                           f"Gas {_f(sp['gas'])} %, Höhe {_f(sp['alt'])} m"))
    else:
        L.append(("info", "Kein Empfängerstrom im Log."))
    sw = s.get("switches") or []
    if sw:
        L.append(("h", f"SCHALTERBETÄTIGUNGEN ({len(sw)})"))
        txt = "; ".join(f"{t_:.0f} s {name} {a:+.0f}→{b:+.0f}" for t_, name, a, b in sw[:40])
        L.append(("info", txt + (" …" if len(sw) > 40 else "")))
    return L
