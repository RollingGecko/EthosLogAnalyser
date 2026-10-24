# -*- coding: utf-8 -*-
"""Assessment across all flights: limit warnings, outliers, usage correlations."""

import numpy as np

from ..config import CAP_SOURCE_LABELS, CHEM, SOC_TOL_PCT
from ..i18n import LazyDate, Msg, N_
from ..utils import _col, _ranges, _trend


# flags: language-neutral code -> user-facing label (meta["flags"] and column "Auffaellig" use the codes)
FLAG_LABELS = {
    "soc_implausible": N_("Ladezustand unplausibel"),
    "deep_discharge": N_("Tiefentladung"),
    "voltage_sag": N_("Spannungseinbruch"),
    "sensor_deviation": N_("Sensorabweichung"),
    "rx_spikes_no_cause": N_("Empfängerstrom-Spitzen ohne Anlass"),
    "ri": N_("Innenwiderstand"),
    "u_ref": N_("Spannung bei Referenzlast"),
    "capacity": N_("geschätzte Kapazität"),
    "p_ref": N_("Antriebsleistung bei Referenzdrehzahl"),
    "rssi": N_("RSSI-Minimum"),
    "vfr": N_("VFR-Minimum"),
    "rx_voltage": N_("Empfängerspannung"),
    "rx_current": N_("Empfängerstrom-Maximum"),
    "sensor_outlier": N_("Abweichung Strommessung/ESC-Zähler"),
}


SEVERE_FLAGS = {"deep_discharge", "voltage_sag"}


# outlier detection: (column, direction, flag code)
ANOM_METRICS = [
    ("Ri_Zelle_mOhm", "high", "ri"),
    ("U_ref_Zelle_V", "low", "u_ref"),
    ("Kap_norm_mAh", "low", "capacity"),
    ("P_ref_W", "high", "p_ref"),
    ("RSSI_min", "low", "rssi"),
    ("VFR_min", "low", "vfr"),
    ("RxBatt_min_V", "low", "rx_voltage"),
    ("RxStrom_max_A", "high", "rx_current"),
    ("Sensor_Abw_pct", "abs", "sensor_outlier"),
]


TREND_METRICS = {"Ri_Zelle_mOhm", "U_ref_Zelle_V", "Kap_norm_mAh", "P_ref_W"}


