# -*- coding: utf-8 -*-
"""Geometry of the artificial horizon (recorder/gauges.py) at the corners of the attitude range."""

import math

import pytest

from ethosloganalyser.recorder.gauges import (LADDER_SLOTS, Dial, aircraft_symbol, bank_scale_ticks, clip_half_plane,
                                              format_attitude, horizon_dial, horizon_shape, line_in_circle)

DIAL = Dial(cx=200.0, cy=200.0, radius=100.0)


def _points(flat):
    return list(zip(flat[0::2], flat[1::2]))


def _centroid(flat):
    points = _points(flat)
    return sum(x for x, _ in points) / len(points), sum(y for _, y in points) / len(points)


def _area(flat):
    points = _points(flat)
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))) / 2


def _inside(flat, dial=DIAL, tolerance=0.5):
    return all(math.hypot(x - dial.cx, y - dial.cy) <= dial.radius + tolerance for x, y in _points(flat))


def test_level_flight_shows_sky_above_and_ground_below():
    shape = horizon_shape(DIAL, 0, 0)
    assert _centroid(shape.sky)[1] < 200 < _centroid(shape.ground)[1]
    assert _area(shape.sky) == pytest.approx(_area(shape.ground), rel=0.01)
    x0, y0, x1, y1 = shape.horizon_line
    assert y0 == pytest.approx(200) and y1 == pytest.approx(200) and abs(x1 - x0) == pytest.approx(200)
    assert _inside(shape.sky) and _inside(shape.ground)
    tip = _points(shape.bank_pointer)[0]
    assert tip[0] == pytest.approx(200) and tip[1] < 200              # the bank pointer stands at the top


def test_nose_up_moves_the_horizon_down():
    up = horizon_shape(DIAL, 0, 10)
    assert up.horizon_line[1] > 200 and _area(up.sky) > _area(up.ground)
    assert horizon_shape(DIAL, 0, -10).horizon_line[1] < 200


def test_right_bank_raises_the_right_end_of_the_horizon():
    x0, y0, x1, y1 = horizon_shape(DIAL, 30, 0).horizon_line
    assert x1 > x0 and y1 < y0                                        # the line rises to the right
    assert _points(horizon_shape(DIAL, 30, 0).bank_pointer)[0][0] < 200  # pointer moves to the left


def test_knife_edge_at_90_degrees_puts_the_sky_on_the_left():
    shape = horizon_shape(DIAL, 90, 0)
    assert _centroid(shape.sky)[0] < 200 < _centroid(shape.ground)[0]


@pytest.mark.parametrize("bank", [180, -180])
def test_inverted_flight_puts_the_ground_on_top(bank):
    shape = horizon_shape(DIAL, bank, 0)
    assert _centroid(shape.ground)[1] < 200 < _centroid(shape.sky)[1]
    assert _points(shape.bank_pointer)[0][1] > 200                    # the pointer is on the sky side: below


def test_a_jump_across_180_degrees_looks_the_same_on_both_sides():
    left, right = horizon_shape(DIAL, 179.9, 5), horizon_shape(DIAL, -179.9, 5)
    assert _centroid(left.sky) == pytest.approx(_centroid(right.sky), abs=0.5)


@pytest.mark.parametrize("pitch, all_of", [(90, "sky"), (-90, "ground")])
def test_pitch_90_fills_the_window_with_sky_or_ground(pitch, all_of):
    shape = horizon_shape(DIAL, 0, pitch)
    filled, empty = (shape.sky, shape.ground) if all_of == "sky" else (shape.ground, shape.sky)
    assert empty == [] and _area(filled) == pytest.approx(math.pi * 100 ** 2, rel=0.01)
    assert shape.horizon_line == ()
    assert 0 < len(shape.ladder) <= LADDER_SLOTS
    assert all(abs(line.pitch) <= 90 for line in shape.ladder)


def test_the_ladder_shows_lines_every_10_degrees_near_the_pitch():
    shape = horizon_shape(DIAL, 0, 0)
    assert sorted(line.pitch for line in shape.ladder) == [-20, -10, 10, 20]   # +-30 lie on the rim: left out
    ten = next(line for line in shape.ladder if line.pitch == 10)
    assert ten.line[1] == pytest.approx(200 - 100 / 3)                # 10 degrees above the horizon line
    nose_up = horizon_shape(DIAL, 0, 25)
    assert {line.pitch for line in nose_up.ladder} == {10, 20, 30, 40, 50}   # within 30 degrees of 25
    assert len(horizon_shape(DIAL, 45, 40).ladder) <= LADDER_SLOTS


def test_helpers():
    square = [(0, 0), (10, 0), (10, 10), (0, 10)]
    assert len(clip_half_plane(square, (0, 5), (0, -1))) == 4         # upper half
    assert clip_half_plane(square, (0, -5), (0, -1)) == []
    assert line_in_circle(DIAL, (200, 400), (1, 0)) == ()
    assert line_in_circle(DIAL, (200, 200), (1, 0), half_length=30) == (170, 200, 230, 200)
    ticks = bank_scale_ticks(DIAL)
    assert ticks[6][0] == 0 and ticks[6][1] == pytest.approx(200) and ticks[6][4] < 100 + 200 - 100
    lines, dot = aircraft_symbol(DIAL)
    assert len(lines) == 2 and dot[0] < 200 < dot[2]
    assert format_attitude(23.4, -4.4) == ("23", "−4") and format_attitude(-0.3, 0) == ("0", "0")


def test_the_dial_fits_the_instrument_and_leaves_room_for_the_digits():
    dial = horizon_dial(0, 0, 400, 400, line_height=20)
    assert dial.cx == 200 and dial.radius < 200 and dial.cy + dial.radius * 1.13 < 400 - 20
