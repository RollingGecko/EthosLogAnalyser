# -*- coding: utf-8 -*-
"""Bewertung über alle Flüge: Grenzwert-Warnungen, Ausreißer, Nutzungs-Korrelationen."""

import numpy as np

from ..config import CHEM, SOC_TOL_PCT
from ..utils import _ranges, _trend


ANOM_METRICS = [
    ("Ri_Zelle_mOhm", "hoch", "Innenwiderstand"),
    ("U_ref_Zelle_V", "niedrig", "Spannung bei Referenzlast"),
    ("Kap_gesch_mAh", "niedrig", "geschätzte Kapazität"),
    ("P_ref_W", "hoch", "Antriebsleistung bei Referenzdrehzahl"),
    ("RSSI_min", "niedrig", "RSSI-Minimum"),
    ("VFR_min", "niedrig", "VFR-Minimum"),
    ("RxBatt_min_V", "niedrig", "Empfängerspannung"),
    ("RxStrom_max_A", "hoch", "Empfängerstrom-Maximum"),
    ("Sensor_Abw_pct", "abs", "Abweichung Strommessung/ESC-Zähler"),
]


TREND_METRICS = {"Ri_Zelle_mOhm", "U_ref_Zelle_V", "Kap_gesch_mAh", "P_ref_W"}


def evaluate(df, p, meta):
    """Gibt (Liste[(Stufe, Text)], {Metrikname: Set(Flugnummern)}) zurück."""
    ch = CHEM[p.chem]
    warns, flags = [], {}
    n = len(df)
    fmt = lambda r: f"Flug {int(r['Flug'])} ({r['datum']:%d.%m.%Y})"

    # absolute Grenzwerte - gleichartige Warnungen werden zu einer Zeile zusammengefasst
    def group(mask, label, tag, text):
        if mask.any():
            nums = df.loc[mask, "Flug"].astype(int).tolist()
            flags[label] = set(nums)
            warns.append((tag, f"{label} in {len(nums)} von {n} Flügen (Flug {_ranges(nums)}): {text}"))

    abw = df["SoC_Abw_pct"].to_numpy(dtype=float)
    unpl = np.isfinite(abw) & (np.abs(abw) > SOC_TOL_PCT)
    if unpl.any():
        group(unpl, "Ladezustand unplausibel", "warn",
              f"Ladezustand aus der Endspannung weicht im Mittel um {np.mean(abw[unpl]):+.0f} Prozentpunkte von der "
              f"Ladungszählung ab (entnommen / {meta['cap_src']} {meta['cap_ref']:.0f} mAh). Verwendet wird die "
              "Ladungszählung. Mögliche Ursachen: Akkuwechsel oder Motorlauf nach der Landung im selben Log, "
              "Spannungssensor, falsche Nennkapazität oder Zellchemie.")

    res_v = df["Reserve_Zelle_V"].to_numpy(dtype=float)
    socq = df["SoC_ende_Q_pct"].to_numpy(dtype=float)
    u_end = df["U_ende_Zelle_V"].to_numpy(dtype=float)
    measured_low = (df["U_ende_Quelle"] == "gemessen").to_numpy() & np.isfinite(u_end) & (u_end < ch["rest_min"])
    deep = (np.isfinite(res_v) & (res_v < 0)) | (np.isfinite(socq) & (socq < 5)) | measured_low
    if deep.any():
        group(deep, "Tiefentladung", "bad",
              f"Ruhespannung am Ende unter {ch['rest_min']:.2f} V/Zelle ({p.chem}) oder rechnerischer Ladezustand "
              f"unter 5 % (tiefste Endspannung {np.nanmin(np.where(deep, u_end, np.nan)):.2f} V/Zelle). "
              "Bitte auch Zellchemie und Nennkapazität prüfen.")
    umin = df["U_min_Zelle_V"].to_numpy(dtype=float)
    low = np.isfinite(umin) & (umin < ch["load_min"])
    group(low, "Spannungseinbruch", "bad",
          f"Spannung unter Last fiel bis auf {np.nanmin(umin):.2f} V/Zelle (Grenze {ch['load_min']:.2f} V).")
    sab = df["Sensor_Abw_pct"].to_numpy(dtype=float)
    sens = np.isfinite(sab) & (np.abs(sab) > 5)
    group(sens, "Sensorabweichung", "warn",
          "Strommessung weicht mehr als 5 % vom ESC-Zähler ab (Sensor prüfen/kalibrieren).")
    ohne = df["RxSp_ohne"].to_numpy(dtype=float)
    group(np.isfinite(ohne) & (ohne >= 3), "Empfängerstrom-Spitzen ohne Anlass", "warn",
          "mindestens 3 Stromspitzen ohne Manöver, Start oder Landung. Servos auf Schwergängigkeit, "
          "Anschlag (Brummen in Endlage) und Defekte prüfen; Zeitpunkte siehe Einzelflug.")

    # statistische Ausreißer (robuster z-Wert, bei Alterungsgrößen relativ zum Trend), erst ab 6 Flügen
    if n >= 6:
        fl = df["Flug"].to_numpy(dtype=float)
        for col, direction, label in ANOM_METRICS:
            x = df[col].to_numpy(dtype=float)
            good = np.isfinite(x)
            if good.sum() < 6:
                continue
            med = float(np.median(x[good]))
            if col in TREND_METRICS and np.ptp(fl[good]) > 0:
                sl, ic = np.polyfit(fl[good], x[good], 1)
                ref = sl * fl + ic
            else:
                ref = np.full(n, med)
            resid = x - ref
            rmed = float(np.median(resid[good]))
            mad = float(np.median(np.abs(resid[good] - rmed))) * 1.4826
            floor = 0.5 if col == "Sensor_Abw_pct" else max(abs(med) * 0.01, 1e-9)
            z = (resid - rmed) / max(mad, floor)
            bad = {"hoch": z > 3.5, "niedrig": z < -3.5}.get(direction, np.abs(z) > 3.5) & good
            if label == "Abweichung Strommessung/ESC-Zähler" and sens.any():
                bad &= ~sens
            if bad.any():
                flags[label] = set(int(v) for v in df.loc[bad, "Flug"])
                for k in np.where(bad)[0]:
                    warns.append(("warn", f"{fmt(df.iloc[k])}: auffälliger Wert bei {label} "
                                          f"({x[k]:.4g}, erwartet ca. {ref[k]:.4g})."))
    return warns, flags


