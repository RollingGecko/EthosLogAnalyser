# -*- coding: utf-8 -*-
"""What the recorder gauges show (recorder/readouts.py): numbers as text, throttle and cell voltage, scales per
flight, gauges of logs with missing sensors, stale values, and one row of a real log."""

import numpy as np
import pytest

from helpers import ROOT
from ethosloganalyser import i18n
from ethosloganalyser.db import FlightDatabase, import_paths
from ethosloganalyser.db import sensor_roles as roles
from ethosloganalyser.config import Params
from ethosloganalyser.recorder.flight_track import build_track, load_track
from ethosloganalyser.recorder.layout import (ALTITUDE, BATTERY, HORIZON, Rect, RPM_THROTTLE, TIMELINE,
                                              VERTICAL_SPEED, recorder_layout)
from ethosloganalyser.recorder.readouts import (NO_VALUE, cell_voltage, decimal_text, flight_scales, grouped_text,
                                                present_panels, readout_lines, reading, throttle_percent,
                                                value_text, voltage_range, widest_text)

NAN = float("nan")
LARGEST_FLIGHT_LOG = ROOT / "examples" / "logs_2026" / "-Viper-Jet-2026-07-20-14-46-48.csv"


def _track(time_s, **columns):
    """Track from columns given as role=values (the column name is the role)."""
    return build_track(time_s, [(role, role, values) for role, values in columns.items()])


def _full_track():
    time_s = np.arange(0, 10, 0.5)
    count = len(time_s)
    return _track(time_s, roll_angle=np.zeros(count), pitch_angle=np.zeros(count),
                  altitude=np.linspace(0, 132, count), vertical_speed=np.linspace(-6, 2.4, count),
                  rpm=np.linspace(0, 84000, count), throttle=np.linspace(-1024, 1024, count),
                  battery_voltage=np.linspace(54.6, 44.2, count), motor_current=np.linspace(0, 63, count))


def test_numbers_have_fixed_decimals_the_sign_of_the_language_and_a_real_minus():
    assert decimal_text(2.44, 1, signed=True) == "+2,4" and decimal_text(-2.44, 1, signed=True) == "−2,4"
    assert decimal_text(-0.04, 1, signed=True) == "0,0" and decimal_text(132.4, 0) == "132"
    assert decimal_text(3, 2) == "3,00"
    i18n.set_language("en")
    try:
        assert decimal_text(2.44, 1, signed=True) == "+2.4"
    finally:
        i18n.set_language("de")
    assert grouped_text(84000) == "84 000" and grouped_text(950) == "950" and grouped_text(-1200) == "−1 200"


def test_throttle_and_cell_voltage():
    assert throttle_percent(-1024) == 0 and throttle_percent(0) == 50 and throttle_percent(1024) == 100
    assert throttle_percent(-454) == pytest.approx(27.83, abs=0.01)          # the same as the analysis
    assert throttle_percent(2000) == 100 and throttle_percent(-2000) == 0
    assert cell_voltage(49.04, 13) == pytest.approx(3.7723, abs=1e-4)
    assert cell_voltage(49.04, 0) is None and cell_voltage(None, 13) is None


def test_the_voltage_bar_ignores_zero_readings_and_single_drops():
    values = np.concatenate([np.zeros(20), np.linspace(54.6, 40.4, 1000), [3.2]])
    assert voltage_range(values) == (40.0, 55.0)
    assert voltage_range(np.full(5, 54.8)) == (54.0, 55.0)
    assert voltage_range(np.full(5, 54.0)) == (53.0, 55.0)                    # one whole value: a range around it
    assert voltage_range(np.array([])) == (0.0, 1.0)


