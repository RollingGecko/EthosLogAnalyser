# -*- coding: utf-8 -*-
"""Flights from the flight database for the single-flight page (no Tkinter here).

The charts and details of a single flight (plots/flight.py, report/text.py) and the statistics need an analysis
result of the whole aircraft: cell count, state of charge, timer and the comparison with the other flights come
from all flights of that aircraft. prepare_aircraft() reads the per-flight analysis of every flight of an aircraft
as stored in the database (db/flight_preparation.py) - quick, but still done in the background; aircraft_result()
then adds the cross-flight part (analysis/fleet.analyse_flights) in a fraction of a second, e.g. after the battery
settings have changed. complete_flight() adds the time series only the single-flight charts draw.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np

from ..analysis.fleet import analyse_flights
from ..db import flight_preparation, flight_store, sensor_roles
from ..db.flight_preparation import PATH_PREFIX, flight_path  # noqa: F401 (part of this module's interface)
from ..i18n import fmt_datetime
from ..plots.flight import FLIGHT_VIEWS
from ..utils import _mmss


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


def prepare_aircraft(connection, aircraft, progress=None, should_cancel=None):
    """The per-flight analysis of every flight of an aircraft that has metrics: {log_id: (row, series)}.

    The values are read as stored with the flight (db/flight_preparation.py); the series then hold what the
    statistics need (complete_flight adds the rest for the single flight). A flight whose stored values are missing
    or outdated (e.g. while they are worked out after an update) is analysed from its stored time series instead,
    so the result is always complete and current. progress(done, total) is called after such an analysis and at
    the end; should_cancel() is checked before every flight.
    """
    flights = flight_preparation.flights_of_aircraft(connection, aircraft)
    prepared = {}
    for done, flight in enumerate(flights, start=1):
        if should_cancel is not None and should_cancel():
            return None
        if flight.is_current:
            analysed = flight.prepared()
        else:
            analysed = flight_preparation.analyse_stored_flight(
                flight_store.load_log_frame(connection, flight.log_id), flight.log_id, flight.file_name,
                flight.start_time, flight.analysis_params_text)
        if analysed is not None:
            prepared[flight.log_id] = analysed
        if progress is not None and (not flight.is_current or done == len(flights)):
            progress(done, len(flights))
    return prepared


def complete_flight(connection, log_id):
    """(row, series) of one flight with all time series, as the single-flight charts need them; None without a
    result. Takes a few hundredths of a second (one analysis of the stored time series)."""
    file_name, start_text, params_text = connection.execute(
        "SELECT log_file.original_name, flight.start_time, flight.analysis_params FROM flight "
        "JOIN log_file ON log_file.id = flight.log_id WHERE flight.log_id = ?", (log_id,)).fetchone()
    return flight_preparation.analyse_stored_flight(flight_store.load_log_frame(connection, log_id), log_id,
                                                    file_name, flight_store.parse_start_time(start_text),
                                                    params_text)


def aircraft_result(prepared, params, aircraft, log_ids=None):
    """Analysis result of the prepared flights of an aircraft: all of them, or only those in log_ids (e.g. the
    flights that pass the filter of the statistics). The cross-flight part (cell count, trends, flight numbers
    1, 2, ...) covers exactly these flights."""
    chosen = prepared.values() if log_ids is None else [prepared[log_id] for log_id in log_ids if log_id in prepared]
    rows = [dict(row) for row, _series in chosen]
    series = {row["pfad"]: flight_series for row, flight_series in chosen}
    meta = {"model": aircraft, "models": {aircraft: len(rows)}}
    return analyse_flights(rows, series, params, meta)
