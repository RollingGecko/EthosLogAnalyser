# -*- coding: utf-8 -*-
"""Stick modes 1 to 4 and what the radio of the flight recorder shows for one log row. Plain Python, no Tkinter.

A radio has two sticks; the mode says which axis sits on which stick (up-down / left-right):

* mode 1: left elevator / rudder, right throttle / aileron
* mode 2: left throttle / rudder, right elevator / aileron
* mode 3: left elevator / aileron, right throttle / rudder
* mode 4: left throttle / aileron, right elevator / rudder

The mode is a setting of the pilot (``stick_mode`` in the settings file, default 2), not a property of the flight.

The log has the channels QR (aileron), HR (elevator), SR (rudder) and Gas (throttle) with values from -1024 to +1024;
the display shows value / 1024 in percent. A positive value is shown to the right or up; the throttle has no centre
(-100 % at the bottom = idle).
"""

from dataclasses import dataclass

from ..db import sensor_roles as roles
from ..i18n import N_, tr
from .readouts import NO_VALUE, decimal_text

THROTTLE, ELEVATOR, AILERON, RUDDER = "throttle", "elevator", "aileron", "rudder"
AXIS_ROLES = {THROTTLE: roles.THROTTLE, ELEVATOR: roles.STICK_ELEVATOR, AILERON: roles.STICK_AILERON,
              RUDDER: roles.STICK_RUDDER}

STICK_MODES = (1, 2, 3, 4)
DEFAULT_STICK_MODE = 2
FULL_DEFLECTION = 1024.0

# Which way the elevator point moves. A positive value is drawn up. Whether "up" means pushing the elevator stick
# forward depends on how the transmitter is programmed and is not known from the log: the Viper-Jet logs fit
# "positive elevator = nose down = stick pushed = up". UNCERTAIN, to be checked with a known manoeuvre in the test
# EXE; set to False to draw the elevator point upside down. This is the only place that knows the direction.
POSITIVE_ELEVATOR_IS_UP = True


@dataclass(frozen=True)
class StickAxes:
    """The two axes of one stick."""
    vertical: str
    horizontal: str


# mode -> (left stick, right stick)
MODE_AXES = {
    1: (StickAxes(ELEVATOR, RUDDER), StickAxes(THROTTLE, AILERON)),
    2: (StickAxes(THROTTLE, RUDDER), StickAxes(ELEVATOR, AILERON)),
    3: (StickAxes(ELEVATOR, AILERON), StickAxes(THROTTLE, RUDDER)),
    4: (StickAxes(THROTTLE, AILERON), StickAxes(ELEVATOR, RUDDER)),
}

# the text naming the axes of a stick, vertical axis first (one text per pair: the words are translated together)
AXES_LABELS = {(THROTTLE, RUDDER): N_("Gas / Seite"), (ELEVATOR, AILERON): N_("Höhe / Quer"),
               (ELEVATOR, RUDDER): N_("Höhe / Seite"), (THROTTLE, AILERON): N_("Gas / Quer")}
MODE_TEXT = N_("Mode {number}")
ASSIGNMENT_TEXT = N_("Links: {left} · Rechts: {right}")


def valid_stick_mode(value):
    """The stick mode 1-4 for a value of the settings file; anything else (missing, text, 0, 5, 2.5) gives the
    default mode 2."""
    if isinstance(value, bool):
        return DEFAULT_STICK_MODE
    try:
        number = float(value)
    except (TypeError, ValueError):
        return DEFAULT_STICK_MODE
    return int(number) if number in STICK_MODES else DEFAULT_STICK_MODE


def stick_axes(mode):
    """(left stick, right stick) as StickAxes for a mode."""
    return MODE_AXES[valid_stick_mode(mode)]


def axes_label(axes):
    """Text naming the axes of a stick in the language of the window, e.g. "Gas / Seite"."""
    return tr(AXES_LABELS[(axes.vertical, axes.horizontal)])


def mode_text(mode):
    """"Mode 2" """
    return tr(MODE_TEXT, number=valid_stick_mode(mode))


def assignment_text(mode):
    """Which axes sit on which stick: "Links: Gas / Seite · Rechts: Höhe / Quer"."""
    left, right = stick_axes(mode)
    return tr(ASSIGNMENT_TEXT, left=axes_label(left), right=axes_label(right))


def has_sticks(track):
    """True if the log has at least one of the four channels (without any the radio is left out)."""
    return any(track.has(role) for role in AXIS_ROLES.values())


def axis_percent(raw):
    """Percent of full deflection (-100 .. +100) for a channel value."""
    return min(max(float(raw) / FULL_DEFLECTION * 100.0, -100.0), 100.0)


def axis_position(axis, raw):
    """Position of the dot on an axis, -1 .. +1 (right or up = +1). Without a value the stick rests: in the centre,
    the throttle at the bottom (idle)."""
    if raw is None:
        return -1.0 if axis == THROTTLE else 0.0
    position = axis_percent(raw) / 100.0
    return -position if axis == ELEVATOR and not POSITIVE_ELEVATOR_IS_UP else position


@dataclass(frozen=True)
class FieldReading:
    """What one stick field shows in a row: the dot position, the two values as text, and whether a channel that
    the log has gives no recent value."""
    x: float
    y: float
    text: str
    stale: bool


def _percent_text(raw):
    return f"{decimal_text(axis_percent(raw), 0, signed=True)} %"


def field_reading(track, row, axes):
    """The reading of the field of a stick (its two axes) in a row of the track.

    A channel the log does not have stays at rest and shows "—"; a channel whose newest value is older than the
    limit of the track shows "—" and turns the dot grey, the dot stays where the last value put it."""
    positions, texts, stale = [], [], False
    for axis in (axes.vertical, axes.horizontal):
        role = AXIS_ROLES[axis]
        raw = track.value(role, row) if track.has(role) else None
        channel_stale = track.has(role) and track.is_stale(role, row)
        stale = stale or channel_stale
        positions.append(axis_position(axis, raw))
        texts.append(NO_VALUE if raw is None or channel_stale else _percent_text(raw))
    return FieldReading(x=positions[1], y=positions[0], text=" / ".join(texts), stale=stale)


def radio_readings(track, row, mode):
    """(left field, right field) readings for a mode."""
    return tuple(field_reading(track, row, axes) for axes in stick_axes(mode))
