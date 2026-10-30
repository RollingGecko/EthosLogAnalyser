# -*- coding: utf-8 -*-
"""Stick modes of the flight recorder radio (recorder/stick_modes.py): the table of the four modes, the setting
value, stick values to dot positions and percent, gaps, missing channels, and one row of a real log."""

import numpy as np
import pytest

from helpers import ROOT
from ethosloganalyser import i18n
from ethosloganalyser.config import Params
from ethosloganalyser.db import FlightDatabase, import_paths
from ethosloganalyser.db import sensor_roles as roles
from ethosloganalyser.recorder import stick_modes
from ethosloganalyser.recorder.flight_track import build_track, load_track
from ethosloganalyser.recorder.stick_modes import (AILERON, DEFAULT_STICK_MODE, ELEVATOR, RUDDER, STICK_MODES,
                                                   THROTTLE, assignment_text, axes_label, axis_percent,
                                                   axis_position, field_reading, has_sticks, mode_text,
                                                   radio_readings, stick_axes, valid_stick_mode)

LARGEST_FLIGHT_LOG = ROOT / "examples" / "logs_2026" / "-Viper-Jet-2026-07-20-14-46-48.csv"
STICK_ROLES = {AILERON: roles.STICK_AILERON, ELEVATOR: roles.STICK_ELEVATOR, RUDDER: roles.STICK_RUDDER,
               THROTTLE: roles.THROTTLE}


def _track(time_s, **columns):
    """Track from columns given as axis name = values (a column is named like its role)."""
    return build_track(time_s, [(STICK_ROLES[axis], STICK_ROLES[axis], values) for axis, values in columns.items()])


def test_the_four_modes_put_every_axis_on_a_stick_exactly_once():
    assert STICK_MODES == (1, 2, 3, 4) and DEFAULT_STICK_MODE == 2
    for mode in STICK_MODES:
        left, right = stick_axes(mode)
        axes = [left.vertical, left.horizontal, right.vertical, right.horizontal]
        assert sorted(axes) == sorted([THROTTLE, ELEVATOR, AILERON, RUDDER]), mode
        assert {left.vertical, right.vertical} & {THROTTLE} and {left.vertical, right.vertical} & {ELEVATOR}
        assert {left.horizontal, right.horizontal} == {AILERON, RUDDER}


@pytest.mark.parametrize("mode, left, right", [
    (1, (ELEVATOR, RUDDER), (THROTTLE, AILERON)), (2, (THROTTLE, RUDDER), (ELEVATOR, AILERON)),
    (3, (ELEVATOR, AILERON), (THROTTLE, RUDDER)), (4, (THROTTLE, AILERON), (ELEVATOR, RUDDER))])
def test_the_table_of_the_modes(mode, left, right):
    stick_left, stick_right = stick_axes(mode)
    assert (stick_left.vertical, stick_left.horizontal) == left
    assert (stick_right.vertical, stick_right.horizontal) == right


def test_the_texts_of_the_modes_are_translated():
    assert mode_text(2) == "Mode 2"
    assert assignment_text(2) == "Links: Gas / Seite · Rechts: Höhe / Quer"
    assert assignment_text(1) == "Links: Höhe / Seite · Rechts: Gas / Quer"
    assert axes_label(stick_axes(3)[1]) == "Gas / Seite"
    i18n.set_language("en")
    try:
        assert assignment_text(4) == "Left: Throttle / Aileron · Right: Elevator / Rudder"
        assert mode_text(3) == "Mode 3"
    finally:
        i18n.set_language("de")
    i18n.set_language("es")
    try:
        assert assignment_text(3) == "Izquierda: Profundidad / Alerón · Derecha: Gas / Timón"
    finally:
        i18n.set_language("de")


@pytest.mark.parametrize("value, expected", [(1, 1), (4, 4), (2, 2), ("3", 3), (3.0, 3), (" 4 ", 4), (0, 2), (5, 2),
                                             (-1, 2), (2.5, 2), ("x", 2), ("", 2), (None, 2), (True, 2), ([3], 2),
                                             (float("nan"), 2), ({}, 2)])
def test_an_invalid_stick_mode_of_the_settings_file_gives_mode_2(value, expected):
    assert valid_stick_mode(value) == expected


def test_percent_of_the_channel_value():
    assert axis_percent(0) == 0 and axis_percent(1024) == 100 and axis_percent(-1024) == -100
    assert axis_percent(512) == 50 and axis_percent(-263) == pytest.approx(-25.68, abs=0.01)
    assert axis_percent(1300) == 100 and axis_percent(-3000) == -100          # limited to full deflection


def test_stick_value_to_dot_position():
    for axis in (AILERON, RUDDER, ELEVATOR):
        assert axis_position(axis, 0) == 0 and axis_position(axis, 1024) == 1 and axis_position(axis, -1024) == -1
        assert axis_position(axis, None) == 0                                   # no value: the stick rests
        assert axis_position(axis, 512) == 0.5 and axis_position(axis, 5000) == 1
    assert axis_position(THROTTLE, -1024) == -1                                  # idle: the dot is at the bottom
    assert axis_position(THROTTLE, None) == -1 and axis_position(THROTTLE, 1024) == 1
    assert axis_position(THROTTLE, 0) == 0                                       # no centre detent, just half


