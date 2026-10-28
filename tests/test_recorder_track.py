# -*- coding: utf-8 -*-
"""Flight recorder track (recorder/flight_track.py): last value holds, missing values, gaps, column choice, end of
the flight, and one real log from the database."""

import math

import numpy as np
import pytest

from helpers import ROOT, ela
from ethosloganalyser.db import FlightDatabase, import_paths
from ethosloganalyser.db import sensor_roles as roles
from ethosloganalyser.recorder.flight_track import (STALE_AFTER_S, build_track, choose_column, displayed_attitude,
                                                    held_values, load_track, relative_altitude, telemetry_ranges)

NAN = float("nan")
SMALLEST_FLIGHT_LOG = ROOT / "examples" / "logs_2026" / "-Viper-Jet-2026-10-18-14-26-06.csv"


def _track(time_s, **columns):
    """Track from columns given as role=(name, values) or role=values (name = role)."""
    prepared = []
    for role, spec in columns.items():
        name, values = spec if isinstance(spec, tuple) else (role, spec)
        prepared.append((name, role, values))
    return build_track(time_s, prepared)


def test_the_last_value_holds_until_the_next_row():
    track = _track([0.0, 0.3, 0.6, 0.9], roll_angle=[10, 20, 30, 40])
    assert track.row_at(0.0) == 0 and track.row_at(0.29) == 0 and track.row_at(0.3) == 1 and track.row_at(0.89) == 2
    assert track.row_at(-5) == 0 and track.row_at(99) == 3
    assert [track.value(roles.ROLL_ANGLE, track.row_at(t)) for t in (0.1, 0.4, 0.95)] == [10, 20, 40]
    assert track.value(roles.PITCH_ANGLE, 0) is None                   # no such column


def test_missing_values_take_over_the_last_valid_value_of_their_column():
    assert np.array_equal(held_values([NAN, 1, NAN, NAN, 4, NAN]), [NAN, 1, 1, 1, 4, 4], equal_nan=True)
    track = _track([0, 1, 2, 3], roll_angle=[5, NAN, NAN, 8], pitch_angle=[NAN, 2, NAN, NAN])
    assert [track.value(roles.ROLL_ANGLE, row) for row in range(4)] == [5, 5, 5, 8]
    assert [track.value(roles.PITCH_ANGLE, row) for row in range(4)] == [None, 2, 2, 2]


def test_a_value_older_than_two_seconds_is_stale():
    time_s = np.arange(0, 6, 0.5)
    roll = np.full(len(time_s), NAN)
    roll[1] = 7                                                     # measured at 0.5 s only
    track = _track(time_s, roll_angle=roll, altitude=np.ones(len(time_s)))
    assert math.isinf(track.age(roles.ROLL_ANGLE, 0)) and track.is_stale(roles.ROLL_ANGLE, 0)
    assert track.age(roles.ROLL_ANGLE, 5) == 2.0 and not track.is_stale(roles.ROLL_ANGLE, 5)     # exactly 2 s
    assert track.age(roles.ROLL_ANGLE, 6) == 2.5 and track.is_stale(roles.ROLL_ANGLE, 6)
    assert track.value(roles.ROLL_ANGLE, 6) == 7                     # the value is kept, only marked as old
    assert STALE_AFTER_S == 2.0


def test_the_first_column_of_a_role_is_used_and_esc_rpm_is_preferred():
    column_roles = [("Altitude(m)", roles.ALTITUDE), ("RPM(U/min)", roles.RPM), ("Altitude(m).1", roles.ALTITUDE),
                    ("ESC RPM(U/min)", roles.RPM)]
    assert choose_column(column_roles, roles.ALTITUDE) == "Altitude(m)"
    assert choose_column(column_roles, roles.RPM) == "ESC RPM(U/min)"
    assert choose_column(column_roles, roles.ROLL_ANGLE) is None
    track = _track([0, 1], altitude=("Altitude(m)", [3, 4]), rpm=("RPM(U/min)", [100, 200]))
    assert track.series[roles.ALTITUDE].column == "Altitude(m)" and track.series[roles.RPM].column == "RPM(U/min)"


