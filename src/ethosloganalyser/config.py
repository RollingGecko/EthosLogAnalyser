# -*- coding: utf-8 -*-
"""Basic configuration: cell chemistry curves, analysis parameters, thresholds and saved settings."""

import os
import sys
import numpy as np
from dataclasses import dataclass

from .i18n import N_, tr


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


# causes of receiver current spikes: language-neutral code and colour; user-facing labels in SPIKE_LABELS
SPIKE_CAUSES = [("switch", "tab:green"), ("manoeuvre", "tab:orange"), ("takeoff_landing", "tab:blue"),
                ("no_cause", "black"), ("no_attitude", "grey")]


SPIKE_LABELS = {
    "switch": N_("Schalter"),
    "manoeuvre": N_("Manöver"),
    "takeoff_landing": N_("Start/Landung"),
    "no_cause": N_("ohne erkennbaren Anlass"),
    "no_attitude": N_("keine Lagedaten"),
}


SPIKE_COLS = ["RxSp_Schalter", "RxSp_Manoever", "RxSp_StartLandung", "RxSp_ohne", "RxSp_unbekannt"]


SPIKE_COLOR = dict(SPIKE_CAUSES)


# signals that are correlated with the receiver current (keys of rx["corr"])
CORR_LABELS = {"stick": N_("Knüppelaktivität"), "rate": N_("Drehrate"), "g": N_("G-Last"), "gas": N_("Gas")}


# stick channels (keys of series["sticks"])
STICK_LABELS = {"aileron": N_("Querruder"), "elevator": N_("Höhenruder"), "rudder": N_("Seitenruder")}


# where the resting voltage at the end of a flight comes from (column U_ende_Quelle)
VOLTAGE_SOURCE_LABELS = {"measured": N_("gemessen"), "estimated": N_("geschätzt"), "": "–"}


# which capacity the state of charge is based on (meta["cap_src"])
CAP_SOURCE_LABELS = {"nominal": N_("Nennkapazität"), "estimated": N_("geschätzte Kapazität")}


# name shown for logs whose file name has no model part (io.ethos_log.UNKNOWN_MODEL)
MODEL_UNKNOWN_LABEL = N_("(unbekannt)")


def model_label(model):
    """User-facing name of a model (file-name model, see io.ethos_log.model_from_filename)."""
    return model if model else tr(MODEL_UNKNOWN_LABEL)


def label(table, code):
    """User-facing label of a code from one of the label tables, in the current language."""
    return tr(table[code]) if table.get(code) else str(code)


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
    date_from: str = ""            # optional period filter (YYYY-MM-DD, inclusive); empty = open
    date_to: str = ""


STEP = 0.25   # time series grid in s


SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".akku_analyse.json")

# flight database: Documents\EthosLogAnalyser\flugbuch.db unless another one was opened (setting "database")
DATABASE_FOLDER_NAME = "EthosLogAnalyser"
DATABASE_FILE_NAME = "flugbuch.db"
DEFAULT_DATABASE_FILE = None          # tests set a path here instead of the real Documents folder


def documents_folder():
    """The user's Documents folder (on Windows also when it has been moved, e.g. into OneDrive)."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes
            from uuid import UUID

            class GUID(ctypes.Structure):
                _fields_ = [("data", ctypes.c_byte * 16)]

            documents_id = GUID()
            documents_id.data[:] = UUID("FDD39AD0-238F-46AF-ADB4-6C85480369C7").bytes_le   # FOLDERID_Documents
            path_pointer = wintypes.LPWSTR()
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(documents_id), 0, None,
                                                          ctypes.byref(path_pointer)) == 0:
                path = path_pointer.value
                ctypes.windll.ole32.CoTaskMemFree(path_pointer)
                return path
        except Exception:
            pass
    return os.path.join(os.path.expanduser("~"), "Documents")


def default_database_path():
    """Where the flight database is created when none has been opened yet."""
    if DEFAULT_DATABASE_FILE:
        return DEFAULT_DATABASE_FILE
    return os.path.join(documents_folder(), DATABASE_FOLDER_NAME, DATABASE_FILE_NAME)


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
