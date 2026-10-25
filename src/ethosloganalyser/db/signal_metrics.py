# -*- coding: utf-8 -*-
"""Values worked out from the stored time series of a log, for every log - also for aircraft without battery
or motor data (the per-flight metrics of analysis/flight.py exist only for logs with battery voltage and
current).

They are the basis of the anomaly rules that look at what happens *within* a flight (analysis/anomalies.py),
so a recalculation of the anomalies never has to read time series or raw logs again.

Stored as JSON in ``flight.signal_metrics``:

  rx_voltage_median_V    median receiver voltage over the log (of the receiver battery input with the largest dip)
  rx_voltage_min_V       lowest receiver voltage of all receiver battery inputs, smoothed over about 1 s
  rx_voltage_dip_pct     largest drop of a receiver battery input below its own median [% of the median]
  rx_voltage_dip_time_s  time of that lowest value, seconds since the start of the log

Keys are missing when the log has no such sensor. Smoothing with a rolling median over about one second keeps
a single wrong sample from counting as a dip; a real voltage dip of the receiver supply lasts longer.
"""

import json

import numpy as np
import pandas as pd

from ..io.ethos_log import _to_num
from . import sensor_roles

SMOOTHING_WINDOW_S = 1.0
MIN_SAMPLES = 20                 # fewer values do not count as a usable sensor
MIN_RECEIVER_VOLTAGE_V = 1.0     # a receiver battery input with a lower median is not connected


def _smoothed(values, time_s):
    """Rolling median over about SMOOTHING_WINDOW_S seconds."""
    step = float(np.median(np.diff(time_s))) if len(time_s) > 1 else 0.0
    samples = max(1, int(round(SMOOTHING_WINDOW_S / step))) if step > 0 else 1
    return pd.Series(values).rolling(samples, center=True, min_periods=1).median().to_numpy()


def receiver_voltage_values(time_s, columns):
    """The receiver voltage values of a log: dict with the keys described in the module docstring, or {}.

    time_s: seconds since the start (array); columns: {column name: values} of the receiver battery inputs.
    """
    best = None
    lowest = np.inf
    for values in columns.values():
        values = np.asarray(values, dtype=float)
        valid = np.isfinite(values) & np.isfinite(time_s)
        if valid.sum() < MIN_SAMPLES:
            continue
        times, measured = time_s[valid], values[valid]
        median = float(np.median(measured))
        if median < MIN_RECEIVER_VOLTAGE_V:
            continue
        smoothed = _smoothed(measured, times)
        position = int(np.argmin(smoothed))
        lowest = min(lowest, float(smoothed[position]))
        dip_pct = (median - float(smoothed[position])) / median * 100.0
        if best is None or dip_pct > best[0]:
            best = (dip_pct, median, float(times[position]))
    if best is None:
        return {}
    dip_pct, median, dip_time = best
    return {"rx_voltage_median_V": round(median, 3), "rx_voltage_min_V": round(lowest, 3),
            "rx_voltage_dip_pct": round(max(dip_pct, 0.0), 2), "rx_voltage_dip_time_s": round(dip_time, 1)}


def signal_metrics(time_s, frame, roles):
    """All signal metrics of a log.

    time_s: seconds since the start; frame: DataFrame with the numeric sensor columns (as read from the log or
    from the stored series); roles: {column name: role}.
    """
    time_s = np.asarray(time_s, dtype=float)
    receiver = {column: _to_num(frame[column]).to_numpy(dtype=float)
                for column in sensor_roles.columns_with_role(roles, sensor_roles.RX_VOLTAGE) if column in frame}
    return receiver_voltage_values(time_s, receiver)


def signal_metrics_to_json(values):
    """Signal metrics -> compact JSON text ("{}" when the log has none, so it is not worked out again)."""
    return json.dumps(values, separators=(",", ":"), sort_keys=True)