def test_texts_of_every_gauge():
    scales = flight_scales(_full_track(), cells=13)
    assert value_text(roles.ALTITUDE, 132.4, scales) == "132 m"
    assert value_text(roles.VERTICAL_SPEED, 2.44, scales) == "+2,4 m/s"
    assert value_text(roles.RPM, 84012, scales) == "84 000 U/min"
    assert value_text(roles.THROTTLE, -454, scales) == "28 %"
    assert value_text(roles.BATTERY_VOLTAGE, 49.04, scales) == "49,0 V · 3,77 V/Zelle"
    assert value_text(roles.MOTOR_CURRENT, 63.2, scales) == "63 A"
    assert value_text(roles.BATTERY_VOLTAGE, 49.04, flight_scales(_full_track())) == "49,0 V"   # no cell count
    i18n.set_language("en")
    try:
        assert value_text(roles.RPM, 84000, scales) == "84 000 rpm"
        assert value_text(roles.BATTERY_VOLTAGE, 49.04, scales) == "49.0 V · 3.77 V/cell"
    finally:
        i18n.set_language("de")


def test_small_currents_get_one_decimal():
    time_s = np.arange(0, 5, 0.5)
    scales = flight_scales(_track(time_s, motor_current=np.linspace(0, 4.3, len(time_s))))
    assert scales.dials[roles.MOTOR_CURRENT].full == 5
    assert value_text(roles.MOTOR_CURRENT, 4.26, scales) == "4,3 A"


def test_scales_are_chosen_once_from_the_values_of_the_flight():
    scales = flight_scales(_full_track(), cells=13)
    assert scales.dials[roles.ALTITUDE].full == 120          # relative to the start: 132 m minus about 24 m
    assert scales.dials[roles.VERTICAL_SPEED].full == 10 and scales.dials[roles.VERTICAL_SPEED].centred
    assert scales.dials[roles.RPM].full == 100000 and scales.dials[roles.MOTOR_CURRENT].full == 80
    assert scales.voltage_range == (44.0, 55.0) and scales.cells == 13
    assert roles.THROTTLE not in scales.dials                                # a bar, no dial


def test_a_log_with_every_sensor_shows_every_gauge():
    panels = present_panels(_full_track())
    assert panels == {ALTITUDE: (roles.ALTITUDE, None), VERTICAL_SPEED: (roles.VERTICAL_SPEED, None),
                      RPM_THROTTLE: (roles.RPM, roles.THROTTLE),
                      BATTERY: (roles.MOTOR_CURRENT, roles.BATTERY_VOLTAGE)}
    assert readout_lines(_full_track()) == [roles.ALTITUDE, roles.VERTICAL_SPEED, roles.RPM, roles.THROTTLE,
                                            roles.BATTERY_VOLTAGE, roles.MOTOR_CURRENT]


def test_missing_sensors_hide_their_gauge_or_their_half_of_it():
    time_s = np.arange(0, 5, 0.5)
    values = np.ones(len(time_s))
    glider = _track(time_s, altitude=values, vertical_speed=values)
    assert present_panels(glider) == {ALTITUDE: (roles.ALTITUDE, None),
                                      VERTICAL_SPEED: (roles.VERTICAL_SPEED, None)}
    without_vario = _track(time_s, altitude=values, throttle=values, battery_voltage=values)
    assert present_panels(without_vario) == {ALTITUDE: (roles.ALTITUDE, None), RPM_THROTTLE: (None, roles.THROTTLE),
                                             BATTERY: (None, roles.BATTERY_VOLTAGE)}
    only_rpm_and_current = _track(time_s, rpm=values, motor_current=values)
    assert present_panels(only_rpm_and_current) == {RPM_THROTTLE: (roles.RPM, None),
                                                    BATTERY: (roles.MOTOR_CURRENT, None)}
    assert present_panels(_track(time_s, roll_angle=values)) == {}
    assert readout_lines(glider) == [roles.ALTITUDE, roles.VERTICAL_SPEED]


def test_a_gap_shows_no_value():
    time_s = np.arange(0, 10, 0.5)
    altitude = np.where(time_s < 3, 50.0, NAN)                              # the sensor stops after 3 s
    track = _track(time_s, altitude=altitude, roll_angle=np.zeros(len(time_s)))
    scales = flight_scales(track)
    assert reading(track, roles.ALTITUDE, track.row_at(4.0), scales).text == "0 m"     # 1.5 s old: still held
    stale = reading(track, roles.ALTITUDE, track.row_at(6.0), scales)
    assert stale.text == NO_VALUE and stale.stale and stale.value is None
    assert reading(track, roles.MOTOR_CURRENT, 0, scales).text == NO_VALUE   # no such column


