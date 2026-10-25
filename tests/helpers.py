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


def read_log(path):
    """An Ethos log file read as the import reads it."""
    from ethosloganalyser.io.ethos_log import read_log_bytes
    return read_log_bytes(Path(path).read_bytes())


def analyse_log(path, p):
    """Per-flight analysis of one log file: (row, "ok") or (None, Msg with the reason)."""
    from ethosloganalyser.analysis.flight import analyse_frame
    from ethosloganalyser.io.ethos_log import read_log_bytes
    return analyse_frame(read_log_bytes(Path(path).read_bytes()), str(path), p)


def analyse_logs(paths, p, model=None):
    """Cross-flight analysis straight from log files, as a reference for the flight database: every file is
    analysed, the flights of one model (default: the model of the first file) are combined."""
    from ethosloganalyser.io.ethos_log import model_from_filename
    paths = sorted(str(path) for path in paths)
    model = model if model is not None else (model_from_filename(paths[0]) if paths else None)
    rows, series = [], {}
    for path in paths:
        if model_from_filename(path) != model:
            continue
        row, _reason = analyse_log(path, p)
        if row is not None:
            series[row["pfad"]] = row.pop("_series")
            rows.append(row)
    return ela.analyse_flights(rows, series, p, {"model": model})


def analyse_folder_logs(folder, p, model=None):
    """analyse_logs for all CSV files of a folder and its subfolders."""
    return analyse_logs(sorted(Path(folder).rglob("*.csv")), p, model)


@lru_cache(maxsize=None)
def example_result(nominal_mah=0.0):
    """Analysis of the example logs (cached because it takes a few seconds)."""
    return analyse_logs(EXAMPLE_FILES, ela.Params(nominal_mah=nominal_mah))


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

