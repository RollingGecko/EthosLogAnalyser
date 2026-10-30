# -*- coding: utf-8 -*-
"""Geometry of the recorder gauges (recorder/dials.py): nice scales, pointer angles with limits, ticks, bars and
the parts of a gauge."""

import itertools
import math

import pytest

from ethosloganalyser.recorder.dials import (ARC, CENTRED_ARC, Dial, bar_fill, fraction, label_divisor, label_text,
                                             nice_ceiling, panel_parts, point_on_dial, pointer_angle,
                                             pointer_polygon, scale_for, scale_labels, scale_ticks, tick_step,
                                             vertical_speed_scale)
from ethosloganalyser.recorder.layout import Rect


@pytest.mark.parametrize("value, minimum, expected", [
    (200.7, 10, 250), (151.8, 10, 200), (22.4, 10, 25), (3, 10, 10), (0, 10, 10), (float("nan"), 10, 10),
    (106000, 1000, 120000), (84800, 1000, 100000), (121.4, 5, 150), (117.9, 5, 120), (4.3, 5, 5), (250, 10, 250)])
def test_nice_ceiling_is_the_next_nice_value_at_or_above_the_largest_value(value, minimum, expected):
    assert nice_ceiling(value, minimum) == expected


@pytest.mark.parametrize("full, step", [(250, 50), (200, 50), (120, 20), (150, 25), (25, 5), (10, 2),
                                        (120000, 20000), (15, 2.5), (300, 50)])
def test_tick_step_divides_the_scale_into_four_to_eight_parts(full, step):
    assert tick_step(full, (4, 8)) == step
    assert 4 <= full / step <= 8 and float(full / step).is_integer()


def test_scales_of_small_and_large_models():
    park_flyer, jet = scale_for(22.4, 10), scale_for(200.7, 10)
    assert (park_flyer.full, park_flyer.step) == (25, 5) and (jet.full, jet.step) == (250, 50)
    assert jet.major_values() == [0, 50, 100, 150, 200, 250]
    assert jet.minor_values() == [25, 75, 125, 175, 225]


@pytest.mark.parametrize("largest, full", [(0, 5), (2.4, 5), (5, 5), (6.2, 10), (10, 10), (14, 20), (20, 20),
                                           (27, 30)])
def test_the_vertical_speed_scale_is_5_10_or_20_and_centred_on_zero(largest, full):
    scale = vertical_speed_scale(largest)
    assert scale.full == full and scale.centred and scale.low == -full
    assert scale.major_values()[0] == -full and scale.major_values()[-1] == full and 0 in scale.major_values()


def test_pointer_angle_stops_at_the_ends_of_the_scale():
    scale = scale_for(200, 10)
    assert pointer_angle(0, scale, ARC) == ARC.zero_angle == -135
    assert pointer_angle(200, scale, ARC) == 135
    assert pointer_angle(100, scale, ARC) == 0                     # half scale at 12 o'clock
    assert pointer_angle(500, scale, ARC) == 135 and pointer_angle(-30, scale, ARC) == -135
    assert pointer_angle(None, scale, ARC) == -135 and pointer_angle(float("nan"), scale, ARC) == -135


def test_the_vertical_speed_pointer_is_at_9_oclock_for_zero_and_symmetric():
    scale = vertical_speed_scale(10)
    zero = pointer_angle(0, scale, CENTRED_ARC)
    assert zero == -90                                             # 9 o'clock
    for value in (2.4, 5, 10):
        climb, sink = pointer_angle(value, scale, CENTRED_ARC), pointer_angle(-value, scale, CENTRED_ARC)
        assert climb - zero == pytest.approx(zero - sink) and climb > zero
    assert pointer_angle(25, scale, CENTRED_ARC) == pointer_angle(10, scale, CENTRED_ARC)
    assert pointer_angle(-25, scale, CENTRED_ARC) == pointer_angle(-10, scale, CENTRED_ARC)
    assert pointer_angle(None, scale, CENTRED_ARC) == zero
    dial = Dial(100, 100, 50)
    x, y = point_on_dial(dial, pointer_angle(5, scale, CENTRED_ARC), 40)
    assert y < 100                                                 # climbing points up


