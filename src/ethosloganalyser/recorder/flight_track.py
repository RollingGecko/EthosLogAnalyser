# -*- coding: utf-8 -*-
"""The time series of one log as the flight recorder plays it back.

There is no interpolation between log rows: at a time t the last row with a time <= t holds ("last value holds
until the next row", found with ``numpy.searchsorted``). Ethos writes sensors into rows of their own, so every
column is filled on its own: a row without a value (NaN) takes over the last valid value of that column. How old
that value is (``FlightTrack.age``) tells the instruments when to show that a sensor has gone quiet.

Each instrument reads the first column of its sensor role (``db/sensor_roles.py``, stored per column), like the
analysis; for the RPM a column named "ESC RPM" is preferred. Only the columns of these roles and of the telemetry
roles are read from the database.

The flight ends with the last log row that still has telemetry (any sensor of the aircraft; sticks, switches and
the transmitter battery are logged by the transmitter and do not count). Some logs run on for minutes after the
landing without telemetry; the recorder does not show that part. A log without any telemetry ends with its last
row.
"""

from dataclasses import dataclass, field

import numpy as np

from ..db import sensor_roles as roles
from ..db.series_codec import decode_series

STALE_AFTER_S = 2.0                 # a value older than this is shown as "no data" (about 7 log rows)
RELATIVE_ALTITUDE_START_VALUES = 8  # the altitude is relative to the median of its first values, as in the charts

# roles the recorder shows (the instruments of later packages read them from the same track)
TRACK_ROLES = (roles.ROLL_ANGLE, roles.PITCH_ANGLE, roles.ALTITUDE, roles.VERTICAL_SPEED, roles.RPM,
               roles.THROTTLE, roles.BATTERY_VOLTAGE, roles.MOTOR_CURRENT, roles.STICK_AILERON,
               roles.STICK_ELEVATOR, roles.STICK_RUDDER)

# roles that are no telemetry: they are logged by the transmitter, also when the aircraft is switched off
NOT_TELEMETRY_ROLES = frozenset({roles.TIME, roles.STICK_AILERON, roles.STICK_ELEVATOR, roles.STICK_RUDDER,
                                 roles.THROTTLE, roles.SWITCH, roles.TX_VOLTAGE})

# name parts that make a column the preferred one of its role (otherwise the first column in log order wins)
PREFERRED_COLUMN_NAMES = {roles.RPM: ("esc rpm",)}

# Sign convention of the attitude sensor (R.angle / P.angle). Provisional until ticket TW-053 has checked it with
# a known manoeuvre: in the Viper-Jet logs a positive P.angle goes with losing height, i.e. nose down; a positive
# R.angle is taken as right wing down. This is the only place that knows the convention.
LOG_PITCH_POSITIVE_IS_NOSE_DOWN = True
LOG_ROLL_POSITIVE_IS_RIGHT_WING_DOWN = True


def displayed_attitude(log_roll, log_pitch):
    """Attitude as the instruments show it, from the values of the log: (bank, pitch) in degrees with bank > 0 =
    right wing down and pitch > 0 = nose up (the usual cockpit convention)."""
    bank = log_roll if LOG_ROLL_POSITIVE_IS_RIGHT_WING_DOWN else -log_roll
    pitch = -log_pitch if LOG_PITCH_POSITIVE_IS_NOSE_DOWN else log_pitch
    return bank, pitch


def choose_column(column_roles, role):
    """The column that stands for a role: a preferred name if there is one, else the first column in log order;
    None if the log has no column of that role. column_roles: [(column name, role)] in log order."""
    candidates = [column for column, column_role in column_roles if column_role == role]
    for name_part in PREFERRED_COLUMN_NAMES.get(role, ()):
        for column in candidates:
            if name_part in str(column).lower():
                return column
    return candidates[0] if candidates else None


def last_valid_index(values):
    """For every row the index of the last row with a valid (finite) value, -1 before the first one."""
    rows = np.arange(len(values))
    marked = np.where(np.isfinite(values), rows, -1)
    return np.maximum.accumulate(marked) if len(values) else marked


def held_values(values):
    """The values with every missing one replaced by the last valid value before it (NaN before the first)."""
    values = np.asarray(values, dtype=float)
    source = last_valid_index(values)
    held = values[np.maximum(source, 0)] if len(values) else values.copy()
    return np.where(source >= 0, held, np.nan)


def relative_altitude(values):
    """Altitude relative to the start: minus the median of the first valid values (as the charts do)."""
    values = np.asarray(values, dtype=float)
    first = values[np.isfinite(values)][:RELATIVE_ALTITUDE_START_VALUES]
    return values - float(np.median(first)) if len(first) else values


@dataclass
class TrackSeries:
    """One sensor of the track: the column it comes from, its held values and when each was measured."""
    column: str
    values: np.ndarray          # held values, NaN before the first valid one
    measured_at: np.ndarray     # log time of the value that holds in each row, NaN before the first valid one


def make_series(column, time_s, raw_values):
    """TrackSeries of a column from its raw values (NaN where the row has no value)."""
    raw_values = np.asarray(raw_values, dtype=float)
    source = last_valid_index(raw_values)
    measured_at = np.where(source >= 0, time_s[np.maximum(source, 0)], np.nan) if len(time_s) else time_s.copy()
    return TrackSeries(column=column, values=held_values(raw_values), measured_at=measured_at)