def evaluate(df, p, meta):
    """Returns (list[(level, Msg)], {flag code: set(flight numbers)}).

    The warning texts are Msg objects, i.e. they are translated when they are displayed.
    """
    ch = CHEM[p.chem]
    warns, flags = [], {}
    n = len(df)

    # absolute limits - warnings of the same kind are merged into one line
    def group(mask, code, tag, text):
        if mask.any():
            nums = df.loc[mask, "Flug"].astype(int).tolist()
            flags[code] = set(nums)
            warns.append((tag, Msg("{label} in {n} von {total} Flügen (Flug {flights}): {text}",
                                   label=Msg(FLAG_LABELS[code]), n=len(nums), total=n, flights=_ranges(nums),
                                   text=text)))

    abw = df["SoC_Abw_pct"].to_numpy(dtype=float)
    unpl = np.isfinite(abw) & (np.abs(abw) > SOC_TOL_PCT)
    if unpl.any():
        group(unpl, "soc_implausible", "warn",
              Msg("Ladezustand aus der Endspannung weicht im Mittel um {dev:+.0f} Prozentpunkte von der "
                  "Ladungszählung ab (entnommen / {src} {cap:.0f} mAh). Verwendet wird die "
                  "Ladungszählung. Mögliche Ursachen: Akkuwechsel oder Motorlauf nach der Landung im selben Log, "
                  "Spannungssensor, falsche Nennkapazität oder Zellchemie.",
                  dev=float(np.mean(abw[unpl])), src=Msg(CAP_SOURCE_LABELS[meta["cap_src"]]), cap=meta["cap_ref"]))

    res_v = df["Reserve_Zelle_V"].to_numpy(dtype=float)
    socq = df["SoC_ende_Q_pct"].to_numpy(dtype=float)
    u_end = df["U_ende_Zelle_V"].to_numpy(dtype=float)
    measured_low = (df["U_ende_Quelle"] == "measured").to_numpy() & np.isfinite(u_end) & (u_end < ch["rest_min"])
    deep = (np.isfinite(res_v) & (res_v < 0)) | (np.isfinite(socq) & (socq < 5)) | measured_low
    if deep.any():
        group(deep, "deep_discharge", "bad",
              Msg("Ruhespannung am Ende unter {rest:.2f} V/Zelle ({chem}) oder rechnerischer Ladezustand "
                  "unter 5 % (tiefste Endspannung {low:.2f} V/Zelle). "
                  "Bitte auch Zellchemie und Nennkapazität prüfen.",
                  rest=ch["rest_min"], chem=p.chem, low=float(np.nanmin(np.where(deep, u_end, np.nan)))))
    umin = df["U_min_Zelle_V"].to_numpy(dtype=float)
    low = np.isfinite(umin) & (umin < ch["load_min"])
    if low.any():
        group(low, "voltage_sag", "bad",
              Msg("Spannung unter Last fiel bis auf {low:.2f} V/Zelle (Grenze {limit:.2f} V).",
                  low=float(np.nanmin(umin)), limit=ch["load_min"]))
    sab = df["Sensor_Abw_pct"].to_numpy(dtype=float)
    sens = np.isfinite(sab) & (np.abs(sab) > 5)
    group(sens, "sensor_deviation", "warn",
          Msg("Strommessung weicht mehr als 5 % vom ESC-Zähler ab (Sensor prüfen/kalibrieren)."))
    ohne = df["RxSp_ohne"].to_numpy(dtype=float)
    group(np.isfinite(ohne) & (ohne >= 3), "rx_spikes_no_cause", "warn",
          Msg("mindestens 3 Stromspitzen ohne Manöver, Start oder Landung. Servos auf Schwergängigkeit, "
              "Anschlag (Brummen in Endlage) und Defekte prüfen; Zeitpunkte siehe Einzelflug."))

    # receiver base current (sticks neutral): hint only when a rise is confirmed (see analysis/rx_baseline.py);
    # the reference are the earlier flights, not a fixed limit
    rb = meta.get("rx_base") or {}
    if rb.get("trend") == "up":
        warns.append(("warn", Msg("Der Grundstrom des Empfängers ist über die Flüge gestiegen ({start:.2f} → "
                                  "{end:.2f} A, Flug {first}–{last}). Servos und Anlenkungen prüfen.",
                                  start=rb["start"], end=rb["current"], first=int(rb["first"]),
                                  last=int(rb["last"]))))

    # statistical outliers (robust z-score, relative to the trend for ageing metrics), from 6 flights on
    if n >= 6:
        fl = df["Flug"].to_numpy(dtype=float)
        for col, direction, code in ANOM_METRICS:
            x = _col(df, col)
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
            bad = {"high": z > 3.5, "low": z < -3.5}.get(direction, np.abs(z) > 3.5) & good
            if code == "sensor_outlier" and sens.any():
                bad &= ~sens
            if bad.any():
                flags[code] = set(int(v) for v in df.loc[bad, "Flug"])
                for k in np.where(bad)[0]:
                    r = df.iloc[k]
                    warns.append(("warn", Msg("Flug {no} ({date}): auffälliger Wert bei {label} "
                                              "({value}, erwartet ca. {expected}).",
                                              no=int(r["Flug"]), date=LazyDate(r["datum"]),
                                              label=Msg(FLAG_LABELS[code]),
                                              value=f"{x[k]:.4g}", expected=f"{ref[k]:.4g}")))
    return warns, flags


# usage factors for the ageing correlation: code -> user-facing label
USAGE_LABELS = {
    "c_peak": N_("Spitzen-C-Rate"), "dod": N_("Entladetiefe"), "end_voltage": N_("Endspannung"),
    "start_soc": N_("Ladezustand beim Start"), "pause": N_("Pause seit letztem Flug"),
    "mean_current": N_("mittlerer Strom"), "duration": N_("Flugdauer"),
}


def usage_correlations(df):
    """Correlates the deviation of Ri from its trend with usage factors (hints only, not causality).

    Returns [(factor code, r)], strongest first; labels in USAGE_LABELS.
    """
    out = []
    if len(df) < 8:
        return out
    x = df["Flug"].to_numpy(dtype=float)
    ri = df["Ri_Zelle_mOhm"].to_numpy(dtype=float)
    trd = _trend(x, ri)
    if trd is None:
        return out
    resid = ri - (trd[0] * x + trd[1])
    factors = [("C_peak", "c_peak"), ("dSoC_pct", "dod"), ("U_ende_Zelle_V", "end_voltage"),
               ("SoC_start_pct", "start_soc"), ("Pause_h", "pause"), ("I_mittel_A", "mean_current"),
               ("dauer_s", "duration")]
    for col, code in factors:
        f = df[col].to_numpy(dtype=float)
        m = np.isfinite(f) & np.isfinite(resid)
        if m.sum() >= 8 and np.std(f[m]) > 0 and np.std(resid[m]) > 0:
            r = float(np.corrcoef(f[m], resid[m])[0, 1])
            if abs(r) >= 0.6:
                out.append((code, r))
    return sorted(out, key=lambda a: -abs(a[1]))
