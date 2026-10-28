# -*- coding: utf-8 -*-
"""What the cockpit gauges of the flight recorder show: their scales per flight, the value of each row as text,
and which gauges a log has data for. Plain Python, no Tkinter.

The four gauges next to the horizon (in the order of the user) and what they hold:

* altitude: round dial, relative to the start (the track gives the relative altitude);
* vertical speed: round dial centred on 0, only from a vario sensor (never worked out from the altitude);
* drive: RPM as a round dial and the throttle as a bar 0-100 % below it;
* battery: current as a round dial and the voltage as a bar between the lowest and highest value of the flight,
  with the voltage per cell if the battery settings of the aircraft have a cell count.

A gauge whose sensors are all missing from the log is not shown; one of two sensors missing leaves the other.
A value older than STALE_AFTER_S shows as NO_VALUE with a grey pointer (recorder/flight_track.py).
"""

import math
from dataclasses import dataclass

import numpy as np

from ..db import sensor_roles as roles
from ..i18n import N_, get_language, tr
from .dials import ARC, CENTRED_ARC, Scale, fraction, scale_for, vertical_speed_scale
from .layout import ALTITUDE, BATTERY, RPM_THROTTLE, VERTICAL_SPEED

NO_VALUE = "—"
MINUS = "−"
THOUSANDS_SEPARATOR = " "     # no-break space: "84 000" in every language (no comma/point confusion)

# smallest full scale of a dial, so a flight with tiny values does not get a scale of 1
MINIMUM_FULL_SCALE = {roles.ALTITUDE: 10, roles.RPM: 1000, roles.MOTOR_CURRENT: 5}
VOLTAGE_LOW_PERCENTILE = 0.5       # the lowest 0.5 % of the voltage values do not stretch the bar (single drops)

PANEL_TITLES = {ALTITUDE: N_("Höhe"), VERTICAL_SPEED: N_("Steigen/Sinken"), RPM_THROTTLE: N_("Antrieb"),
                BATTERY: N_("Akku")}
QUANTITY_NAMES = {roles.ALTITUDE: N_("Höhe"), roles.VERTICAL_SPEED: N_("Steigen/Sinken"),
                  roles.RPM: N_("Drehzahl"), roles.THROTTLE: N_("Gas"), roles.BATTERY_VOLTAGE: N_("Spannung"),
                  roles.MOTOR_CURRENT: N_("Strom")}
RPM_UNIT = N_("U/min")
PER_CELL_UNIT = N_("V/Zelle")

# panel -> (role shown as a round dial, role shown as a bar); a role the log does not have is left out
PANEL_ROLES = {ALTITUDE: (roles.ALTITUDE, None), VERTICAL_SPEED: (roles.VERTICAL_SPEED, None),
               RPM_THROTTLE: (roles.RPM, roles.THROTTLE), BATTERY: (roles.MOTOR_CURRENT, roles.BATTERY_VOLTAGE)}
# order of the lines in the minimal layout (numbers only)
READOUT_ORDER = (roles.ALTITUDE, roles.VERTICAL_SPEED, roles.RPM, roles.THROTTLE, roles.BATTERY_VOLTAGE,
                 roles.MOTOR_CURRENT)


# ---------------- numbers as text ----------------
def decimal_text(value, places, signed=False):
    """A number with a fixed count of decimals, the decimal sign of the language and a real minus sign;
    signed adds "+" to positive values. -0 becomes 0."""
    rounded = round(float(value), places)
    if rounded == 0:
        rounded = 0.0
    text = f"{abs(rounded):.{places}f}"
    if get_language() in ("de", "es"):
        text = text.replace(".", ",")
    if rounded < 0:
        return MINUS + text
    return "+" + text if signed and rounded > 0 else text


def grouped_text(value):
    """A whole number with a space between thousands: 84 000."""
    number = int(round(float(value)))
    text = f"{abs(number):,}".replace(",", THOUSANDS_SEPARATOR)
    return MINUS + text if number < 0 else text


def throttle_percent(raw):
    """Throttle channel (-1024 .. +1024) in percent 0-100, the same conversion as the analysis."""
    return min(max((float(raw) + 1024.0) / 2048.0 * 100.0, 0.0), 100.0)


def cell_voltage(voltage, cells):
    """Voltage per cell, None without a cell count (0 = not set in the battery settings)."""
    return voltage / cells if cells and cells > 0 and voltage is not None else None


# ---------------- scales of one flight ----------------
@dataclass(frozen=True)
class FlightScales:
    """The scales of one flight: dials per role, the voltage bar range and the cell count."""
    dials: dict                      # role -> Scale
    voltage_range: tuple = (0.0, 1.0)
    cells: int = 0

    def decimals(self, role):
        """Decimals of the number of a role: 1 for small currents and the vertical speed, else 0."""
        if role == roles.MOTOR_CURRENT:
            return 1 if self.dials[role].full <= 20 else 0
        return 1 if role in (roles.VERTICAL_SPEED, roles.BATTERY_VOLTAGE) else 0