def test_bar_shares():
    track = _full_track()
    scales = flight_scales(track)
    assert reading(track, roles.THROTTLE, 0, scales).share == 0
    assert reading(track, roles.THROTTLE, track.end_row, scales).share == 1
    voltage = reading(track, roles.BATTERY_VOLTAGE, 0, scales)
    assert voltage.share == pytest.approx((54.6 - 44) / 11)


def test_widest_text_covers_the_largest_values_of_the_flight():
    scales = flight_scales(_full_track(), cells=13)
    assert widest_text(roles.ALTITUDE, scales) == "120 m"
    assert widest_text(roles.VERTICAL_SPEED, scales) == "+10,0 m/s"
    assert widest_text(roles.RPM, scales) == "100 000 U/min"
    assert widest_text(roles.THROTTLE, scales) == "100 %"
    assert widest_text(roles.BATTERY_VOLTAGE, scales) == "55,0 V · 4,23 V/Zelle"


@pytest.mark.parametrize("size", [(1920, 1080), (1280, 720), (900, 600), (600, 400)])
@pytest.mark.parametrize("line_height", [16, 24])
def test_layout_with_the_gauges_of_a_full_log_and_of_a_glider(size, line_height):
    time_s = np.arange(0, 5, 0.5)
    values = np.ones(len(time_s))
    glider = _track(time_s, altitude=values, vertical_speed=values)
    for track, horizon in ((_full_track(), True), (glider, False)):
        present = set(present_panels(track)) | ({HORIZON} if horizon else set())
        rects = recorder_layout(*size, present, line_height).rects
        page = Rect(0, 0, *size)
        assert all(rect.inside(page) for rect in rects.values())
        shown = set(rects) - {TIMELINE}
        assert shown <= present | {"readouts"}
        if "readouts" not in shown:
            assert shown == present                                         # every gauge that has data


@pytest.fixture(scope="module")
def largest_flight(tmp_path_factory):
    database = FlightDatabase(tmp_path_factory.mktemp("recorder") / "flights.db")
    import_paths(database, [LARGEST_FLIGHT_LOG], Params(chem="Li-Ion", cells=13, nominal_mah=9000))
    log_id = database.connection.execute("SELECT id FROM log_file").fetchone()[0]
    return load_track(database.connection, log_id)


def test_one_row_of_a_real_log_matches_the_columns_of_the_log(largest_flight):
    """Row 731 of the log (log time 199.85 s) of the flight of 20 July 2026, which is row 730 of the track (the
    flight starts at log time 0.18 s): Altitude(m) 104.7 (8.3 m at the start of the flight is 0 -> 96 m),
    VSpeed(m/s) 10.0, ESC RPM 33 100, Gas -454 (28 %), VFAS 49.04 V (13 cells: 3.77 V), Current 5.3 A."""
    track = largest_flight
    scales = flight_scales(track, cells=13)
    row = track.row_at(199.86 - track.origin)
    assert row == 730 and track.time[row] + track.origin == pytest.approx(199.85, abs=0.005)
    texts = {role: reading(track, role, row, scales).text for role in readout_lines(track)}
    assert texts == {roles.ALTITUDE: "96 m", roles.VERTICAL_SPEED: "+10,0 m/s", roles.RPM: "33 100 U/min",
                     roles.THROTTLE: "28 %", roles.BATTERY_VOLTAGE: "49,0 V · 3,77 V/Zelle",
                     roles.MOTOR_CURRENT: "5 A"}
    assert scales.dials[roles.ALTITUDE].full == 200 and scales.dials[roles.RPM].full == 120000
    assert scales.dials[roles.MOTOR_CURRENT].full == 120 and scales.dials[roles.VERTICAL_SPEED].full == 10
    assert scales.voltage_range == (41.0, 55.0)