def test_altitude_is_relative_to_the_median_of_the_first_values():
    values = [NAN, 100, 102, 101, 99, 100, 103, 98, 100, 150]
    assert relative_altitude(values)[-1] == pytest.approx(50)      # median of the 8 first valid values is 100
    track = _track(np.arange(10.0), altitude=values)
    assert track.value(roles.ALTITUDE, 9) == pytest.approx(50)


def test_the_flight_ends_with_the_last_row_with_telemetry():
    time_s = np.arange(0, 10.0)
    sticks = np.zeros(10)                                           # logged by the transmitter until the end
    voltage = np.array([48, 48, 47, 47, 46, NAN, NAN, NAN, NAN, NAN])
    track = _track(time_s, stick_aileron=sticks, battery_voltage=voltage, tx_voltage=np.full(10, 8.1))
    assert track.end_row == 4 and track.end_time == 4.0
    assert track.row_at(9.0) == 4                                   # positions after the flight are not shown
    assert track.telemetry == [(0.0, 4.0)]
    without_telemetry = _track(time_s, stick_aileron=sticks, throttle=sticks)
    assert without_telemetry.end_row == 9 and without_telemetry.telemetry == []


def test_telemetry_ranges_show_only_real_gaps():
    time_s = np.array([0, 0.3, 0.6, 3.0, 3.3, 9.0])
    present = np.array([True, True, True, True, True, True])
    assert telemetry_ranges(time_s, present, 5) == [(0.0, 0.6), (3.0, 3.3), (9.0, 9.0)]   # gaps of 2.4 and 5.7 s
    almost = np.array([0, 1.9, 3.8, 5.7])                           # rows 1.9 s apart: no gap
    assert telemetry_ranges(almost, np.ones(4, dtype=bool), 3) == [(0.0, 5.7)]
    assert telemetry_ranges(time_s, present, 2) == [(0.0, 0.6)]


def test_rows_without_a_time_are_left_out():
    track = _track([0.0, NAN, 1.0], roll_angle=[1, 2, 3])
    assert list(track.time) == [0.0, 1.0] and track.value(roles.ROLL_ANGLE, 1) == 3


def test_attitude_follows_the_sign_convention_and_missing_axes():
    assert displayed_attitude(30, 10) == (30, -10)                  # log pitch > 0 is nose down (TW-053)
    both = _track([0, 1], roll_angle=[30, 30], pitch_angle=[10, 10])
    assert both.attitude(0) == (30, -10, False)
    assert _track([0, 1], roll_angle=[30, 30]).attitude(1) == (30, 0, False)         # no pitch column: 0
    assert _track([0, 1], pitch_angle=[10, 10]).attitude(1) == (0, -10, False)       # no roll column: 0
    assert _track([0, 1], altitude=[1, 2]).attitude(0) is None                       # neither: no horizon
    late = _track([0, 1, 5], roll_angle=[NAN, 3, NAN], pitch_angle=[1, 1, 1])
    assert late.attitude(0)[2] and not late.attitude(1)[2] and late.attitude(2)[2]  # stale before and after


def test_an_empty_track():
    track = build_track([], [])
    assert track.is_empty and track.row_at(5) == 0 and track.end_time == 0.0 and track.attitude(0) is None


def test_the_smallest_flight_log_of_the_examples(tmp_path):
    database = FlightDatabase(str(tmp_path / "recorder.db"))
    try:
        import_paths(database, [str(SMALLEST_FLIGHT_LOG)], ela.Params(chem="Li-Ion", cells=13, nominal_mah=9000))
        log_id = database.connection.execute("SELECT log_id FROM flight").fetchone()[0]
        track = load_track(database.connection, log_id)
    finally:
        database.close()
    assert len(track.time) == 739 and track.end_row == 738 and track.end_time == pytest.approx(201.13)
    assert track.series[roles.ROLL_ANGLE].column == "R.angle(°)" and track.series[roles.PITCH_ANGLE].column == "P.angle(°)"
    assert track.series[roles.ALTITUDE].column == "Altitude(m)" and track.series[roles.RPM].column == "ESC RPM(U/min)"
    assert {roles.THROTTLE, roles.STICK_AILERON, roles.BATTERY_VOLTAGE, roles.MOTOR_CURRENT} <= set(track.series)
    assert track.telemetry == [(0.0, pytest.approx(201.13))]
    bank, pitch, stale = track.attitude(track.row_at(100.0))
    assert not stale and -180 <= bank <= 180 and -90 <= pitch <= 90
