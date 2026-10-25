# -*- coding: utf-8 -*-
"""Flights from the flight database for the single-flight page (no Tkinter here).

The charts and details of a single flight (plots/flight.py, report/text.py) need an analysis result of the
whole aircraft: cell count, state of charge, timer and the comparison with the other flights come from all
flights of that aircraft. prepare_aircraft() analyses the stored time series of every flight of an aircraft
(analysis/flight.py) - this takes a few seconds and runs in the background; aircraft_result() then adds the
cross-flight part (analysis/fleet.analyse_flights) in a fraction of a second, e.g. after the battery settings
have changed.
"""

import dataclasses
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np

from ..analysis.fleet import analyse_flights
from ..analysis.flight import analyse_frame
from ..db import flight_store, sensor_roles
from ..i18n import fmt_datetime
from ..plots.flight import FLIGHT_VIEWS
from ..utils import _mmss

# "pfad" of a database flight inside an analysis result: there is no file, the key names the stored log
PATH_PREFIX = "db:"

# sensor roles of which at least one must be in a log for a view of the single flight to show something
# (the views draw these signals, plots/flight.py)
VIEW_ROLES = {
    "battery": (sensor_roles.BATTERY_VOLTAGE, sensor_roles.MOTOR_CURRENT),
    "reception": (sensor_roles.RSSI, sensor_roles.LINK_QUALITY, sensor_roles.ALTITUDE),
    "rx_current": (sensor_roles.RX_CURRENT, sensor_roles.RX_VOLTAGE, sensor_roles.THROTTLE,
                   sensor_roles.STICK_AILERON, sensor_roles.STICK_ELEVATOR, sensor_roles.STICK_RUDDER),
    "attitude": (sensor_roles.ROLL_ANGLE, sensor_roles.PITCH_ANGLE, sensor_roles.THROTTLE,
                 sensor_roles.STICK_AILERON, sensor_roles.STICK_ELEVATOR, sensor_roles.STICK_RUDDER,
                 sensor_roles.ACCELERATION_X, sensor_roles.ACCELERATION_Y, sensor_roles.ACCELERATION_Z,
                 sensor_roles.ALTITUDE),
}


@dataclass
class StoredFlight:
    """A flight of the database as listed in the flight selector."""
    log_id: int
    aircraft: str
    start_time: datetime
    duration_s: Optional[float]
    drawn_mah: Optional[float]
    has_metrics: bool             # False: the analysis found no battery/motor data (e.g. a glider)
    file_name: str


def flight_path(log_id):
    """The "pfad" of a database flight in an analysis result."""
    return f"{PATH_PREFIX}{log_id}"


def stored_flights(connection):
    """All logs marked as flight (by the detection or by hand), oldest first."""
    rows = connection.execute(
        "SELECT flight.log_id, aircraft.name, flight.start_time, flight.duration_s, flight.metrics, "
        "log_file.original_name FROM flight JOIN aircraft ON aircraft.id = flight.aircraft_id "
        "JOIN log_file ON log_file.id = flight.log_id "
        "WHERE coalesce(flight.is_flight_manual, flight.is_flight) = 1 "
        "ORDER BY flight.start_time, log_file.original_name").fetchall()
    flights = []
    for log_id, aircraft, start, duration, metrics, file_name in rows:
        drawn = json.loads(metrics).get("entnommen_mAh") if metrics else None
        flights.append(StoredFlight(log_id=log_id, aircraft=aircraft, start_time=flight_store.parse_start_time(start),
                                    duration_s=duration, drawn_mah=drawn, has_metrics=metrics is not None,
                                    file_name=file_name))
    return flights


def flight_choice_label(flight, aircraft_label):
    """Entry of the flight selector: date and time, aircraft, duration, drawn charge."""
    parts = [fmt_datetime(flight.start_time), aircraft_label]
    if flight.duration_s is not None and np.isfinite(flight.duration_s):
        parts.append(_mmss(flight.duration_s))
    if flight.drawn_mah is not None:
        parts.append(f"{flight.drawn_mah:.0f} mAh")
    return " | ".join(parts)


def available_views(roles):
    """Views of the single flight for which the log has data ({column: role} from sensor_roles_of)."""
    present = set(roles.values())
    return [view for view in FLIGHT_VIEWS if present.intersection(VIEW_ROLES[view])]


def _analyse_stored_flight(connection, log_id, file_name, start_text, stored_params, base_params):
    """Per-flight analysis of a stored flight from its time series: (row, series) or None without metrics."""
    params = dataclasses.replace(base_params, **json.loads(stored_params))
    frame = flight_store.load_log_frame(connection, log_id)
    row, _reason = analyse_frame(frame, file_name, params, start_time=flight_store.parse_start_time(start_text))
    if row is None:
        return None
    series = row.pop("_series")
    row["datei"] = file_name
    row["pfad"] = flight_path(log_id)
    return row, series


def prepare_aircraft(connection, aircraft, base_params, progress=None, should_cancel=None):
    """Analyses every flight of an aircraft that has metrics: {log_id: (row, series)}.

    base_params gives the settings not stored with a flight; the per-flight settings are the ones used at
    import (flight.analysis_params), so the result matches the stored metrics.
    """
    rows = connection.execute(
        "SELECT flight.log_id, log_file.original_name, flight.start_time, flight.analysis_params FROM flight "
        "JOIN aircraft ON aircraft.id = flight.aircraft_id JOIN log_file ON log_file.id = flight.log_id "
        "WHERE aircraft.name = ? AND coalesce(flight.is_flight_manual, flight.is_flight) = 1 "
        "AND flight.metrics IS NOT NULL ORDER BY flight.start_time", (aircraft,)).fetchall()
    prepared = {}
    for done, (log_id, file_name, start_text, stored_params) in enumerate(rows, start=1):
        if should_cancel is not None and should_cancel():
            return None
        analysed = _analyse_stored_flight(connection, log_id, file_name, start_text, stored_params, base_params)
        if analysed is not None:
            prepared[log_id] = analysed
        if progress is not None:
            progress(done, len(rows))
    return prepared


def aircraft_result(prepared, params, aircraft, log_ids=None):
    """Analysis result of the prepared flights of an aircraft: all of them, or only those in log_ids (e.g. the
    flights that pass the filter of the statistics). The cross-flight part (cell count, trends, flight numbers
    1, 2, ...) covers exactly these flights, as the folder analysis did for a period."""
    chosen = prepared.values() if log_ids is None else [prepared[log_id] for log_id in log_ids if log_id in prepared]
    rows = [dict(row) for row, _series in chosen]
    series = {row["pfad"]: flight_series for row, flight_series in chosen}
    meta = {"model": aircraft, "models": {aircraft: len(rows)}}
    return analyse_flights(rows, series, params, meta)
