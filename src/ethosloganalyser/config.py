# -*- coding: utf-8 -*-
"""Basic configuration: cell chemistry curves, analysis parameters, thresholds and saved settings."""

import os
import numpy as np
from dataclasses import dataclass


CHEM = {
    "LiPo": dict(
        full=4.20, rest_min=3.70, load_min=3.00,
        soc=[(3.27, 0), (3.61, 5), (3.69, 10), (3.71, 15), (3.73, 20), (3.75, 25), (3.77, 30),
             (3.79, 35), (3.80, 40), (3.82, 45), (3.84, 50), (3.85, 55), (3.87, 60), (3.91, 65),
             (3.95, 70), (3.98, 75), (4.02, 80), (4.08, 85), (4.11, 90), (4.15, 95), (4.20, 100)]),
    "LiHV": dict(
        full=4.35, rest_min=3.75, load_min=3.00,
        soc=[(3.27, 0), (3.61, 5), (3.69, 10), (3.73, 20), (3.77, 30), (3.80, 40), (3.84, 50),
             (3.87, 60), (3.95, 70), (4.02, 80), (4.10, 85), (4.18, 90), (4.27, 95), (4.35, 100)]),
    "Li-Ion": dict(
        full=4.20, rest_min=3.30, load_min=2.80,
        soc=[(3.00, 0), (3.30, 10), (3.40, 20), (3.50, 30), (3.60, 40), (3.70, 50), (3.80, 60),
             (3.90, 70), (4.00, 80), (4.10, 90), (4.20, 100)]),
}


SOC_TOL_PCT = 15.0      # allowed deviation of state of charge, voltage <-> coulomb counting [percentage points]


# colours and (user-facing) labels of the causes of receiver current spikes
SPIKE_CAUSES = [("Schalter", "tab:green"), ("Manöver", "tab:orange"), ("Start/Landung", "tab:blue"),
                ("ohne erkennbaren Anlass", "black"), ("keine Lagedaten", "grey")]


SPIKE_COLS = ["RxSp_Schalter", "RxSp_Manoever", "RxSp_StartLandung", "RxSp_ohne", "RxSp_unbekannt"]


SPIKE_COLOR = dict(SPIKE_CAUSES)


def soc_pct(v_cell, chem):
    pts = CHEM[chem]["soc"]
    return np.interp(v_cell, [a for a, _ in pts], [b for _, b in pts])


@dataclass
class Params:
    cells: int = 0                 # cell count; 0 = automatic from start voltage
    chem: str = "LiPo"             # LiPo / LiHV / Li-Ion
    nominal_mah: float = 0.0       # nominal capacity (0 = unknown)
    min_flight_s: float = 120.0    # minimum flight duration (motor running)
    active_current_a: float = 1.0  # current above which the motor counts as "running"
    reserve_pct: float = 20.0      # desired remaining charge at landing (for the timer)
    col_voltage: str = ""          # optional: column name (substring), empty = automatic
    col_current: str = ""


STEP = 0.25   # time series grid in s


SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".akku_analyse.json")


def load_settings():
    import json
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_settings(d):
    import json
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1)
    except Exception:
        pass