def test_ticks_and_labels_lie_on_the_dial():
    dial, scale = Dial(200, 200, 100), scale_for(250, 10)
    ticks = scale_ticks(dial, scale, ARC)
    assert [tick[0] for tick in ticks if tick[1]] == scale.major_values()
    for _value, _labelled, x0, y0, x1, y1 in ticks:
        assert math.hypot(x0 - 200, y0 - 200) < math.hypot(x1 - 200, y1 - 200) <= 100.01
    for _value, x, y in scale_labels(dial, scale, ARC):
        assert math.hypot(x - 200, y - 200) < 80


def test_labels_in_thousands_and_without_sign_on_a_centred_scale():
    rpm = scale_for(106000, 1000)
    assert label_divisor(rpm) == 1000 and label_text(40000, rpm) == "40"
    assert label_divisor(scale_for(250, 10)) == 1 and label_text(250, scale_for(250, 10)) == "250"
    vertical_speed = vertical_speed_scale(10)
    assert label_text(-5, vertical_speed) == "5" and label_text(0, vertical_speed) == "0"
    assert label_text(2.5, scale_for(15, 5)) == "2,5"                # tests start in German


def test_pointer_polygon_points_from_the_centre_to_the_scale():
    dial = Dial(0, 0, 100)
    polygon = pointer_polygon(dial, 0)                             # 12 o'clock: tip straight up
    assert polygon[0] == pytest.approx(0) and polygon[1] == pytest.approx(-78)
    assert polygon[5] > 0                                          # the tail is below the centre


def test_bar_fill_grows_from_the_left_and_stops_at_the_ends():
    box = (10, 5, 110, 15)
    assert bar_fill(box, 0) == () and bar_fill(box, -1) == ()
    assert bar_fill(box, 0.45) == (10, 5, 55, 15)
    assert bar_fill(box, 2) == (10, 5, 110, 15)
    assert fraction(48, 40, 56) == 0.5 and fraction(60, 40, 56) == 1 and fraction(48, 50, 50) == 0


@pytest.mark.parametrize("size", [(160, 160), (200, 200), (380, 380), (160, 220)])
@pytest.mark.parametrize("line_height", [16, 20, 24])
@pytest.mark.parametrize("has_dial, has_bar", [(True, True), (True, False), (False, True)])
def test_the_parts_of_a_gauge_stay_inside_it_and_do_not_overlap(size, line_height, has_dial, has_bar):
    rect = Rect(10, 20, *size)
    parts = panel_parts(rect, line_height, has_dial, has_bar)
    assert (parts.dial is not None) == has_dial and (parts.bar_box is not None) == has_bar
    boxes = {"title": (rect.x, rect.y, rect.right, parts.title[1] + line_height / 2)}
    if has_dial:
        dial = parts.dial
        boxes["dial"] = (dial.cx - dial.radius, dial.cy - dial.radius, dial.cx + dial.radius, dial.cy + dial.radius)
        boxes["number"] = (rect.x, parts.value_line[1] - line_height / 2, rect.right, parts.value_line[1]
                           + line_height / 2)
    if has_bar:
        boxes["bar label"] = (rect.x, parts.bar_label_line[2] - line_height / 2, rect.right,
                              parts.bar_label_line[2] + line_height / 2)
        boxes["bar"] = parts.bar_box
    for name, (x0, y0, x1, y1) in boxes.items():
        assert rect.x <= x0 and rect.y <= y0 and x1 <= rect.right + 0.01 and y1 <= rect.bottom + 0.01, name
    for (name_a, a), (name_b, b) in itertools.combinations(boxes.items(), 2):
        assert a[3] <= b[1] + 0.01 or b[3] <= a[1] + 0.01, (name_a, name_b)    # one above the other


def test_a_gauge_with_a_dial_only_gets_a_larger_dial():
    rect = Rect(0, 0, 300, 300)
    assert panel_parts(rect, 16, True, False).dial.radius > panel_parts(rect, 16, True, True).dial.radius
