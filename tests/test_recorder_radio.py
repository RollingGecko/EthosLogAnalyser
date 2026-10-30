# -*- coding: utf-8 -*-
"""Geometry of the radio of the flight recorder (recorder/radio.py): the stick fields and their text lines fit
inside the rectangle at every size and font, the dot stays inside its field."""

import itertools

import pytest

from ethosloganalyser.recorder.layout import Rect
from ethosloganalyser.recorder.radio import (DOT_TRAVEL, dot_position, dot_radius, overhead, radio_parts,
                                             radio_width)

SIZES = [(130, 120), (194, 136), (260, 169), (400, 259), (462, 270), (600, 300), (200, 300)]


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("line_height", [16, 20, 24])
def test_fields_and_text_lines_stay_inside_the_radio_and_do_not_overlap(size, line_height):
    rect = Rect(30, 40, *size)
    parts = radio_parts(rect, line_height)
    boxes = {}
    for index in range(2):
        x0, y0, x1, y1 = parts.fields[index]
        boxes[f"field {index}"] = (x0, y0, x1, y1)
        boxes[f"label {index}"] = (parts.labels[index][0] - parts.text_width / 2,
                                   parts.labels[index][1] - line_height * 0.6,
                                   parts.labels[index][0] + parts.text_width / 2,
                                   parts.labels[index][1] + line_height * 0.6)
        boxes[f"value {index}"] = (parts.values[index][0] - parts.text_width / 2,
                                   parts.values[index][1] - line_height * 0.6,
                                   parts.values[index][0] + parts.text_width / 2,
                                   parts.values[index][1] + line_height * 0.6)
    for name, (x0, y0, x1, y1) in boxes.items():
        if name.startswith("field"):
            assert rect.x <= x0 and rect.y <= y0 and x1 <= rect.right + 0.01 and y1 <= rect.bottom + 0.01, name
            assert x1 - x0 == pytest.approx(y1 - y0)                               # square
    for (name_a, a), (name_b, b) in itertools.combinations(boxes.items(), 2):
        separate = a[2] <= b[0] + 0.01 or b[2] <= a[0] + 0.01 or a[3] <= b[1] + 0.01 or b[3] <= a[1] + 0.01
        assert separate, (name_a, name_b)
    assert parts.fields[0][2] < parts.fields[1][0]                                  # left field, then right field
    assert parts.values[0][1] + line_height * 0.5 <= rect.bottom + 0.01              # the numbers are inside


def test_the_width_for_a_height_holds_exactly_two_fields():
    for line_height in (16, 24):
        height = 220
        parts = radio_parts(Rect(0, 0, radio_width(height, line_height), height), line_height)
        assert parts.side == pytest.approx(height - overhead(line_height))
    assert radio_width(300, 16) > radio_width(200, 16) > radio_width(100, 16)


def test_a_wide_rectangle_is_limited_by_its_height_and_a_narrow_one_by_its_width():
    tall = radio_parts(Rect(0, 0, 200, 600), 16)
    wide = radio_parts(Rect(0, 0, 900, 150), 16)
    assert tall.side < 100 and wide.side == pytest.approx(150 - overhead(16))
    assert wide.fields[0][0] > 100 and wide.fields[1][2] < 800                      # the pair is centred


def test_the_dot_stays_inside_its_field():
    field = (100.0, 50.0, 200.0, 150.0)
    assert dot_position(field, 0, 0) == (150, 100)
    assert dot_position(field, 1, 1) == (150 + 50 * DOT_TRAVEL, 100 - 50 * DOT_TRAVEL)    # right and up
    assert dot_position(field, -1, -1) == (150 - 50 * DOT_TRAVEL, 100 + 50 * DOT_TRAVEL)
    size = dot_radius(field)
    for x, y in itertools.product((-1, 0, 1), repeat=2):
        cx, cy = dot_position(field, x, y)
        assert field[0] <= cx - size and cx + size <= field[2] and field[1] <= cy - size and cy + size <= field[3]
    assert dot_radius((0, 0, 20, 20)) == 3