def _largest(values):
    return float(np.max(values)) if len(values) else 0.0


def voltage_range(values):
    """Range of the voltage bar in whole volts: from the lowest to the highest value of the flight. Readings of
    0 V (sensor not ready) and single drops (the lowest VOLTAGE_LOW_PERCENTILE %) do not count."""
    valid = values[values > 0] if len(values) else values
    if not len(valid):
        return 0.0, 1.0
    low = math.floor(float(np.percentile(valid, VOLTAGE_LOW_PERCENTILE)))
    high = math.ceil(float(np.max(valid)))
    return (float(low - 1), float(high + 1)) if high <= low else (float(low), float(high))


def flight_scales(track, cells=0):
    """The scales of the dials and the voltage bar, worked out once from the values of the flight."""
    dials = {}
    for role, minimum in MINIMUM_FULL_SCALE.items():
        if track.has(role):
            dials[role] = scale_for(_largest(track.flight_values(role)), minimum)
    if track.has(roles.VERTICAL_SPEED):
        values = track.flight_values(roles.VERTICAL_SPEED)
        dials[roles.VERTICAL_SPEED] = vertical_speed_scale(float(np.max(np.abs(values))) if len(values) else 0.0)
    voltage = voltage_range(track.flight_values(roles.BATTERY_VOLTAGE)) if track.has(roles.BATTERY_VOLTAGE) \
        else (0.0, 1.0)
    return FlightScales(dials=dials, voltage_range=voltage, cells=int(cells or 0))


def present_panels(track):
    """{panel: (dial role or None, bar role or None)} for the gauges the log has data for."""
    panels = {}
    for panel, (dial_role, bar_role) in PANEL_ROLES.items():
        dial_role = dial_role if track.has(dial_role) else None
        bar_role = bar_role if bar_role is not None and track.has(bar_role) else None
        if dial_role or bar_role:
            panels[panel] = (dial_role, bar_role)
    return panels


def arc_of(role):
    """The arc of the dial of a role (the vertical speed is centred on 0)."""
    return CENTRED_ARC if role == roles.VERTICAL_SPEED else ARC


# ---------------- the value of one row ----------------
@dataclass(frozen=True)
class Reading:
    """What a gauge shows in one row: the value (None if missing or stale), its text and where the pointer or
    bar stands (0..1 for bars; the value itself for dials, the dial limits it)."""
    value: object
    text: str
    share: float
    stale: bool


def value_text(role, value, scales):
    """The number of a role with its unit, e.g. "132 m", "+2,4 m/s", "84 000 U/min", "45 %", "48,6 V · 3,74
    V/Zelle", "63 A"."""
    if role == roles.ALTITUDE:
        return f"{decimal_text(value, 0)} m"
    if role == roles.VERTICAL_SPEED:
        return f"{decimal_text(value, 1, signed=True)} m/s"
    if role == roles.RPM:
        return f"{grouped_text(round(value, -2))} {tr(RPM_UNIT)}"
    if role == roles.THROTTLE:
        return f"{decimal_text(throttle_percent(value), 0)} %"
    if role == roles.BATTERY_VOLTAGE:
        text = f"{decimal_text(value, 1)} V"
        per_cell = cell_voltage(value, scales.cells)
        return text if per_cell is None else f"{text} · {decimal_text(per_cell, 2)} {tr(PER_CELL_UNIT)}"
    if role == roles.MOTOR_CURRENT:
        return f"{decimal_text(value, scales.decimals(role))} A"
    raise ValueError(role)


def reading(track, role, row, scales):
    """What the gauge of a role shows in a row; NO_VALUE if the value is missing or older than STALE_AFTER_S."""
    value = track.value(role, row)
    if value is None or track.is_stale(role, row):
        return Reading(value=None, text=NO_VALUE, share=0.0, stale=True)
    if role == roles.THROTTLE:
        share = throttle_percent(value) / 100.0
    elif role == roles.BATTERY_VOLTAGE:
        share = fraction(value, *scales.voltage_range)
    else:
        share = 0.0
    return Reading(value=value, text=value_text(role, value, scales), share=share, stale=False)


def widest_text(role, scales):
    """The widest number a role can show in this flight (to size the font so that no number is cut off)."""
    if role in scales.dials:
        full = scales.dials[role].full
        samples = (full, -full) if role == roles.VERTICAL_SPEED else (full, -full / 10)
    elif role == roles.BATTERY_VOLTAGE:
        samples = (max(scales.voltage_range[1], 10.0),)
    else:
        samples = (1024.0,)                                    # throttle: 100 %
    return max((value_text(role, sample, scales) for sample in samples), key=len)


def readout_lines(track):
    """Roles of the lines in the minimal layout, in a fixed order, only those the log has."""
    return [role for role in READOUT_ORDER if track.has(role)]


def dial_scale(scales, role):
    """Scale of the dial of a role."""
    scale = scales.dials.get(role)
    return scale if scale is not None else Scale(full=1.0, step=1.0)
