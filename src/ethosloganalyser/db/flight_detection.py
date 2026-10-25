# -*- coding: utf-8 -*-
"""Is a log a flight? Decided with the best sensor the log has.

1. Motor current: the rule of the analysis so far (motor running for at least the minimum flight duration,
   analysis/flight.py). Used when the current sensor shows the motor running at all.
2. Altitude: the aircraft is more than AIRBORNE_ALTITUDE_M above the start level for at least the minimum
   flight duration (first to last sample above it).
3. Vertical speed (vario) when there is no altitude: climbing or sinking faster than MOVING_VERTICAL_SPEED
   over at least the minimum flight duration.
4. Otherwise the radio link: receiver signal (RSSI) present for at least the minimum flight duration.
   A log without any receiver telemetry (receiver off, only transmitter values) is not a flight.

Every log is imported; logs that are not flights are only marked (and can be changed by hand later).
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from ..io.ethos_log import _to_num
from . import sensor_roles as roles_

MOTOR = "motor"
ALTITUDE = "altitude"
VERTICAL_SPEED = "vertical_speed"
RADIO_LINK = "radio_link"
NO_SENSOR = "none"

AIRBORNE_ALTITUDE_M = 15.0      # above the start level; ground logs drift by up to about 10 m
MOVING_VERTICAL_SPEED = 1.5     # m/s
MIN_SAMPLES = 20                # fewer values than this do not count as a usable sensor
SMOOTHING_SAMPLES = 5           # rolling median against single spikes of barometric sensors


@dataclass
class FlightDetection:
    """Result of the flight detection for one log."""
    is_flight: bool
    method: str                  # MOTOR, ALTITUDE, VERTICAL_SPEED, RADIO_LINK or NO_SENSOR
    duration_s: Optional[float]  # flight duration found by the method (motor running, airborne, ...)


def _usable_series(frame, columns, time_s):
    """(time, values) of every column with at least MIN_SAMPLES values, values smoothed."""
    found = []
    for column in columns:
        values = _to_num(frame[column]).to_numpy(dtype=float)
        valid = np.isfinite(values) & np.isfinite(time_s)
        if valid.sum() < MIN_SAMPLES:
            continue
        smoothed = pd.Series(values[valid]).rolling(SMOOTHING_SAMPLES, center=True, min_periods=1).median()
        found.append((time_s[valid], smoothed.to_numpy()))
    return found


def _span_s(times, active):
    """Time from the first to the last sample where active is True (0 if there is none)."""
    if not np.any(active):
        return 0.0
    hits = times[active]
    return float(hits[-1] - hits[0])


def _motor_running(frame, roles, params):
    for column in roles_.columns_with_role(roles, roles_.MOTOR_CURRENT):
        current = _to_num(frame[column]).to_numpy(dtype=float)
        if np.isfinite(current).sum() >= MIN_SAMPLES and np.nanmax(current) > params.active_current_a:
            return True
    return False


def _airborne_span_s(series):
    spans = []
    for times, altitude in series:
        start_level = float(np.median(altitude[:10]))
        spans.append(_span_s(times, altitude - start_level > AIRBORNE_ALTITUDE_M))
    return max(spans)


def _vertical_motion_span_s(series):
    return max(_span_s(times, np.abs(speed) > MOVING_VERTICAL_SPEED) for times, speed in series)


def _radio_link_span_s(series):
    return max(_span_s(times, rssi > 0) for times, rssi in series)


def detect_flight(frame, time_s, roles, motor_metrics, params):
    """Decides whether the log is a flight.

    frame: the log as read by read_log_bytes; time_s: seconds since the start (as io.ethos_log._time_seconds);
    roles: from sensor_roles.assign_roles; motor_metrics: the result of the flight analysis (dict) or None if
    the analysis found no flight; params: config.Params (min_flight_s, active_current_a).
    """
    min_flight_s = params.min_flight_s
    if _motor_running(frame, roles, params):
        if motor_metrics is None:
            return FlightDetection(False, MOTOR, None)
        return FlightDetection(True, MOTOR, float(motor_metrics["dauer_s"]))

    altitude = _usable_series(frame, roles_.columns_with_role(roles, roles_.ALTITUDE), time_s)
    if altitude:
        span = _airborne_span_s(altitude)
        return FlightDetection(span >= min_flight_s, ALTITUDE, span)

    vertical_speed = _usable_series(frame, roles_.columns_with_role(roles, roles_.VERTICAL_SPEED), time_s)
    if vertical_speed:
        span = _vertical_motion_span_s(vertical_speed)
        return FlightDetection(span >= min_flight_s, VERTICAL_SPEED, span)

    rssi = _usable_series(frame, roles_.columns_with_role(roles, roles_.RSSI), time_s)
    if rssi:
        span = _radio_link_span_s(rssi)
        return FlightDetection(span >= min_flight_s, RADIO_LINK, span)

    return FlightDetection(False, NO_SENSOR, None)
