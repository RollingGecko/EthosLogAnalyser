# -*- coding: utf-8 -*-
"""Feasibility report: estimated receiver current per control surface for all flights in a folder.

Development tool (no user interface). The values are ESTIMATES from the total receiver current; see
docs/methodology.md, "Receiver current per control surface".

Usage:
    python scripts/rx_surface_report.py <log folder> [--csv out.csv] [--cells N --chem Li-Ion --mah 9000]
                                        [--channel aileron=QR --channel elevator=HR ...]
"""

import argparse
import glob
import os
import sys
import warnings

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from ethosloganalyser.analysis.flight import analyse_file          # noqa: E402
from ethosloganalyser.analysis.rx_surfaces import SURFACES, surface_current_analysis, surface_trend  # noqa: E402
from ethosloganalyser.config import Params                          # noqa: E402

SHORT = {"aileron": "ail", "elevator": "ele", "rudder": "rud"}


def analyse(folder, params):
    rows = []
    for path in sorted(glob.glob(os.path.join(folder, "**", "*.csv"), recursive=True)):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r, _ = analyse_file(path, params)
        if r is None:
            continue
        s = r["_series"]
        spikes = [sp["t"] for sp in (s["rx"]["spikes"] if s["rx"] else [])]
        res = surface_current_analysis(s["t"], s["rxi"], s["sticks"], s["alt"], spikes)
        if res is None:
            continue
        row = dict(file=r["datei"], date=r["datum"], duration_s=r["dauer_s"], rx_mean_a=r["RxStrom_mittel_A"],
                   rx_max_a=r["RxStrom_max_A"], lag_s=res["lag_s"], r2=round(res["r2"], 2),
                   base_a=round(res["base_a"], 2), base_lo=round(res["base_lo"], 2),
                   base_hi=round(res["base_hi"], 2), spikes=len(res["spikes"]),
                   combined_n=len(res["combined"]),
                   combined_peak_a=round(max((c["peak_a"] for c in res["combined"]), default=np.nan), 2))
        for (a, b), c in res["coupling"].items():
            row[f"r_{SHORT[a]}_{SHORT[b]}"] = round(c, 2)
        for k in SURFACES:
            v = res["surfaces"][k]
            p = SHORT[k]
            row.update({f"{p}_status": v["status"], f"{p}_per100": round(v["per100"], 2),
                        f"{p}_per100_lo": round(v["per100_lo"], 2), f"{p}_per100_hi": round(v["per100_hi"], 2),
                        f"{p}_speed": round(v["speed"], 2), f"{p}_share": round(v["share"], 2),
                        f"{p}_active_s": round(v["active_s"]), f"{p}_clean": v["clean_events"],
                        f"{p}_spikes": round(res["spike_share"].get(k, np.nan), 2)})
        row["several_spikes"] = round(res["spike_share"].get("several", np.nan), 2)
        row["none_spikes"] = round(res["spike_share"].get("none", np.nan), 2)
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder")
    ap.add_argument("--csv")
    ap.add_argument("--cells", type=int, default=0)
    ap.add_argument("--chem", default="LiPo")
    ap.add_argument("--mah", type=float, default=0.0)
    ap.add_argument("--channel", action="append", default=[], help="code=column, e.g. aileron=QR")
    a = ap.parse_args()
    channels = dict(c.split("=", 1) for c in a.channel)
    df = analyse(a.folder, Params(cells=a.cells, chem=a.chem, nominal_mah=a.mah, channels=channels))
    if df.empty:
        print("no flights with receiver current and stick channels")
        return
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 60)
    cols = ["date", "lag_s", "r2", "base_a", "combined_n", "combined_peak_a", "r_ail_ele", "r_ail_rud", "r_ele_rud"]
    for k in SURFACES:
        p = SHORT[k]
        cols += [f"{p}_clean", f"{p}_per100", f"{p}_per100_lo", f"{p}_per100_hi", f"{p}_spikes"]
    print(df[[c for c in cols if c in df.columns]].to_string(index=False))
    x = np.arange(len(df))
    series = [(k, SHORT[k] + "_per100", "A per 100 %") for k in SURFACES] + [("base current", "base_a", "A")]
    for name, col, unit in series:
        lo, hi = (col + "_lo", col + "_hi") if col != "base_a" else ("base_lo", "base_hi")
        tr = surface_trend(x, df[col], df[lo], df[hi])
        if tr:
            print(f"{name}: {tr['start']:.2f} -> {tr['end']:.2f} {unit}, slope {tr['slope'] * 10:+.3f} per 10 flights "
                  f"(90 %: {tr['slope_lo'] * 10:+.3f} .. {tr['slope_hi'] * 10:+.3f}), "
                  f"{'rising' if tr['rising'] else 'falling' if tr['falling'] else 'no confirmed change'}")
    comb = df["combined_peak_a"].dropna()
    if len(comb):
        print(f"combined full-deflection manoeuvres: {int(df['combined_n'].sum())} in {len(comb)} flights, "
              f"peak receiver current {comb.min():.2f}-{comb.max():.2f} A (median {comb.median():.2f} A)")
    if a.csv:
        df.to_csv(a.csv, index=False)


if __name__ == "__main__":
    main()