def usage_correlations(df):
    """Korreliert die Ri-Abweichung vom Trend mit Nutzungsfaktoren (nur Hinweise, keine Kausalität)."""
    out = []
    if len(df) < 8:
        return out
    x = df["Flug"].to_numpy(dtype=float)
    ri = df["Ri_Zelle_mOhm"].to_numpy(dtype=float)
    tr = _trend(x, ri)
    if tr is None:
        return out
    resid = ri - (tr[0] * x + tr[1])
    factors = [("C_peak", "Spitzen-C-Rate"), ("dSoC_pct", "Entladetiefe"), ("U_ende_Zelle_V", "Endspannung"),
               ("SoC_start_pct", "Ladezustand beim Start"), ("Pause_h", "Pause seit letztem Flug"),
               ("I_mittel_A", "mittlerer Strom"), ("dauer_s", "Flugdauer")]
    for col, label in factors:
        f = df[col].to_numpy(dtype=float)
        m = np.isfinite(f) & np.isfinite(resid)
        if m.sum() >= 8 and np.std(f[m]) > 0 and np.std(resid[m]) > 0:
            r = float(np.corrcoef(f[m], resid[m])[0, 1])
            if abs(r) >= 0.6:
                out.append((label, r))
    return sorted(out, key=lambda a: -abs(a[1]))
