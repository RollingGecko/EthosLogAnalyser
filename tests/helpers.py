# -*- coding: utf-8 -*-
"""Gemeinsame Testdaten: Beispiel-Logs und synthetische Ethos-Logs."""

import os
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))           # Tests laufen auch ohne "pip install -e ."
os.environ.setdefault("MPLBACKEND", "Agg")      # Diagramme ohne Bildschirm

import ethosloganalyser as ela                  # noqa: E402

EXAMPLES = ROOT / "examples" / "logs"
EXAMPLE_FILES = sorted(EXAMPLES.glob("*.csv"))


@lru_cache(maxsize=None)
def example_result(nominal_mah=0.0):
    """Auswertung des Beispielordners (zwischengespeichert, weil sie einige Sekunden dauert)."""
    return ela.analyse_folder(str(EXAMPLES), ela.Params(nominal_mah=nominal_mah))


def write_ethos_csv(folder, name, t, u, i, extra=None, start="2026-05-01 12:00:00"):
    """Schreibt ein minimales Log im Ethos-Format (Date/Time-Spalten, Sensoren als eigene Spalten)."""
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
