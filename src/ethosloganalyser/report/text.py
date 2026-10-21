# -*- coding: utf-8 -*-
"""Text reports: summary across all flights and single-flight details.

All texts are produced in the current language (see i18n.py) at the time the report is built.
"""

import numpy as np
import pandas as pd

from ..analysis.evaluate import FLAG_LABELS, SEVERE_FLAGS, USAGE_LABELS
from ..config import (CAP_SOURCE_LABELS, CHEM, CORR_LABELS, SOC_TOL_PCT, SPIKE_CAUSES, SPIKE_COLS, SPIKE_LABELS,
                      VOLTAGE_SOURCE_LABELS, label)
from ..i18n import fmt_date, fmt_datetime, tr
from ..utils import _f, _mmss, _trend, _window_change


def soc_lines(r, meta):
    """Lines about the state of charge of one flight (summary and single flight)."""
    L = []
    q = r["SoC_ende_Q_pct"]
    src = label(VOLTAGE_SOURCE_LABELS, r["U_ende_Quelle"])
    if np.isfinite(q):
        tag = "bad" if q < 5 else ("warn" if q < 20 else "info")
        L.append((tag, tr("Ladezustand: Start ≈ {start} %, Ende ≈ {end:.0f} %  (Ladungszählung: {drawn:.0f} mAh "
                          "entnommen von {cap:.0f} mAh {src})",
                          start=_f(r["SoC_start_pct"]), end=q, drawn=r["entnommen_mAh"], cap=meta["cap_ref"],
                          src=label(CAP_SOURCE_LABELS, meta["cap_src"]))))
        check = dict(u0=_f(r["U_start_Zelle_V"], "{:.2f}"), u1=_f(r["U_ende_Zelle_V"], "{:.2f}"), src=src,
                     soc=_f(r["SoC_ende_U_pct"]))
        if np.isfinite(r["SoC_Abw_pct"]) and abs(r["SoC_Abw_pct"]) > SOC_TOL_PCT:
            L.append(("warn", tr("  Gegenprobe Ruhespannung: {u0} → {u1} V/Zelle ({src}) ≙ {soc} % - passt nicht zur "
                                 "entnommenen Ladung ({dev:+.0f} Pkt.), verworfen", dev=r["SoC_Abw_pct"], **check)))
        else:
            L.append(("info", tr("  Gegenprobe Ruhespannung: {u0} → {u1} V/Zelle ({src}) ≙ {soc} % - passt", **check)))
    else:
        L.append(("warn", tr("Ladezustand: Start ≈ {start} %, Ende ≈ {end} % nur aus Ruhespannung ({u1} V/Zelle, {src}) - "
                             "ohne Gegenprobe. Nennkapazität eintragen für die Ladungszählung.",
                             start=_f(r["SoC_start_pct"]), end=_f(r["SoC_ende_U_pct"]),
                             u1=_f(r["U_ende_Zelle_V"], "{:.2f}"), src=src)))
    return L


