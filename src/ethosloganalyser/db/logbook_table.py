# -*- coding: utf-8 -*-
"""The flight table of the logbook, built from the flights stored in the database.

One row per stored log (flights and logs that are not flights). The columns use the names of the flight
table of the analysis where there is one, so ``analysis.logbook.logbook`` can total them:

  Flug             number of the flight within its aircraft (1, 2, ... by start time; empty for non-flights)
  datum            start of the log (from the file name)
  dauer_s          flight duration [s] as stored (motor running time for aircraft with a motor)
  entnommen_mAh    drawn charge from the stored metrics (empty where the log has no battery data)
  Akku_gueltig     the battery values of the flight are usable (no stuck current sensor, no voltage dropout)

and, new, ``log_id``, ``aircraft``, ``file_name``, ``is_flight`` (the decision that counts), ``auto_flight``
(the automatic detection) and ``possible_duplicate``.

Nothing here reads time series, so the table is built in a few milliseconds even for many flights.
"""

import json

import numpy as np
import pandas as pd

from ..analysis.quality import BATTERY_INVALID, cell_count, detect_data_errors
from ..config import CHEM

# values of the stored per-flight metrics that the logbook needs
METRIC_KEYS = ("entnommen_mAh", "I_mittel_A", "I_max_A", "U_min_V", "U_ruhe_start_V", "U_start_V")

# columns of the logbook flight table, in this order
TABLE_COLUMNS = ["log_id", "aircraft", "file_name", "datum", "Flug", "dauer_s", "entnommen_mAh", "Akku_gueltig",
                 "is_flight", "auto_flight", "possible_duplicate"]


def metric_columns(metrics_texts):
    """The needed metrics of every flight as columns: (DataFrame with METRIC_KEYS, boolean array "has metrics").

    metrics_texts: the stored JSON text per flight (None or NaN for a flight without metrics, as pandas reads
    a missing text). Missing values are NaN.
    """
    values = {key: np.full(len(metrics_texts), np.nan) for key in METRIC_KEYS}
    has_metrics = np.zeros(len(metrics_texts), dtype=bool)
    for position, text in enumerate(metrics_texts):
        if not isinstance(text, str):
            continue
        has_metrics[position] = True
        stored = json.loads(text)
        for key in METRIC_KEYS:
            value = stored.get(key)
            if value is not None:
                values[key][position] = value
    return pd.DataFrame(values), has_metrics


def battery_valid(metrics, params):
    """Which flights have usable battery values: boolean array in the order of ``metrics``.

    Same rule as the folder analysis (analysis/fleet.py, analysis/quality.py): a flight with a stuck current
    sensor or a voltage dropout does not count for battery values. The number of cells is the configured one,
    or - if none is configured - estimated from the highest start voltage of the given flights.
    """
    chemistry = CHEM[params.chem]
    highest_start_voltage = metrics["U_ruhe_start_V"].fillna(metrics["U_start_V"]).max()
    cells = cell_count(params.cells, highest_start_voltage, chemistry)
    lowest_cell_voltage = (metrics["U_min_V"] / cells).round(3) if cells > 0 else np.nan
    flight_table = pd.DataFrame({"I_mittel_A": metrics["I_mittel_A"], "I_max_A": metrics["I_max_A"],
                                 "U_min_Zelle_V": lowest_cell_voltage})
    errors = detect_data_errors(flight_table, chemistry)
    invalid = np.zeros(len(metrics), dtype=bool)
    for code in BATTERY_INVALID:
        invalid |= errors[code]
    return ~invalid


def _effective_flight(rows):
    """Boolean Series: the decision that counts - by hand if there is one, otherwise the automatic detection."""
    manual = pd.to_numeric(rows["is_flight_manual"], errors="coerce")
    return manual.where(manual.notna(), rows["is_flight"]).astype(int).astype(bool)


def manual_value_after_switch(is_flight, auto_flight):
    """New value of ``flight.is_flight_manual`` when the user switches a log between flight and no flight.

    ``None`` (no manual decision) if the new state equals the automatic detection, so switching twice
    gives back the automatic result.
    """
    new_state = not is_flight
    return None if new_state == bool(auto_flight) else int(new_state)


def empty_logbook_table():
    """The logbook table of a database without logs (the columns exist, the date column has its type)."""
    table = pd.DataFrame({column: pd.Series(dtype=object) for column in TABLE_COLUMNS})
    table["datum"] = pd.to_datetime(table["datum"])
    return table


def _flight_numbers(table):
    """Number of every flight within its aircraft (1, 2, ... in the order of the table); empty for non-flights."""
    numbers = pd.Series(pd.NA, index=table.index, dtype="Int64")
    flights = table[table["is_flight"]]
    numbers.loc[flights.index] = (flights.groupby("aircraft").cumcount() + 1).to_numpy()
    return numbers


def _battery_valid_per_aircraft(table, metrics, params_for):
    """Battery validity of every flight with metrics, judged with the battery settings of its aircraft."""
    valid = pd.Series(False, index=table.index)
    usable = table[table["is_flight"] & table["has_metrics"]]
    for aircraft, flights in usable.groupby("aircraft"):
        valid.loc[flights.index] = battery_valid(metrics.loc[flights.index], params_for(aircraft))
    return valid


def build_logbook_table(rows, params_for):
    """The logbook flight table from the rows of ``flight_store.logbook_rows``, oldest first.

    params_for(aircraft name) gives the analysis settings (battery) of that aircraft.
    """
    if rows.empty:
        return empty_logbook_table()
    rows = rows.sort_values(["start_time", "original_name"], kind="stable").reset_index(drop=True)
    metrics, has_metrics = metric_columns(list(rows["metrics"]))
    duration = pd.to_numeric(rows["duration_s"], errors="coerce")
    table = pd.DataFrame({
        "log_id": rows["log_id"].to_numpy(),
        "aircraft": rows["aircraft"].to_numpy(),
        "file_name": rows["original_name"].to_numpy(),
        "datum": pd.to_datetime(rows["start_time"]).to_numpy(),
        # a log without a detected duration (not a flight, no motor) shows the length of the whole log
        "dauer_s": duration.fillna(pd.to_numeric(rows["log_duration_s"], errors="coerce")).to_numpy(),
        "entnommen_mAh": metrics["entnommen_mAh"].to_numpy(),
        "is_flight": _effective_flight(rows).to_numpy(),
        "auto_flight": rows["is_flight"].astype(bool).to_numpy(),
        "possible_duplicate": rows["possible_duplicate"].astype(bool).to_numpy(),
        "has_metrics": has_metrics,
    })
    table["Flug"] = _flight_numbers(table)
    table["Akku_gueltig"] = _battery_valid_per_aircraft(table, metrics, params_for)
    return table[TABLE_COLUMNS]
