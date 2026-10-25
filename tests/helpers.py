# -*- coding: utf-8 -*-
"""Shared test data: the example logs and synthetic Ethos logs."""

import os
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))           # tests also run without "pip install -e ."
os.environ.setdefault("MPLBACKEND", "Agg")      # charts without a display

import ethosloganalyser as ela                  # noqa: E402

EXAMPLES = ROOT / "examples" / "logs"
EXAMPLE_FILES = sorted(EXAMPLES.glob("*.csv"))


@lru_cache(maxsize=None)
def example_result(nominal_mah=0.0):
    """Analysis of the example folder (cached because it takes a few seconds)."""
    return ela.analyse_folder(str(EXAMPLES), ela.Params(nominal_mah=nominal_mah))


def write_ethos_csv(folder, name, t, u, i, extra=None, start="2026-05-01 12:00:00"):
    """Writes a minimal log in Ethos format (Date/Time columns, one column per sensor)."""
    ts = pd.Timestamp(start) + pd.to_timedelta(np.asarray(t), unit="s")
    data = {"Date": ts.strftime("%Y-%m-%d"), "Time": ts.strftime("%H:%M:%S.%f").str[:-3],
            "VFAS(V)": np.round(u, 3), "Current(A)": np.round(i, 2)}
    for k, v in (extra or {}).items():
        data[k] = v
    path = Path(folder) / name
    pd.DataFrame(data).to_csv(path, index=False)
    return path


def tmpdir():
    return tempfile.mkdtemp(prefix="ela_test_")


def write_glider_log(folder, name, airborne_s, start="2026-06-01 14:00:00"):
    """Log without current sensor: altitude, vario and receiver signal only (e.g. a glider)."""
    t = np.arange(0, airborne_s + 120, 0.5)
    altitude = np.where((t > 60) & (t < 60 + airborne_s), 120.0, 0.0) + 0.3 * np.sin(t)
    times = pd.Timestamp(start) + pd.to_timedelta(t, unit="s")
    frame = pd.DataFrame({"Date": times.strftime("%Y-%m-%d"), "Time": times.strftime("%H:%M:%S.%f").str[:-3],
                          "Altitude(m)": np.round(altitude, 2), "VSpeed(m/s)": np.round(np.gradient(altitude), 2),
                          "RSSI 2.4G(dB)": 90, "RxBatt(V)": 5.1})
    path = Path(folder) / name
    frame.to_csv(path, index=False)
    return path