def telemetry_rows(telemetry_columns, row_count):
    """Boolean array: rows in which at least one telemetry column has a value."""
    present = np.zeros(row_count, dtype=bool)
    for values in telemetry_columns:
        present |= np.isfinite(np.asarray(values, dtype=float))
    return present


def telemetry_ranges(time_s, present, last_row, max_gap_s=STALE_AFTER_S):
    """[(start, end)] log times with telemetry up to last_row; rows less than max_gap_s apart form one range, so
    only real gaps in the telemetry stay visible."""
    ranges = []
    for row in np.flatnonzero(present[:last_row + 1]):
        t = float(time_s[row])
        if ranges and t - ranges[-1][1] <= max_gap_s:
            ranges[-1][1] = t
        else:
            ranges.append([t, t])
    return [tuple(item) for item in ranges]


@dataclass
class FlightTrack:
    """The rows of one log up to the end of the flight, with one held series per sensor role."""
    time: np.ndarray                                  # log time of every row [s], ascending
    series: dict = field(default_factory=dict)        # role -> TrackSeries
    end_row: int = 0                                  # last row of the flight (see module text)
    telemetry: list = field(default_factory=list)     # [(start, end)] log times with telemetry

    @property
    def start_time(self):
        return float(self.time[0]) if len(self.time) else 0.0

    @property
    def end_time(self):
        return float(self.time[self.end_row]) if len(self.time) else 0.0

    @property
    def is_empty(self):
        return len(self.time) == 0

    def has(self, role):
        return role in self.series

    def row_at(self, t):
        """The row that holds at log time t (the last row with a time <= t), limited to the flight."""
        if self.is_empty:
            return 0
        row = int(np.searchsorted(self.time[:self.end_row + 1], t, side="right")) - 1
        return min(max(row, 0), self.end_row)

    def value(self, role, row):
        """Held value of a role in a row; None if the log has no such column or no value yet."""
        series = self.series.get(role)
        if series is None:
            return None
        value = series.values[row]
        return float(value) if np.isfinite(value) else None

    def flight_values(self, role):
        """The valid values of a role from the start to the end of the flight (to choose the scales of the
        gauges once per flight); empty without the column."""
        series = self.series.get(role)
        if series is None:
            return np.array([])
        values = series.values[:self.end_row + 1]
        return values[np.isfinite(values)]

    def age(self, role, row):
        """How old the value of a role is in a row [s]; infinite without a value (or without the column)."""
        series = self.series.get(role)
        if series is None or not np.isfinite(series.measured_at[row]):
            return float("inf")
        return float(self.time[row] - series.measured_at[row])

    def is_stale(self, role, row):
        """True if the value of a role is missing or older than STALE_AFTER_S."""
        return self.age(role, row) > STALE_AFTER_S

    def attitude(self, row):
        """(bank, pitch, stale) as the horizon shows it (see displayed_attitude), or None if the log has neither
        roll nor pitch. A missing axis counts as 0; stale is True if a present axis has no recent value."""
        present = [role for role in (roles.ROLL_ANGLE, roles.PITCH_ANGLE) if self.has(role)]
        if not present:
            return None
        stale = any(self.is_stale(role, row) for role in present)
        log_roll = self.value(roles.ROLL_ANGLE, row) or 0.0
        log_pitch = self.value(roles.PITCH_ANGLE, row) or 0.0
        bank, pitch = displayed_attitude(log_roll, log_pitch)
        return bank, pitch, stale


def build_track(time_s, columns):
    """FlightTrack from the time axis and the columns of a log.

    columns: [(column name, role, raw values)] in log order (values NaN where the row has none). Rows without a
    time are left out.
    """
    time_s = np.asarray(time_s, dtype=float)
    keep = np.isfinite(time_s)
    time_s = time_s[keep]
    columns = [(name, role, np.asarray(values, dtype=float)[keep]) for name, role, values in columns]
    column_roles = [(name, role) for name, role, _values in columns]
    values_of = {name: values for name, _role, values in columns}

    series = {}
    for role in TRACK_ROLES:
        column = choose_column(column_roles, role)
        if column is None:
            continue
        raw = relative_altitude(values_of[column]) if role == roles.ALTITUDE else values_of[column]
        series[role] = make_series(column, time_s, raw)

    present = telemetry_rows([values for _name, role, values in columns if is_telemetry_role(role)], len(time_s))
    end_row = int(np.flatnonzero(present)[-1]) if present.any() else max(len(time_s) - 1, 0)
    return FlightTrack(time=time_s, series=series, end_row=end_row,
                       telemetry=telemetry_ranges(time_s, present, end_row))


def is_telemetry_role(role):
    """True for the roles of sensors in the aircraft (a column without a known role does not count)."""
    return role is not None and role not in NOT_TELEMETRY_ROLES


def load_track(connection, log_id):
    """FlightTrack of a stored log; reads only the time axis and the columns of the shown and telemetry roles."""
    rows = connection.execute(
        "SELECT sensor.column_name, sensor.role, series.data FROM sensor JOIN series ON series.sensor_id = sensor.id "
        "WHERE sensor.log_id = ? ORDER BY sensor.position", (log_id,)).fetchall()
    time_s = np.array([])
    columns = []
    for name, role, data in rows:
        if role == roles.TIME:
            time_s = decode_series(data)
        elif role in TRACK_ROLES or is_telemetry_role(role):
            columns.append((name, role, decode_series(data)))
    return build_track(time_s, columns)