def summary_lines(res, p):
    df, meta = res.df, res.meta
    L = []
    if df.empty:
        return [("bad", tr("Keine auswertbaren Flüge gefunden."))]
    n = len(df)
    x = df["Flug"].to_numpy(dtype=float)
    k = max(1, min(3, n // 3))
    cells = meta["cells"]

    L.append(("h", tr("ÜBERSICHT")))
    L.append(("info", tr("{n} Flüge ausgewertet ({first} – {last}), {skipped} Dateien übersprungen",
                         n=n, first=fmt_date(df["datum"].min()), last=fmt_date(df["datum"].max()),
                         skipped=len(res.skipped))))
    line = tr("Akku: {cells}S {chem}", cells=cells, chem=p.chem)
    if p.cells <= 0:
        line += tr("  (Zellenzahl automatisch erkannt)")
    if p.nominal_mah > 0:
        line += tr(", Nennkapazität {cap:.0f} mAh", cap=p.nominal_mah)
    L.append(("info", line))
    line = tr("Gesamt entnommen: {ah:.1f} Ah", ah=df["entnommen_mAh"].sum() / 1000)
    if np.isfinite(df["Vollzyklen_kum"].iloc[-1]):
        line += tr("  (≈ {cycles:.1f} Vollzyklen)", cycles=df["Vollzyklen_kum"].iloc[-1])
    L.append(("info", line))

    # ---------------- battery ----------------
    L.append(("h", tr("AKKU ÜBER ALLE FLÜGE")))
    L.append(("info", tr("Details zu jedem einzelnen Flug (auch zum letzten) stehen im Reiter Einzelflug.")))
    med = lambda c: float(df[c].median()) if df[c].notna().any() else np.nan
    L.append(("info", tr("Typischer Flug (Median): {dur}, {drawn} mAh entnommen, Ladezustand am Ende ≈ {soc} %, "
                         "Spitze {imax} A / {pmax} W, min. {umin} V/Zelle unter Last",
                         dur=_mmss(med("dauer_s")), drawn=_f(med("entnommen_mAh")), soc=_f(med("SoC_ende_pct")),
                         imax=_f(med("I_max_A")), pmax=_f(med("P_max_W")), umin=_f(med("U_min_Zelle_V"), "{:.2f}"))))
    L.append(("info", tr("Innenwiderstand je Zelle: Median {med} mΩ, Spanne {lo} – {hi} mΩ",
                         med=_f(med("Ri_Zelle_mOhm"), "{:.2f}"), lo=_f(df["Ri_Zelle_mOhm"].min(), "{:.2f}"),
                         hi=_f(df["Ri_Zelle_mOhm"].max(), "{:.2f}"))))
    fit = meta.get("chem_fit", {})
    if p.chem in fit:
        best = min(fit, key=fit.get)
        if fit[p.chem] > SOC_TOL_PCT and best != p.chem and fit[best] < 10:
            L.append(("bad", tr("Zellchemie prüfen: Mit {chem} passen Ruhespannung und entnommene Ladung nicht zusammen "
                                "(Abweichung im Median {dev:.0f} Prozentpunkte), mit {best} sehr gut ({best_dev:.0f} Pkt.). "
                                "Ist der Akku ein {best}-Akku? Falls es wirklich {chem} ist, liefert er deutlich weniger "
                                "als die eingetragenen {cap:.0f} mAh (geschätzt ca. {est} mAh).",
                                chem=p.chem, dev=fit[p.chem], best=best, best_dev=fit[best], cap=p.nominal_mah,
                                est=_f(meta["cap_est"]))))
        elif fit[p.chem] <= SOC_TOL_PCT:
            L.append(("ok", tr("Ruhespannung und entnommene Ladung passen zur Einstellung {chem} / {cap:.0f} mAh "
                               "(Abweichung im Median {dev:.0f} Pkt.).",
                               chem=p.chem, cap=p.nominal_mah, dev=fit[p.chem])))
    elif p.nominal_mah <= 0:
        L.append(("warn", tr("Nennkapazität nicht eingetragen: Ladezustand und Timer beruhen nur auf der "
                             "Spannungskennlinie.")))

    # ---------------- ageing ----------------
    L.append(("h", tr("ALTERUNG UND RESTKAPAZITÄT")))
    if n < 4:
        L.append(("warn", tr("Für Trend, Restkapazität (SoH) und Lebensdauer-Prognose werden mindestens 4 Flüge "
                             "mit gültigen Werten benötigt.")))
    else:
        life = []
        cw = _window_change(df, "Kap_gesch_mAh", k)
        if cw:
            first, cur = cw
            soh = cur / first * 100
            tag = "ok" if soh >= 90 else ("warn" if soh >= 80 else "bad")
            shaky = p.chem in fit and fit[p.chem] > SOC_TOL_PCT
            line = tr("Restkapazität (SoH): ca. {soh:.0f} % der Anfangskapazität  ({first:.0f} → {cur:.0f} mAh)",
                      soh=soh, first=first, cur=cur)
            if shaky:
                line += tr("  - unzuverlässig, solange die Zellchemie nicht passt (siehe oben)")
            L.append(("warn" if shaky else tag, line))
            if p.nominal_mah > 0:
                L.append(("info", tr("  absolut: ca. {cur:.0f} mAh = {pct:.0f} % der Nennkapazität",
                                     cur=cur, pct=cur / p.nominal_mah * 100)))
            trd = _trend(x, df["Kap_gesch_mAh"].to_numpy(dtype=float))
            if trd and trd[0] < 0:
                fl = max((0.8 * first - (trd[0] * x[-1] + trd[1])) / trd[0], 0)
                life.append(fl)
                L.append(("info", tr("  Prognose: 80 % SoH in ca. {n:.0f} weiteren Flügen", n=fl)))
        else:
            L.append(("warn", tr("Kapazitäts-SoH nicht bestimmbar: zu wenige Flüge mit ≥ 40 % Entladetiefe.")))
        rw = _window_change(df, "Ri_Zelle_mOhm", k)
        if rw:
            r0, r1 = rw
            ch_pct = (r1 / r0 - 1) * 100
            tag = "ok" if ch_pct < 20 else ("warn" if ch_pct < 50 else "bad")
            L.append((tag, tr("Innenwiderstand je Zelle: {r0:.2f} → {r1:.2f} mΩ ({pct:+.0f} %)", r0=r0, r1=r1, pct=ch_pct)))
            trd = _trend(x, df["Ri_Zelle_mOhm"].to_numpy(dtype=float))
            if trd and trd[0] > 0:
                fl = max((1.5 * r0 - (trd[0] * x[-1] + trd[1])) / trd[0], 0)
                life.append(fl)
                L.append(("info", tr("  Prognose: +50 % Ri (Faustregel Lebensende) in ca. {n:.0f} weiteren Flügen", n=fl)))
        uw = _window_change(df, "U_ref_Zelle_V", k)
        if uw:
            L.append(("info", tr("Spannung bei {iref:.0f} A / {qref:.0f} mAh: {u0:.3f} → {u1:.3f} V/Zelle ({mv:+.0f} mV)",
                                 iref=meta["iref"], qref=meta["qref"], u0=uw[0], u1=uw[1], mv=(uw[1] - uw[0]) * 1000)))
        if life:
            fl = min(life)
            avg = float(df["entnommen_mAh"].mean())
            cap = meta["cap_ref"]
            line = tr("Restlebensdauer (früheres Kriterium): ca. {n:.0f} Flüge", n=fl)
            if np.isfinite(cap) and cap > 0:
                line += tr(", ≈ {cycles:.0f} Vollzyklen", cycles=fl * avg / cap)
            L.append(("info", line))
        if meta["corr"]:
            L.append(("info", tr("Zusammenhang Nutzung ↔ Ri-Abweichung (Hinweis, keine Kausalität):")))
            for code, r in meta["corr"][:3]:
                L.append(("info", f"  {label(USAGE_LABELS, code)}: r = {r:+.2f}"))

    # ---------------- timer ----------------
    L.append(("h", tr("TIMER-EMPFEHLUNG")))
    if np.isfinite(meta["timer_s"]):
        L.append(("ok", tr("Landung bei {reserve:.0f} % Restkapazität: Timer ca. {timer} (Median der letzten Flüge; "
                           "geflogen: {flown})", reserve=p.reserve_pct, timer=_mmss(meta["timer_s"]),
                           flown=_mmss(float(df["dauer_s"].iloc[-5:].median())))))
        L.append(("info", tr("Basis: Kapazität ≈ {cap:.0f} mAh, Leistungsprofil der letzten Flüge.", cap=meta["cap_timer"])))
    else:
        L.append(("warn", tr("Nicht bestimmbar (Kapazität unbekannt: Nennkapazität eintragen oder Flüge mit ≥ 40 % "
                             "Entladetiefe).")))

    # ---------------- drive ----------------
    L.append(("h", tr("ANTRIEB UND SENSOREN")))
    pw = _window_change(df, "P_ref_W", k)
    if pw:
        d = (pw[1] / pw[0] - 1) * 100
        tag = "ok" if d < 5 else ("warn" if d < 10 else "bad")
        line = tr("Leistungsbedarf bei {rpm:.0f} U/min: {p0:.0f} → {p1:.0f} W ({pct:+.0f} %)",
                  rpm=meta["rpm_ref"], p0=pw[0], p1=pw[1], pct=d)
        if d >= 10:
            line += tr("  - Anstieg kann auf Verschleiß/Lagerschaden/Fremdkörper hindeuten")
        L.append((tag, line))
    elif np.isfinite(meta["rpm_ref"]):
        L.append(("info", tr("Antriebs-Trend: ab 4 Flügen verfügbar.")))
    else:
        L.append(("info", tr("Antriebs-Kennlinie nicht verfügbar (keine Drehzahl im Log).")))
    sd = df["Sensor_Abw_pct"].dropna()
    if len(sd):
        m_ = float(sd.median())
        L.append(("ok" if abs(m_) <= 3 else "warn", tr("Strommessung vs. ESC-Zähler: Median {dev:+.1f} % Abweichung", dev=m_)))

    # ---------------- radio ----------------
    L.append(("h", tr("FUNK UND BORDNETZ (schlechtester Wert über alle Flüge)")))
    parts = []
    for col, lab, unit in [("RSSI_min", "RSSI", ""), ("VFR_min", "VFR", " %"), ("RxBatt_min_V", tr("Empfängerakku"), " V"),
                           ("RxStrom_max_A", tr("Empfängerstrom max"), " A"), ("TxBat_min_V", tr("Senderakku"), " V")]:
        v = df[col].dropna()
        if len(v):
            val = v.max() if col == "RxStrom_max_A" else v.min()
            fl_no = int(df.loc[v.idxmax() if col == "RxStrom_max_A" else v.idxmin(), "Flug"])
            parts.append(tr("{label} {value}{unit} (Flug {no})", label=lab, value=f"{val:.4g}", unit=unit, no=fl_no))
    L.append(("info", "; ".join(parts) if parts else tr("keine Funkwerte im Log")))
    if df["RxSpitzen_n"].notna().any():
        L.extend(rx_summary_lines(df))

    # ---------------- warnings ----------------
    L.append(("h", tr("WARNUNGEN UND AUFFÄLLIGKEITEN")))
    if meta["warnings"]:
        for tag, text in meta["warnings"][:60]:
            L.append((tag, "• " + str(text)))
        if len(meta["warnings"]) > 60:
            L.append(("info", tr("… und {n} weitere", n=len(meta["warnings"]) - 60)))
    else:
        line = tr("Keine Auffälligkeiten festgestellt.")
        if n < 6:
            line += tr(" (Ausreißer-Erkennung erst ab 6 Flügen aktiv.)")
        L.append(("ok", line))

    L.append(("h", tr("GRENZEN DER AUSWERTUNG")))
    for s in [tr("Ohne Temperaturdaten: Ri hängt stark von der Akku-Temperatur ab - kalte Flüge wirken schlechter, "
                 "als der Akku ist."),
              tr("Keine Einzelzellspannungen: schwache Zellen/Balancing sind nicht erkennbar."),
              tr("Ladezustand am Ende: Ladungszählung, abhängig von der richtigen Nennkapazität bzw. "
                 "Kapazitätsschätzung. Die Ruhespannung ist nur eine Gegenprobe (Näherungskennlinie, Akku erholt "
                 "sich nach der Landung)."),
              tr("Empfängerstrom-Spitzen: Zuordnung über Schalterbetätigung, Knüppelbewegung, Drehrate (Roll/Nick), "
                 "G-Last, Flugzeit und Höhe - soweit diese Werte im Log stehen. Welcher Schalter z. B. das Fahrwerk "
                 "schaltet, weiß die App nicht; sie nennt den Namen der Ethos-Quelle."),
              tr("Flugphasen und Wh je 100 m Steigen sind indikativ (Höhenwerte geglättet).")]:
        L.append(("info", "• " + s))
    if res.skipped:
        L.append(("h", tr("ÜBERSPRUNGENE DATEIEN")))
        for nme, msg in res.skipped[:40]:
            L.append(("info", f"• {nme}: {msg}"))
        if len(res.skipped) > 40:
            L.append(("info", tr("… und {n} weitere", n=len(res.skipped) - 40)))
    return L


def rx_summary_lines(df):
    L = []
    base = df["RxStrom_mittel_A"].dropna()
    peak = df["RxStrom_max_A"].dropna()
    if len(base):
        line = tr("Empfängerstrom: Grundlast Ø {base:.2f} A (Median der Flüge)", base=base.median())
        if len(peak):
            line += tr(", Spitzen bis {peak:.2f} A", peak=peak.max())
        L.append(("info", line))
    tot = {c: int(np.nansum(df[col])) for (c, _), col in zip(SPIKE_CAUSES, SPIKE_COLS) if col in df.columns}
    n = sum(tot.values())
    if n:
        txt = ", ".join(f"{label(SPIKE_LABELS, c)} {v / n * 100:.0f} %" for c, v in tot.items() if v)
        share_ohne = tot.get("no_cause", 0) / n
        L.append(("warn" if share_ohne > 0.3 and n >= 5 else "info",
                  tr("Stromspitzen (alle Flüge): {n} - {shares}", n=n, shares=txt)))
    for col, code in [("Rx_r_Knueppel", "stick"), ("Rx_r_Drehrate", "rate")]:
        r = df[col].dropna() if col in df.columns else pd.Series(dtype=float)
        if len(r):
            med = float(r.median())
            interp = (tr("Strom folgt deutlich den Steuerausschlägen (Servolast)") if med >= 0.5 else
                      tr("mäßiger Zusammenhang mit den Steuerausschlägen") if med >= 0.3 else
                      tr("kaum Zusammenhang mit den Steuerausschlägen"))
            L.append(("info", tr("Zusammenhang Empfängerstrom ↔ {signal}: r = {r:+.2f} (Median) - {verdict}",
                                 signal=label(CORR_LABELS, code), r=med, verdict=interp)))
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
        return tr("{value}{unit} (Median {median}{unit})", value=_f(v, fmt), median=_f(med, fmt), unit=unit)

    vz = tr(" V/Zelle")
    L = [("h", tr("Flug {no} – {date} – {dur} – {drawn:.0f} mAh – {file}", no=no, date=fmt_datetime(r["datum"]),
                  dur=_mmss(r["dauer_s"]), drawn=r["entnommen_mAh"], file=r["datei"]))]

    # warnings for this flight first
    own = [code for code, fl in meta["flags"].items() if no in fl]
    if own:
        L.append(("h", tr("AUFFÄLLIGKEITEN IN DIESEM FLUG")))
        for code in own:
            L.append(("bad" if code in SEVERE_FLAGS else "warn", f"• {label(FLAG_LABELS, code)}"))

    L.append(("h", tr("AKKU")))
    if np.isfinite(r["Ri_mOhm"]):
        L.append(("info", tr("Innenwiderstand je Zelle: {value}", value=cmp("Ri_Zelle_mOhm", "{:.2f}", " mΩ"))))
        if np.isfinite(r["Ri_Anfang_mOhm"]) and np.isfinite(r["Ri_Ende_mOhm"]):
            L.append(("info", tr("  im Flugverlauf: Anfang {r0:.2f} → Ende {r1:.2f} mΩ ({pct:+.0f} %)",
                                 r0=r["Ri_Anf_Zelle_mOhm"], r1=r["Ri_End_Zelle_mOhm"],
                                 pct=(r["Ri_Ende_mOhm"] / r["Ri_Anfang_mOhm"] - 1) * 100)))
    else:
        L.append(("info", tr("Innenwiderstand: nicht bestimmbar (zu gleichmäßige Last)")))
    L += soc_lines(r, meta)
    if np.isfinite(r["Reserve_Zelle_V"]):
        tag = "ok" if r["Reserve_Zelle_V"] >= 0.05 else ("warn" if r["Reserve_Zelle_V"] >= 0 else "bad")
        L.append((tag, tr("Reserve zur Mindest-Ruhespannung ({rest:.2f} V/Zelle): {reserve:+.2f} V/Zelle",
                          rest=ch["rest_min"], reserve=r["Reserve_Zelle_V"])))
    if np.isfinite(r["Kap_gesch_mAh"]):
        L.append(("info", tr("Geschätzte Gesamtkapazität: {value}", value=cmp("Kap_gesch_mAh", unit=" mAh"))))
    tag = "bad" if r["U_min_Zelle_V"] < ch["load_min"] else "info"
    L.append((tag, tr("Minimale Spannung unter Last: {value} bei {imax:.0f} A Spitze",
                      value=cmp("U_min_Zelle_V", "{:.2f}", vz), imax=r["I_max_A"])))
    if np.isfinite(r["U_ref_Zelle_V"]):
        L.append(("info", tr("Spannung bei {iref:.0f} A / {qref:.0f} mAh: {value}", iref=meta["iref"], qref=meta["qref"],
                             value=cmp("U_ref_Zelle_V", "{:.3f}", vz))))

    L.append(("h", tr("BELASTUNG UND FLUGPROFIL")))
    line = tr("Spitzenleistung {value}", value=cmp("P_max_W", unit=" W"))
    if np.isfinite(r["C_peak"]):
        line = tr("C-Rate Spitze {value}", value=cmp("C_peak", "{:.1f}", " C")) + ", " + line
    L.append(("info", line))
    L.append(("info", tr("Mittlere Leistung {value}, {t80:.0f} s über 80 % des Spitzenstroms, mittleres Gas {gas} %",
                         value=cmp("P_mittel_W", unit=" W"), t80=r["Zeit_80_s"], gas=_f(r["Gas_mittel_pct"]))))
    if np.isfinite(r["E_steig_Wh"]):
        tot = r["E_steig_Wh"] + r["E_reise_Wh"] + r["E_sink_Wh"]
        L.append(("info", tr("Energie nach Phase: Steigflug {up:.0f} Wh ({pct:.0f} %), Reise {cr:.0f} Wh, "
                             "Sinkflug {dn:.0f} Wh", up=r["E_steig_Wh"], pct=r["E_steig_Wh"] / tot * 100,
                             cr=r["E_reise_Wh"], dn=r["E_sink_Wh"])))
        line = tr("Max. Höhe {value}", value=cmp("Hoehe_max_m", unit=" m"))
        if np.isfinite(r["Wh_je_100m"]):
            line += tr(", {wh} Wh je 100 m Steigen", wh=_f(r["Wh_je_100m"], "{:.1f}"))
        L.append(("info", line))
    if np.isfinite(r["g_max"]):
        L.append(("info", tr("G-Kräfte: max {value}, 95. Perzentil {p95:.1f} g", value=cmp("g_max", "{:.1f}", " g"),
                             p95=r["g_p95"])))

    L.append(("h", tr("TIMER")))
    if np.isfinite(r["Timer_s"]):
        diff = r["dauer_s"] - r["Timer_s"]
        tag = "warn" if diff > 15 else "ok"
        line = tr("Empfehlung für {reserve:.0f} % Rest bei diesem Flugprofil: {timer}, geflogen {flown} ",
                  reserve=p.reserve_pct, timer=_mmss(r["Timer_s"]), flown=_mmss(r["dauer_s"]))
        line += (tr("({diff} länger als empfohlen)", diff=_mmss(diff)) if diff > 15 else tr("(innerhalb der Empfehlung)"))
        L.append((tag, line))
    else:
        L.append(("info", tr("Keine Timer-Empfehlung (Kapazität unbekannt).")))

    L.append(("h", tr("ANTRIEB UND SENSOREN")))
    rpm_unit = tr(" U/min")
    line = tr("Drehzahl (90. Perzentil): {value}", value=cmp("rpm_p90", unit=rpm_unit))
    if np.isfinite(r["P_ref_W"]):
        line += tr("; Leistung bei {rpm:.0f} U/min: {value}", rpm=meta["rpm_ref"], value=cmp("P_ref_W", unit=" W"))
    L.append(("info", line))
    if np.isfinite(r["Sensor_Abw_pct"]):
        tag = "ok" if abs(r["Sensor_Abw_pct"]) <= 5 else "warn"
        L.append((tag, tr("Eigene mAh-Berechnung gegen ESC-Zähler: {own:.0f} gegen {esc:.0f} mAh ({dev:+.1f} %)",
                          own=r["entnommen_mAh"], esc=r["ESC_mAh"], dev=r["Sensor_Abw_pct"])))

    L.append(("h", tr("FUNK UND BORDNETZ")))
    L.append(("info", tr("RSSI min. {rssi}, VFR min. {vfr}", rssi=cmp("RSSI_min"), vfr=cmp("VFR_min", unit=" %"))))
    L.append(("info", tr("Empfängerakku min. {rx}, Senderakku min. {tx} V", rx=cmp("RxBatt_min_V", "{:.2f}", " V"),
                         tx=_f(r["TxBat_min_V"], "{:.2f}"))))
    rx = s.get("rx")
    if rx:
        L.append(("info", tr("Empfängerstrom: Grundlast {base:.2f} A, Maximum {value}, Spitzenschwelle {thr:.2f} A",
                             base=rx["base"], value=cmp("RxStrom_max_A", "{:.2f}", " A"), thr=rx["thr"])))
        if rx["corr"]:
            L.append(("info", tr("Zusammenhang mit dem Empfängerstrom: {values}",
                                 values=", ".join(f"{label(CORR_LABELS, c)} r = {v:+.2f}" for c, v in rx["corr"].items()))))
        L.append(("h", tr("EMPFÄNGERSTROM-SPITZEN ({n})", n=len(rx["spikes"]))))
        if not rx["spikes"]:
            L.append(("ok", tr("Keine Spitzen über der Schwelle.")))
        for sp in rx["spikes"]:
            tag = "warn" if sp["anlass"] == "no_cause" else "info"
            why = label(SPIKE_LABELS, sp["anlass"]) + (f" ({sp['schalter']})" if sp["schalter"] else "")
            L.append((tag, tr("  t = {t:6.1f} s  {peak:.2f} A, {dur:.1f} s  →  {why}:  Knüppel {stick} %/s, "
                              "Drehrate {rate} °/s, {g} g, Gas {gas} %, Höhe {alt} m",
                              t=sp["t"], peak=sp["peak"], dur=sp["dauer"], why=why, stick=_f(sp["stick"]),
                              rate=_f(sp["rate"]), g=_f(sp["g"], "{:.1f}"), gas=_f(sp["gas"]), alt=_f(sp["alt"]))))
    else:
        L.append(("info", tr("Kein Empfängerstrom im Log.")))
    sw = s.get("switches") or []
    if sw:
        L.append(("h", tr("SCHALTERBETÄTIGUNGEN ({n})", n=len(sw))))
        txt = "; ".join(f"{t_:.0f} s {name} {a:+.0f}→{b:+.0f}" for t_, name, a, b in sw[:40])
        L.append(("info", txt + (" …" if len(sw) > 40 else "")))
    return L
