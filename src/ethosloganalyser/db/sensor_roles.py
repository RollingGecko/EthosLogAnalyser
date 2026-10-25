# -*- coding: utf-8 -*-
"""Which sensor role a log column plays (battery voltage, motor current, altitude, ...).

The roles are found from the column names Ethos writes today, with the same rules the analysis uses
(io/ethos_log.py, analysis/flight.py). There is no user interface for this yet; other manufacturers' sensor
names follow later (TW-027). A column without a known role is stored anyway, with role None.
"""

from ..io.ethos_log import CURR_KEYS, VOLT_KEYS, _find_col, _switch_columns

TIME = "time"
BATTERY_VOLTAGE = "battery_voltage"
MOTOR_CURRENT = "motor_current"
RPM = "rpm"
THROTTLE = "throttle"
ALTITUDE = "altitude"
VERTICAL_SPEED = "vertical_speed"
RSSI = "rssi"
LINK_QUALITY = "link_quality"
RX_VOLTAGE = "rx_voltage"
RX_CURRENT = "rx_current"
TX_VOLTAGE = "tx_voltage"
ESC_CONSUMPTION = "esc_consumption"
ACCELERATION_X = "acceleration_x"
ACCELERATION_Y = "acceleration_y"
ACCELERATION_Z = "acceleration_z"
ROLL_ANGLE = "roll_angle"
PITCH_ANGLE = "pitch_angle"
STICK_AILERON = "stick_aileron"
STICK_ELEVATOR = "stick_elevator"
STICK_RUDDER = "stick_rudder"
SWITCH = "switch"

# Columns that hold the date or the time of day of a sample; the database keeps one time axis instead.
DATE_TIME_NAMES = ("date", "datum", "time", "zeit", "t")

# (role, name parts) - the first rule with a part contained in the lower-case column name wins
_NAME_RULES = (
    (ESC_CONSUMPTION, ("consumption",)),
    (RPM, ("rpm",)),
    (RX_CURRENT, ("rxcurrent", "rx current", "rx curr")),
    (RX_VOLTAGE, ("rxbatt", "rx batt", "rxbat")),
    (TX_VOLTAGE, ("txbat",)),
    (RSSI, ("rssi",)),
    (LINK_QUALITY, ("vfr",)),
    (VERTICAL_SPEED, ("vspeed", "vspd", "vario")),
    (ALTITUDE, ("altitude", "höhe", "hoehe")),
    (ACCELERATION_X, ("accx",)),
    (ACCELERATION_Y, ("accy",)),
    (ACCELERATION_Z, ("accz",)),
    (ROLL_ANGLE, ("roll", "r.angle")),
    (PITCH_ANGLE, ("pitch", "nick", "p.angle")),
    (THROTTLE, ("gas", "thr")),
)

# stick channels are Ethos sources with exact names (same lists as analysis/flight.py)
_EXACT_RULES = (
    (STICK_AILERON, ("qr", "quer", "ail", "aileron", "querruder")),
    (STICK_ELEVATOR, ("hr", "ele", "elevator", "höhenruder")),
    (STICK_RUDDER, ("sr", "rud", "rudder", "seite", "seitenruder")),
)


def is_date_time_column(column_name):
    """True for the date and time-of-day columns of a log."""
    name = str(column_name).strip().lower()
    return name in DATE_TIME_NAMES or "time" in name


def _role_from_name(column_name):
    name = str(column_name).strip().lower()
    for role, names in _EXACT_RULES:
        if name in names:
            return role
    for role, parts in _NAME_RULES:
        if any(part in name for part in parts):
            return role
    return None


def assign_roles(frame, params):
    """Role of every column of a log: {column name: role or None}.

    Battery voltage and motor current are the columns the analysis uses (including the optional column names
    in the settings); switches are columns that only hold -1/0/1 and change during the log.
    """
    roles = {column: _role_from_name(column) for column in frame.columns}
    voltage_column = _find_col(frame.columns, VOLT_KEYS, params.col_voltage)
    current_column = _find_col(frame.columns, CURR_KEYS, params.col_current)
    if voltage_column is not None:
        roles[voltage_column] = BATTERY_VOLTAGE
    if current_column is not None:
        roles[current_column] = MOTOR_CURRENT
    for switch_name, _ in _switch_columns(frame):
        column = next((c for c in frame.columns if str(c).strip() == switch_name), None)
        if column is not None and roles.get(column) is None:
            roles[column] = SWITCH
    return roles


def columns_with_role(roles, role):
    """The columns that have the given role, in log order."""
    return [column for column, column_role in roles.items() if column_role == role]
