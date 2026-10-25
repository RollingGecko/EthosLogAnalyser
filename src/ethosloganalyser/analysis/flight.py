# -*- coding: utf-8 -*-
"""Analysis of a single flight (one log file)."""

import os
import numpy as np
import pandas as pd

from ..analysis.rx_spikes import rx_spike_analysis
from ..config import Params, SPIKE_CAUSES, STEP
from ..i18n import Msg
from ..io.ethos_log import CURR_KEYS, VOLT_KEYS, _active_series, _exact_series, _file_datetime, _find_col, _first_series, _numeric_cols, _switch_columns, _time_seconds, _to_num
from ..utils import _mmss, _nanmax, _nanmin, _rolling


def analyse_frame(df, path, p: Params, start_time=None):
    """Analyses one log that has already been read (``read_log_bytes``, or the time series stored in the flight
    database). Returns (dict, "ok") or (None, Msg with the reason why the log is no flight with battery data).

    path is only used for the file name and the date in the result; start_time (datetime) replaces the date
    taken from the file name, e.g. for a log stored in the flight database whose file no longer exists.
    """
    cv = _find_col(df.columns, VOLT_KEYS, p.col_voltage)
    ci = _find_col(df.columns, CURR_KEYS, p.col_current)
    if cv is None or ci is None:
        return None, Msg("Spalten nicht gefunden (Spannung={cv}, Strom={ci}). Verfügbar: {cols}",
                          cv=cv, ci=ci, cols=list(df.columns))
    t = _time_seconds(df)
    if t is None:
        return None, Msg("Zeitspalte nicht erkannt")

    # Ethos logs each sensor in its own rows -> fill gaps with the last value
    work = pd.DataFrame({"t": t, "u": _to_num(df[cv]).to_numpy(dtype=float),
                         "i": _to_num(df[ci]).to_numpy(dtype=float)}, index=df.index)
    extras = {
        "gas": _first_series(df, ["gas", "thr"]),
        "rpm": (_first_series(df, ["esc rpm"]) if _first_series(df, ["esc rpm"]) is not None
                else _first_series(df, ["rpm"])),
        "alt": _first_series(df, ["altitude", "höhe", "hoehe"]),
        "ax": _first_series(df, ["accx"]), "ay": _first_series(df, ["accy"]), "az": _first_series(df, ["accz"]),
        "rssi": _active_series(df, ["rssi"]),
        "vfr": _active_series(df, ["vfr"]),
        "rxi": _active_series(df, ["rxcurrent", "rx current", "rx curr"]),
        "rxu": _active_series(df, ["rxbatt", "rx batt", "rxbat"]),
        "roll": _first_series(df, ["roll", "r.angle"]),
        "pitch": _first_series(df, ["pitch", "nick", "p.angle"]),
        # stick channels (Ethos sources, exact names): aileron, elevator, rudder
        "qr": _exact_series(df, ["QR", "Quer", "Ail", "Aileron", "Querruder"]),
        "hr": _exact_series(df, ["HR", "Ele", "Elevator", "Höhenruder"]),
        "sr": _exact_series(df, ["SR", "Rud", "Rudder", "Seite", "Seitenruder"]),
    }
    switch_cols = _switch_columns(df)
    for k_, (name, sr) in enumerate(switch_cols):
        extras[f"sw{k_}"] = sr
    for k, sr in extras.items():
        if sr is not None:
            work[k] = sr.to_numpy(dtype=float)
    work = work[np.isfinite(work["t"])].sort_values("t")
    if work["u"].notna().sum() < 20 or work["i"].notna().sum() < 20:
        return None, Msg("Spannung/Strom kaum vorhanden (Sensor nicht verbunden?)")
    if work["u"].abs().max() < 1.0 and work["i"].abs().max() < 0.5:
        return None, Msg("nur Nullwerte in {cv}/{ci} (Bodenlog ohne Akku-Telemetrie)", cv=cv, ci=ci)
    fillc = [c for c in work.columns if c != "t"]
    work[fillc] = work[fillc].ffill(limit=20)
    work = work.dropna(subset=["u", "i"]).reset_index(drop=True)
    if len(work) < 20:
        return None, Msg("zu wenige Datenpunkte")

    # only consider the period with the motor running
    act = np.where(work["i"].to_numpy() > p.active_current_a)[0]
    if len(act) < 10:
        return None, Msg("kein Motorstrom erkannt")
    # Split motor running into blocks (gap > 20 s) and take the block with the largest charge -
    # a short motor test before take-off or after a battery swap is thus not counted as flight.
    ta, ia = work["t"].to_numpy()[act], work["i"].to_numpy()[act]
    cut = np.flatnonzero(np.diff(ta) > 20.0) + 1
    blocks = np.split(np.arange(len(act)), cut)
    blk = max(blocks, key=lambda b: float(np.sum(ia[b])))
    a0, a1 = act[blk[0]], act[blk[-1]]
    pre = work.iloc[max(0, a0 - 15):a0]
    u_rest_start = float(np.median(pre["u"])) if len(pre) >= 3 else np.nan   # resting voltage before take-off

    # Measured voltage after motor stop (5-30 s after the last motor current, no load).
    # The battery keeps recovering, so the value is rather slightly too low (conservative).
    u_rest_after = np.nan
    post = work.iloc[a1 + 1:]
    if len(post):
        tp = post["t"].to_numpy() - float(work["t"].iloc[a1])
        m = (tp >= 5) & (tp <= 30) & (post["i"].to_numpy() < p.active_current_a)
        if m.sum() >= 3:      # last values in the window: closest to the true resting voltage
            u_rest_after = float(np.median(post["u"].to_numpy()[m][-3:]))

    win = work.iloc[a0:a1 + 1]
    idx = win.index
    t = win["t"].to_numpy()
    u = win["u"].to_numpy()
    i = win["i"].to_numpy()
    dur = float(t[-1] - t[0])
    if dur < p.min_flight_s:
        return None, Msg("zu kurz ({dur} < {min})", dur=_mmss(dur), min=_mmss(p.min_flight_s))

    dt = np.clip(np.diff(t, prepend=t[0]), 0, 5.0)         # do not integrate over gaps in the log
    q_mah = np.cumsum(i * dt) / 3.6                        # A*s -> mAh
    e_wh = float(np.sum(u * i * dt) / 3600.0)

    # --- time grid ------------------------------------------------------------
    tg = np.arange(t[0], t[-1], STEP)
    if len(tg) < 40:
        return None, Msg("zu wenige Datenpunkte")

    def grid(col):
        if col in win.columns and win[col].notna().sum() > 5:
            return np.interp(tg, t, win[col].ffill().bfill().to_numpy(dtype=float))
        return None

    ug, ig = np.interp(tg, t, u), np.interp(tg, t, i)
    qg_mah = np.interp(tg, t, q_mah)
    pg = ug * ig
    gasg, rpmg, altg = grid("gas"), grid("rpm"), grid("alt")
    axg, ayg, azg = grid("ax"), grid("ay"), grid("az")
    rssig, vfrg, rxig, rxug = grid("rssi"), grid("vfr"), grid("rxi"), grid("rxu")
    rollg, pitchg = grid("roll"), grid("pitch")
    sticks = {}
    for key, code in [("qr", "aileron"), ("hr", "elevator"), ("sr", "rudder")]:
        g_ = grid(key)
        if g_ is not None and np.ptp(g_) > 20:
            sticks[code] = np.clip(g_ / 1024.0 * 100.0, -100, 100)          # stick travel [%]
    stick_act = None
    if sticks:      # stick activity: sum of stick speeds [%/s] - a measure of servo work
        stick_act = np.sum([np.abs(np.gradient(_rolling(v, 2), STEP)) for v in sticks.values()], axis=0)
        stick_act = _rolling(stick_act, 3)
    # switch events during the flight (time relative to motor start)
    switch_ev = []
    t_win = win["t"].to_numpy()
    for k_, (name, _) in enumerate(switch_cols):
        col = f"sw{k_}"
        if col not in win.columns:
            continue
        v = win[col].ffill().bfill().to_numpy(dtype=float)
        for j in np.flatnonzero(np.diff(v) != 0):
            if np.isfinite(v[j]) and np.isfinite(v[j + 1]):
                switch_ev.append((float(t_win[j + 1] - tg[0]), name, v[j], v[j + 1]))
    switch_ev.sort()

    # --- internal resistance: U = c0 + c1*I + c2*Q  (Ri = -c1) ------------------------
    # Ethos logs current with a time offset to voltage -> search for the best offset.
    ri = u0 = k_v = r2 = lag_best = np.nan
    ri_seg = [np.nan, np.nan, np.nan]
    ocv_g = None
    qg_ah = qg_mah / 1000.0
    best = None
    for lag in np.arange(-1.0, 1.51, STEP):
        sh = int(round(lag / STEP))
        if sh > 0:
            uu, ii, qq = ug[sh:], ig[:-sh], qg_ah[sh:]
        elif sh < 0:
            uu, ii, qq = ug[:sh], ig[-sh:], qg_ah[:sh]
        else:
            uu, ii, qq = ug, ig, qg_ah
        m = ii > max(2.0, p.active_current_a)
        if m.sum() < 30 or np.std(ii[m]) < 1.0:
            continue
        X = np.column_stack([np.ones(m.sum()), ii[m], qq[m]])
        coef, *_ = np.linalg.lstsq(X, uu[m], rcond=None)
        res = uu[m] - X @ coef
        tot = np.var(uu[m])
        r2_ = 1 - np.var(res) / tot if tot > 0 else np.nan
        if np.isfinite(r2_) and (best is None or r2_ > best[0]):
            best = (r2_, coef, lag, sh)
    if best is not None:
        r2, coef, lag_best, sh = best
        u0, ri, k_v = float(coef[0]), float(-coef[1]), float(coef[2])
        if not (0 < ri < 1.0):                              # implausible (> 1 ohm for the pack)
            ri = u0 = k_v = np.nan
        else:
            # Ri during the flight (start / middle / end by drawn charge)
            if sh > 0:
                uu, ii, qq = ug[sh:], ig[:-sh], qg_ah[sh:]
            elif sh < 0:
                uu, ii, qq = ug[:sh], ig[-sh:], qg_ah[:sh]
            else:
                uu, ii, qq = ug, ig, qg_ah
            uadj = uu - k_v * qq
            qmax = qq.max()
            edges = [0, qmax / 3, 2 * qmax / 3, qmax + 1]
            for s_i in range(3):
                m = (qq >= edges[s_i]) & (qq < edges[s_i + 1]) & (ii > max(2.0, p.active_current_a))
                if m.sum() >= 25 and np.std(ii[m]) > 1.0:
                    sl, _ = np.polyfit(ii[m], uadj[m], 1)
                    if 0 < -sl < 1.0:
                        ri_seg[s_i] = float(-sl)
            # resting voltage (estimated without load) with time-aligned current, smoothed over ~10 s
            i_al = np.interp(tg - sh * STEP, tg, ig)
            ocv_g = _rolling(ug + ri * i_al, 40)

    # resting voltage at the end (model estimate)
    if ocv_g is not None:
        u_ocv_end = float(np.mean(ocv_g[-40:]))
    else:
        low = np.where(ig < p.active_current_a)[0]
        u_ocv_end = float(np.median(ug[low[-20:]])) if len(low) >= 5 else np.nan

    # --- load ---------------------------------------------------------------------
    p_max = float(np.max(_rolling(pg, 4)))
    p_mean = float(e_wh * 3600.0 / max(dur, 1))
    zeit80 = float(np.sum(ig > 0.8 * ig.max()) * STEP)
    gas_pct = None
    gas_hist = None
    if gasg is not None:
        gas_pct = np.clip((gasg + 1024.0) / 2048.0 * 100.0, 0, 100)
        gas_hist = np.histogram(gas_pct, bins=np.arange(0, 101, 10))[0] * STEP     # seconds per 10 % bin

    # --- drive: P_el = exp(a) * rpm^n -------------------------------------------------
    rpm_p90 = rpm_max = p_n = p_a = np.nan
    if rpmg is not None and np.nanmax(rpmg) > 1000:
        rs = _rolling(rpmg, 4, "median")
        ps = _rolling(pg, 4)
        rpm_max = float(np.max(rs))
        rpm_p90 = float(np.percentile(rs[rs > 1000], 90)) if np.any(rs > 1000) else np.nan
        m = (rs > 0.3 * rs.max()) & (ps > 200)
        if m.sum() > 40 and np.ptp(np.log(rs[m])) > 0.15:
            n_, a_ = np.polyfit(np.log(rs[m]), np.log(ps[m]), 1)
            if 1.0 < n_ < 6.0:
                p_n, p_a = float(n_), float(a_)

    # --- flight phases (from altitude) -----------------------------------------------------
    e_up = e_cr = e_dn = t_up = t_cr = t_dn = wh100 = alt_max = np.nan
    alt_rel = None
    if altg is not None and np.ptp(altg) > 5:
        alt_s = _rolling(altg, 8)
        alt_rel = alt_s - np.median(alt_s[:8])
        vz = np.gradient(alt_s, STEP)
        up, dn = vz > 1.0, vz < -1.0
        cr = ~(up | dn)
        e_step = pg * STEP / 3600.0
        e_up, e_dn, e_cr = float(e_step[up].sum()), float(e_step[dn].sum()), float(e_step[cr].sum())
        t_up, t_dn, t_cr = float(up.sum() * STEP), float(dn.sum() * STEP), float(cr.sum() * STEP)
        dalt = np.diff(alt_s)
        climb = float(np.sum(np.clip(dalt, 0, None)[up[1:]]))
        wh100 = e_up / climb * 100.0 if climb > 20 else np.nan
        alt_max = float(alt_rel.max())

    # --- g-forces and rotation rate --------------------------------------------------------
    g_max = g_p95 = rate_p95 = np.nan
    gg = None
    if axg is not None and ayg is not None and azg is not None:
        gg = np.sqrt(axg ** 2 + ayg ** 2 + azg ** 2)
        g_max, g_p95 = float(np.max(gg)), float(np.percentile(gg, 95))
    rateg = None
    comps = [np.abs(np.gradient(_rolling(np.degrees(np.unwrap(np.radians(a))), 3), STEP))
             for a in (rollg, pitchg) if a is not None]
    if comps:
        rateg = np.sqrt(np.sum([c ** 2 for c in comps], axis=0))      # rotation rate roll+pitch [°/s]
        rate_p95 = float(np.percentile(rateg, 95))

    # --- radio / onboard power (only while the motor is running) ----------------------------------
    def win_vals(keys, how, need_pos=False):
        vals = []
        for _, s in _numeric_cols(df, keys):
            sv = s.iloc[_orig_idx]
            if sv.notna().sum() == 0 or (need_pos and sv.max() <= 0):
                continue
            vals.append(float(sv.min() if how == "min" else sv.max()))
        return _nanmin(vals) if how == "min" else _nanmax(vals)

    # rows of the original file within the flight (work has been renumbered)
    t_all = np.asarray(_time_seconds(df), dtype=float)
    _orig_idx = np.flatnonzero((t_all >= t[0]) & (t_all <= t[-1]))

    rssi_min = win_vals(["rssi"], "min", need_pos=True)
    vfr_min = win_vals(["vfr"], "min", need_pos=True)
    rxb_min = win_vals(["rxbatt", "rx batt", "rxbat"], "min")
    rxc_max = win_vals(["rxcurrent", "rx current", "rx curr"], "max")
    txb_min = win_vals(["txbat"], "min")

    rx = rx_spike_analysis(tg - tg[0], rxig, gas_pct, alt_rel, rateg, gg, rollg, pitchg, stick_act, switch_ev)
    cnt = {c: 0 for c, _ in SPIKE_CAUSES}
    if rx:
        for sp in rx["spikes"]:
            cnt[sp["anlass"]] += 1

    esc = _first_series(df, ["esc consumption", "consumption"])
    esc_mah = np.nan
    if esc is not None:
        ev = esc.iloc[_orig_idx].dropna()
        if len(ev):
            esc_mah = float(ev.max() - ev.min())

    umin = float(np.min(_rolling(u, 5)))
    # lowest voltage in the last 10 s under load: the resting voltage after landing cannot be lower
    u_end_load = float(np.min(_rolling(u, 5)[t >= t[-1] - 10.0]))
    row = dict(
        datei=os.path.basename(path), pfad=path,
        datum=start_time if start_time is not None else _file_datetime(path),
        dauer_s=round(dur, 1),
        entnommen_mAh=round(float(q_mah[-1]), 0), ESC_mAh=round(esc_mah, 0) if np.isfinite(esc_mah) else np.nan,
        energie_Wh=round(e_wh, 2),
        I_mittel_A=round(float(np.mean(i)), 1), I_max_A=round(float(np.max(i)), 1),
        P_max_W=round(p_max, 0), P_mittel_W=round(p_mean, 0), Zeit_80_s=round(zeit80, 1),
        Gas_mittel_pct=round(float(np.mean(gas_pct)), 1) if gas_pct is not None else np.nan,
        U_start_V=round(float(np.max(u[:max(3, len(u) // 50)])), 2),
        U_ruhe_start_V=round(u_rest_start, 2) if np.isfinite(u_rest_start) else np.nan,
        U_min_V=round(umin, 2), U_last_ende_V=round(u_end_load, 2), U_ocv_ende_V=round(u_ocv_end, 2) if np.isfinite(u_ocv_end) else np.nan,
        U_ruhe_nach_V=round(u_rest_after, 2) if np.isfinite(u_rest_after) else np.nan,
        Ri_mOhm=round(ri * 1000, 1) if np.isfinite(ri) else np.nan,
        Ri_Anfang_mOhm=round(ri_seg[0] * 1000, 1) if np.isfinite(ri_seg[0]) else np.nan,
        Ri_Mitte_mOhm=round(ri_seg[1] * 1000, 1) if np.isfinite(ri_seg[1]) else np.nan,
        Ri_Ende_mOhm=round(ri_seg[2] * 1000, 1) if np.isfinite(ri_seg[2]) else np.nan,
        U0_V=round(u0, 3) if np.isfinite(u0) else np.nan, k_V_je_Ah=k_v,
        fit_R2=round(float(r2), 2) if np.isfinite(r2) else np.nan,
        versatz_s=round(float(lag_best), 2) if np.isfinite(lag_best) else np.nan,
        rpm_max=round(rpm_max, 0) if np.isfinite(rpm_max) else np.nan,
        rpm_p90=round(rpm_p90, 0) if np.isfinite(rpm_p90) else np.nan, P_n=p_n, P_a=p_a,
        E_steig_Wh=e_up, E_reise_Wh=e_cr, E_sink_Wh=e_dn, t_steig_s=t_up, t_reise_s=t_cr, t_sink_s=t_dn,
        Wh_je_100m=wh100, Hoehe_max_m=alt_max, g_max=g_max, g_p95=g_p95, Drehrate_p95=rate_p95,
        RSSI_min=rssi_min, VFR_min=vfr_min, RxBatt_min_V=rxb_min, RxStrom_max_A=rxc_max, TxBat_min_V=txb_min,
        RxStrom_mittel_A=round(rx["mean"], 2) if rx else np.nan,
        RxSpitzen_n=len(rx["spikes"]) if rx else np.nan,
        RxSp_Schalter=cnt["switch"] if rx else np.nan,
        RxSp_Manoever=cnt["manoeuvre"] if rx else np.nan,
        RxSp_StartLandung=cnt["takeoff_landing"] if rx else np.nan,
        RxSp_ohne=cnt["no_cause"] if rx else np.nan,
        RxSp_unbekannt=cnt["no_attitude"] if rx else np.nan,
        Rx_r_Drehrate=round(rx["corr"]["rate"], 2) if rx and "rate" in rx["corr"] else np.nan,
        Rx_r_Knueppel=round(rx["corr"]["stick"], 2) if rx and "stick" in rx["corr"] else np.nan,
        Knueppel_p95=round(float(np.percentile(stick_act, 95)), 0) if stick_act is not None else np.nan,
        Schalter_n=len(switch_ev),
        Rx_r_G=round(rx["corr"]["g"], 2) if rx and "g" in rx["corr"] else np.nan,
    )
    row["_series"] = dict(
        t=tg - tg[0], u=ug, i=ig, p=pg, q=qg_mah, gas=gas_pct, rpm=rpmg, alt=alt_rel, ocv=ocv_g,
        gas_hist=gas_hist, rssi=rssig, vfr=vfrg, rxi=rxig, rxu=rxug, rate=rateg, g=gg, rx=rx,
        roll=rollg, pitch=pitchg, sticks=sticks, stick=stick_act, switches=switch_ev,
    )
    return row, "ok"
