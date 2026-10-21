# -*- coding: utf-8 -*-
"""Analysis of a whole log folder (cross-section over all flights)."""

import os
import glob
import numpy as np
import pandas as pd

from ..analysis.evaluate import evaluate, usage_correlations
from ..analysis.flight import analyse_file
from ..config import CHEM, Params, SOC_TOL_PCT, soc_pct


class Result:
    def __init__(self, df, skipped, total, series, meta):
        self.df, self.skipped, self.total, self.series, self.meta = df, skipped, total, series, meta


def _timer_s(series, q_limit):
    """Time at which the drawn charge reaches q_limit [mAh] (extrapolated if needed)."""
    t, q = series["t"], np.maximum.accumulate(series["q"])
    if q[-1] >= q_limit:
        return float(np.interp(q_limit, q, t))
    tail = series["i"][-240:]                          # last 60 s
    i_mean = max(float(np.mean(tail)), 1.0)
    return float(t[-1] + (q_limit - q[-1]) / (i_mean / 3.6))


def analyse_folder(folder, p: Params, progress=None):
    files = sorted(glob.glob(os.path.join(folder, "**", "*.csv"), recursive=True))
    rows, skipped, series = [], [], {}
    for n, f in enumerate(files):
        res, msg = analyse_file(f, p)
        if res is None:
            skipped.append((os.path.basename(f), msg))
        else:
            series[res["pfad"]] = res.pop("_series")
            rows.append(res)
        if progress:
            progress(n + 1, len(files))

    meta = {}
    if not rows:
        return Result(pd.DataFrame(), skipped, len(files), series, meta)

    df = pd.DataFrame(rows).sort_values("datum").reset_index(drop=True)
    df.insert(0, "Flug", np.arange(1, len(df) + 1))
    ch = CHEM[p.chem]

    # cell count: as configured, or estimated from the highest start voltage
    ustart = df["U_ruhe_start_V"].fillna(df["U_start_V"])
    cells = p.cells if p.cells > 0 else int(np.ceil(ustart.max() / (ch["full"] + 0.05)))
    meta["cells"] = cells
    df["Zellen"] = cells

    for src, dst in [("U_min_V", "U_min_Zelle_V"), ("U_ruhe_start_V", "U_start_Zelle_V"),
                     ("U_ocv_ende_V", "U_ende_gesch_Zelle_V"), ("U_ruhe_nach_V", "U_ende_mess_Zelle_V"),
                     ("U0_V", "U0_Zelle_V")]:
        df[dst] = (df[src] / cells).round(3)
    for src, dst in [("Ri_mOhm", "Ri_Zelle_mOhm"), ("Ri_Anfang_mOhm", "Ri_Anf_Zelle_mOhm"),
                     ("Ri_Ende_mOhm", "Ri_End_Zelle_mOhm")]:
        df[dst] = (df[src] / cells).round(2)

    # Resting voltage at the end: measured after motor stop preferred, otherwise model estimate.
    # A value above the start voltage is physically impossible (e.g. battery swap in the same log) -> discard.
    u_st = df["U_start_Zelle_V"].to_numpy(dtype=float)
    u_me = df["U_ende_mess_Zelle_V"].to_numpy(dtype=float)
    u_ge = df["U_ende_gesch_Zelle_V"].to_numpy(dtype=float)
    below = lambda v: np.isfinite(v) & (~np.isfinite(u_st) | (v < u_st - 0.03))
    ok_me, ok_ge = below(u_me), below(u_ge)
    df["U_ende_Zelle_V"] = np.where(ok_me, u_me, np.where(ok_ge, u_ge, np.nan)).round(3)
    df["U_ende_Quelle"] = np.where(ok_me, "gemessen", np.where(ok_ge, "geschätzt", "–"))

    # state of charge from resting voltage (approximate curve) and capacity estimate
    df["SoC_start_pct"] = np.round(soc_pct(df["U_start_Zelle_V"].to_numpy(dtype=float), p.chem), 0)
    df["SoC_ende_U_pct"] = np.round(soc_pct(df["U_ende_Zelle_V"].to_numpy(dtype=float), p.chem), 0)
    dsoc_u = (df["SoC_start_pct"] - df["SoC_ende_U_pct"]).to_numpy(dtype=float)
    ent = df["entnommen_mAh"].to_numpy(dtype=float)
    kap = np.where(dsoc_u >= 40, np.round(ent / (np.where(dsoc_u > 0, dsoc_u, np.nan) / 100.0), 0), np.nan)
    kf = kap[np.isfinite(kap)]
    if len(kf) >= 3:                                    # discard gross outliers (factor 1.6)
        med = np.median(kf)
        kap = np.where((kap > med / 1.6) & (kap < med * 1.6), kap, np.nan)
    df["Kap_gesch_mAh"] = kap

    # sensor plausibility and breaks between flights
    esc = df["ESC_mAh"].to_numpy(dtype=float)
    df["Sensor_Abw_pct"] = np.where(esc > 100, np.round((ent - esc) / np.where(esc > 0, esc, np.nan) * 100, 1), np.nan)
    df["Pause_h"] = df["datum"].diff().dt.total_seconds() / 3600.0

    # capacity reference: current estimate (last 3 valid flights) or nominal capacity
    kv = df["Kap_gesch_mAh"].dropna()
    cap_est = float(kv.iloc[-3:].median()) if len(kv) else np.nan
    cap_ref = p.nominal_mah if p.nominal_mah > 0 else cap_est
    meta.update(cap_est=cap_est, cap_ref=cap_ref,
                cap_src="Nennkapazität" if p.nominal_mah > 0 else "geschätzte Kapazität")

    # State of charge at the end: coulomb counting (start SoC - drawn/capacity) is robust against
    # voltage recovery, battery swaps and sensor glitches at the end of the log. Voltage is the cross-check.
    if np.isfinite(cap_ref) and cap_ref > 0:
        soc0 = df["SoC_start_pct"].fillna(100.0).to_numpy(dtype=float)
        df["SoC_ende_Q_pct"] = np.round(soc0 - ent / cap_ref * 100.0, 0)
    else:
        df["SoC_ende_Q_pct"] = np.nan
    sq, su = df["SoC_ende_Q_pct"].to_numpy(dtype=float), df["SoC_ende_U_pct"].to_numpy(dtype=float)
    df["SoC_Abw_pct"] = np.where(np.isfinite(sq) & np.isfinite(su), su - sq, np.nan)
    df["SoC_ende_pct"] = np.where(np.isfinite(sq), sq, su)
    df["dSoC_pct"] = df["SoC_start_pct"] - df["SoC_ende_pct"]
    abw = df["SoC_Abw_pct"].to_numpy(dtype=float)
    df["SoC_plausibel"] = np.where(np.isfinite(abw), np.abs(abw) <= SOC_TOL_PCT, np.isfinite(su))
    # voltage reserve only if the end voltage matches the drawn charge
    df["Reserve_Zelle_V"] = np.where(df["SoC_plausibel"], (df["U_ende_Zelle_V"] - ch["rest_min"]).round(3), np.nan)

    # Cell chemistry check: with which curve do resting voltage and coulomb counting agree?
    # (only meaningful with a nominal capacity entered, otherwise the check would be circular)
    meta["chem_fit"] = {}
    if p.nominal_mah > 0:
        u_end_all = df["U_ende_Zelle_V"].to_numpy(dtype=float)
        for chem_ in CHEM:
            s0 = soc_pct(u_st, chem_)
            s0 = np.where(np.isfinite(u_st), s0, 100.0)
            dd = np.abs(soc_pct(u_end_all, chem_) - (s0 - ent / p.nominal_mah * 100.0))
            dd = dd[np.isfinite(dd) & np.isfinite(u_end_all)]
            if len(dd) >= 3:
                meta["chem_fit"][chem_] = float(np.median(dd))

    # reference conditions for a fair comparison across all flights
    iref = max(5.0, round(float(df["I_mittel_A"].median()) / 5) * 5)
    qref = max(100.0, round(0.5 * float(df["entnommen_mAh"].median()) / 100) * 100)
    meta.update(iref=iref, qref=qref)
    ok = (df["entnommen_mAh"] >= qref) & df["U0_V"].notna()
    df["U_ref_Zelle_V"] = np.where(
        ok, (df["U0_V"] - df["Ri_mOhm"] / 1000.0 * iref + df["k_V_je_Ah"] * qref / 1000.0) / cells, np.nan)
    df["U_ref_Zelle_V"] = df["U_ref_Zelle_V"].round(3)

    rpm_ref = np.nan
    if df["rpm_p90"].notna().any():
        rpm_ref = round(float(df["rpm_p90"].median()) / 1000) * 1000
        okr = (df["rpm_p90"] >= 0.9 * rpm_ref) & df["P_n"].notna()
        df["P_ref_W"] = np.where(okr, np.round(np.exp(df["P_a"] + df["P_n"] * np.log(rpm_ref)), 0), np.nan)
    else:
        df["P_ref_W"] = np.nan
    meta["rpm_ref"] = rpm_ref

    df["C_peak"] = df["I_max_A"] / (cap_ref / 1000.0) if np.isfinite(cap_ref) and cap_ref > 0 else np.nan
    if np.isfinite(cap_ref) and cap_ref > 0:
        df["Vollzyklen_kum"] = (df["entnommen_mAh"].cumsum() / cap_ref).round(2)
    else:
        df["Vollzyklen_kum"] = np.nan

    # timer: time until the reserve (remaining charge = reserve_pct), per flight from its own profile
    cap_timer = cap_est if np.isfinite(cap_est) else (p.nominal_mah if p.nominal_mah > 0 else np.nan)
    if p.nominal_mah > 0:
        cap_timer = p.nominal_mah if not np.isfinite(cap_est) else min(cap_est, p.nominal_mah)
    timers = []
    for _, r in df.iterrows():
        s = series[r["pfad"]]
        soc0 = r["SoC_start_pct"] if np.isfinite(r["SoC_start_pct"]) else 100.0
        if np.isfinite(cap_timer) and soc0 > p.reserve_pct:
            timers.append(round(_timer_s(s, cap_timer * (soc0 - p.reserve_pct) / 100.0), 0))
        else:
            timers.append(np.nan)
    df["Timer_s"] = timers
    meta["timer_s"] = float(np.nanmedian(df["Timer_s"].iloc[-5:])) if df["Timer_s"].notna().any() else np.nan
    meta["cap_timer"] = cap_timer

    warnings, flags = evaluate(df, p, meta)
    meta["warnings"], meta["flags"] = warnings, flags
    df["Auffaellig"] = [
        ", ".join(name for name, fl in flags.items() if int(r["Flug"]) in fl) for _, r in df.iterrows()]
    meta["corr"] = usage_correlations(df)
    return Result(df, skipped, len(files), series, meta)