def test_the_direction_of_the_elevator_is_one_named_constant(monkeypatch):
    assert stick_modes.POSITIVE_ELEVATOR_IS_UP is True and axis_position(ELEVATOR, 1024) == 1
    monkeypatch.setattr(stick_modes, "POSITIVE_ELEVATOR_IS_UP", False)
    assert axis_position(ELEVATOR, 1024) == -1 and axis_position(ELEVATOR, -512) == 0.5
    assert axis_position(AILERON, 1024) == 1 and axis_position(THROTTLE, 1024) == 1     # nothing else changes
    assert axis_percent(1024) == 100                                             # the percent shows the log value


def test_a_field_shows_the_dot_and_the_percent_of_both_axes():
    time_s = np.arange(0, 5, 0.5)
    count = len(time_s)
    track = _track(time_s, throttle=np.full(count, -512.0), rudder=np.full(count, 256.0),
                   elevator=np.full(count, 1024.0), aileron=np.full(count, -1024.0))
    left, right = radio_readings(track, 3, 2)                 # mode 2: throttle / rudder, elevator / aileron
    assert (left.x, left.y, left.text, left.stale) == (0.25, -0.5, "−50 % / +25 %", False)
    assert (right.x, right.y, right.text, right.stale) == (-1.0, 1.0, "+100 % / −100 %", False)
    left, right = radio_readings(track, 3, 3)                 # mode 3: elevator / aileron, throttle / rudder
    assert (left.x, left.y, left.text) == (-1.0, 1.0, "+100 % / −100 %")
    assert (right.x, right.y, right.text) == (0.25, -0.5, "−50 % / +25 %")
    assert field_reading(track, 3, stick_axes(1)[0]).text == "+100 % / +25 %"          # mode 1 left: elevator / rudder
    assert radio_readings(track, 3, 99) == radio_readings(track, 3, 2)               # an unknown mode counts as 2


def test_zero_is_written_without_a_sign():
    time_s = np.arange(0, 3, 0.5)
    track = _track(time_s, throttle=np.full(len(time_s), -1024.0), rudder=np.zeros(len(time_s)))
    assert radio_readings(track, 0, 2)[0].text == "−100 % / 0 %"


def test_a_missing_channel_rests_and_shows_a_dash_without_turning_the_dot_grey():
    time_s = np.arange(0, 5, 0.5)
    count = len(time_s)
    track = _track(time_s, elevator=np.full(count, 512.0), aileron=np.full(count, 512.0))   # no throttle, no rudder
    assert has_sticks(track)
    left, right = radio_readings(track, 2, 2)
    assert (left.x, left.y, left.text, left.stale) == (0.0, -1.0, "— / —", False)       # throttle at the bottom
    assert (right.x, right.y, right.text, right.stale) == (0.5, 0.5, "+50 % / +50 %", False)


def test_a_log_without_any_stick_channel_has_no_radio():
    time_s = np.arange(0, 5, 0.5)
    other = build_track(time_s, [("altitude", roles.ALTITUDE, np.ones(len(time_s)))])
    assert not has_sticks(other)
    assert has_sticks(_track(time_s, rudder=np.ones(len(time_s))))
    assert has_sticks(_track(time_s, throttle=np.ones(len(time_s))))


def test_a_channel_without_a_recent_value_shows_a_dash_and_a_grey_dot_that_stays_put():
    time_s = np.arange(0, 10, 0.5)
    count = len(time_s)
    elevator = np.where(time_s < 3, 256.0, np.nan)             # the channel stops after 3 s
    track = _track(time_s, elevator=elevator, aileron=np.full(count, 512.0))
    held = radio_readings(track, track.row_at(4.0), 2)[1]       # 1.5 s old: still held
    assert (held.y, held.text, held.stale) == (0.25, "+25 % / +50 %", False)
    gone = radio_readings(track, track.row_at(6.0), 2)[1]       # older than 2 s
    assert gone.stale and gone.text == "— / +50 %"
    assert (gone.x, gone.y) == (0.5, 0.25)                      # the dot stays where the last value put it


def test_a_stick_reading_before_the_first_value_rests():
    time_s = np.arange(0, 5, 0.5)
    track = _track(time_s, throttle=np.where(time_s >= 2, 0.0, np.nan), rudder=np.zeros(len(time_s)))
    first = radio_readings(track, 0, 2)[0]
    assert (first.y, first.text) == (-1.0, "— / 0 %") and first.stale


@pytest.fixture(scope="module")
def largest_flight(tmp_path_factory):
    database = FlightDatabase(tmp_path_factory.mktemp("recorder") / "flights.db")
    import_paths(database, [LARGEST_FLIGHT_LOG], Params(chem="Li-Ion", cells=13, nominal_mah=9000))
    log_id = database.connection.execute("SELECT id FROM log_file").fetchone()[0]
    return load_track(database.connection, log_id)


def test_one_row_of_a_real_log_matches_the_columns_of_the_log(largest_flight):
    """Row 731 (log time 199.85 s) of the flight of 20 July 2026: QR -263, HR -799, SR 0, Gas -454."""
    track = largest_flight
    row = track.row_at(200.0)
    assert row == 731
    left, right = radio_readings(track, row, 2)                  # mode 2: throttle / rudder, elevator / aileron
    assert left.text == "−44 % / 0 %" and right.text == "−78 % / −26 %"
    assert (left.x, left.y) == (0.0, pytest.approx(-454 / 1024)) and not left.stale
    assert (right.x, right.y) == (pytest.approx(-263 / 1024), pytest.approx(-799 / 1024))
    left, right = radio_readings(track, row, 1)                  # mode 1: elevator / rudder, throttle / aileron
    assert left.text == "−78 % / 0 %" and right.text == "−44 % / −26 %"
