# -*- coding: utf-8 -*-
"""Layout of the flight recorder (recorder/layout.py): modes, thresholds that follow the font, all rectangles
inside, no overlap."""

import itertools

import pytest

from ethosloganalyser.recorder.dials import panel_parts
from ethosloganalyser.recorder.layout import (AIRCRAFT, ALTITUDE, BATTERY, COMPACT, COMPACT_MIN_SIZE, HORIZON,
                                              MINIMAL, NORMAL, NORMAL_MIN_SIZE, RADIO, READOUTS, RPM_THROTTLE,
                                              SIDE_GAUGES, TIMELINE, VERTICAL_SPEED, Rect, font_scale, min_size,
                                              recorder_layout, recorder_mode, timeline_height)

ALL = {HORIZON, ALTITUDE, VERTICAL_SPEED, RPM_THROTTLE, BATTERY, RADIO, AIRCRAFT}
FONTS = (16, 20, 24)                     # line heights at a Windows display scaling of 100, 125 and 150 %
SIZES = [(size, line_height) for size in [(1920, 1080), (1280, 720), (900, 600), (600, 400)] for line_height in FONTS]


def _check(layout, width, height):
    """Every rectangle lies inside the page, has a size and overlaps no other one."""
    page = Rect(0, 0, width, height)
    for name, rect in layout.rects.items():
        assert rect.inside(page), (name, rect)
        assert rect.width > 0 and rect.height > 0, (name, rect)
    for (name_a, a), (name_b, b) in itertools.combinations(layout.rects.items(), 2):
        assert not a.overlaps(b), (name_a, a, name_b, b)


@pytest.mark.parametrize("size, line_height", SIZES)
@pytest.mark.parametrize("present", [{HORIZON}, ALL, {HORIZON, ALTITUDE}, {ALTITUDE, BATTERY}, set(),
                                     {HORIZON, RADIO, AIRCRAFT}, ALL - {HORIZON}, ALL - {AIRCRAFT}, {RADIO},
                                     {HORIZON, RADIO}, ALL - {RADIO}, {AIRCRAFT}, ALL - {RADIO, AIRCRAFT}])
def test_no_rectangle_overlaps_another_or_leaves_the_page(size, line_height, present):
    layout = recorder_layout(*size, present, line_height)
    _check(layout, *size)
    assert TIMELINE in layout.rects
    shown = set(layout.rects) - {TIMELINE, READOUTS}
    assert shown <= present                                         # nothing that the log has no data for


def test_the_timeline_takes_the_full_width_at_the_bottom_and_grows_with_the_font():
    for line_height in (16, 20, 24):
        timeline = recorder_layout(1920, 1080, {HORIZON}, line_height).rects[TIMELINE]
        assert (timeline.x, timeline.width, timeline.bottom) == (0, 1920, 1080)
        assert timeline.height == timeline_height(line_height)
    assert timeline_height(24) > timeline_height(16)


def test_modes_follow_the_size():
    assert recorder_layout(1920, 1080, ALL, 16).mode == NORMAL
    assert recorder_layout(1280, 720, ALL, 16).mode == NORMAL
    assert recorder_layout(900, 600, ALL, 16).mode == COMPACT
    assert recorder_layout(600, 400, ALL, 16).mode == MINIMAL


@pytest.mark.parametrize("size, modes", [
    ((1920, 1080), (NORMAL, NORMAL, NORMAL)), ((1600, 900), (NORMAL, NORMAL, COMPACT)),
    ((1280, 720), (NORMAL, COMPACT, MINIMAL)), ((900, 600), (COMPACT, MINIMAL, MINIMAL)),
    ((600, 400), (MINIMAL, MINIMAL, MINIMAL))])
def test_a_larger_font_switches_to_compact_and_minimal_earlier(size, modes):
    assert tuple(recorder_layout(*size, ALL, line_height).mode for line_height in FONTS) == modes


def test_the_thresholds_at_100_percent_stay_as_they_were():
    for line_height in (12, 15, 16):                         # Segoe UI 9 pt at 100 %: 15 pixels
        assert font_scale(line_height) == 1.0
        assert min_size(NORMAL, line_height) == NORMAL_MIN_SIZE and min_size(COMPACT, line_height) == COMPACT_MIN_SIZE
    assert min_size(NORMAL, 24) == (1650, 840) and min_size(COMPACT, 20) == (800, 525)
    assert recorder_mode(1100, 560) == NORMAL and recorder_mode(1099, 560) == COMPACT
    assert recorder_mode(640, 420) == COMPACT and recorder_mode(640, 419) == MINIMAL


@pytest.mark.parametrize("line_height", (15,) + FONTS)
@pytest.mark.parametrize("present", [ALL, ALL - {RADIO, AIRCRAFT}, ALL - {RADIO}])
def test_the_dials_keep_their_size_in_lines_at_every_font(line_height, present):
    """Normal and compact are used only while every dial has a radius of about two lines of text (as at the
    thresholds at 100 %), so the numbers stay readable at 125 and 150 %."""
    for width in range(500, 2000, 50):
        for height in range(400, 1200, 25):
            layout = recorder_layout(width, height, present, line_height)
            if layout.mode == MINIMAL:
                continue
            for name in SIDE_GAUGES:
                parts = panel_parts(layout.rects[name], line_height, True, name == RPM_THROTTLE)
                assert parts.dial.radius >= 1.9 * line_height, (width, height, name, parts.dial.radius)


def test_normal_mode_puts_the_horizon_in_the_middle_with_the_gauges_left_and_right():
    rects = recorder_layout(1920, 1080, ALL, 16).rects
    horizon = rects[HORIZON]
    assert horizon.width == horizon.height                          # square
    assert abs(horizon.center[0] - 960) <= 1
    assert rects[ALTITUDE].right <= horizon.x and rects[RPM_THROTTLE].right <= horizon.x
    assert rects[VERTICAL_SPEED].x >= horizon.right and rects[BATTERY].x >= horizon.right
    assert rects[ALTITUDE].y < rects[RPM_THROTTLE].y and rects[VERTICAL_SPEED].y < rects[BATTERY].y
    assert rects[RADIO].right <= rects[AIRCRAFT].x and rects[AIRCRAFT].right > 1500   # bottom right, side by side
    for gauge in SIDE_GAUGES:
        assert rects[gauge].width < horizon.width                    # the horizon is the largest instrument


def test_the_horizon_alone_uses_the_space_of_the_missing_instruments():
    alone = recorder_layout(1920, 1080, {HORIZON}, 16).rects[HORIZON]
    with_all = recorder_layout(1920, 1080, ALL, 16).rects[HORIZON]
    assert alone.width > with_all.width
    assert abs(alone.center[0] - 960) <= 1


def test_missing_gauges_leave_no_gap():
    rects = recorder_layout(1920, 1080, {HORIZON, ALTITUDE, BATTERY}, 16).rects
    assert rects[ALTITUDE].right <= rects[HORIZON].x and rects[BATTERY].x >= rects[HORIZON].right
    assert rects[ALTITUDE].y == rects[BATTERY].y                     # both in the first row


def test_compact_mode_puts_the_gauges_in_a_grid_next_to_the_horizon():
    rects = recorder_layout(900, 600, ALL, 16).rects
    horizon = rects[HORIZON]
    assert horizon.x < rects[ALTITUDE].x and all(rects[name].x >= horizon.right for name in SIDE_GAUGES)
    assert rects[ALTITUDE].y == rects[VERTICAL_SPEED].y < rects[RPM_THROTTLE].y == rects[BATTERY].y
    assert rects[RADIO].y >= horizon.bottom and rects[AIRCRAFT].y >= horizon.bottom


def test_minimal_mode_shows_the_horizon_and_numbers_only():
    rects = recorder_layout(600, 400, ALL, 16).rects
    assert set(rects) == {HORIZON, READOUTS, TIMELINE}
    assert set(recorder_layout(600, 400, {HORIZON}, 16).rects) == {HORIZON, TIMELINE}


def test_a_page_too_small_for_anything_but_the_timeline():
    layout = recorder_layout(300, 60, {HORIZON}, 24)
    assert layout.rects[TIMELINE].height == 60 and HORIZON not in layout.rects


@pytest.mark.parametrize("size, line_height", SIZES)
def test_the_radio_sits_in_the_bottom_row_with_and_without_the_aircraft(size, line_height):
    layout = recorder_layout(*size, ALL, line_height)
    without = recorder_layout(*size, ALL - {RADIO}, line_height)
    if layout.mode == MINIMAL:
        assert RADIO not in layout.rects and RADIO not in without.rects          # the minimal layout has no radio
        return
    rects = layout.rects
    assert RADIO in rects and rects[RADIO].y >= rects[HORIZON].bottom - 1 and rects[RADIO].right <= size[0]
    if layout.mode == NORMAL:
        assert rects[RADIO].x > size[0] / 2 and rects[AIRCRAFT].x >= rects[RADIO].right or rects[AIRCRAFT].right <= rects[RADIO].x
    assert RADIO not in without.rects
    assert recorder_layout(*size, ALL - {AIRCRAFT}, line_height).rects[RADIO].width > 0


@pytest.mark.parametrize("size, line_height, smallest", [
    ((1920, 1080), 16, 100), ((1920, 1080), 20, 90), ((1920, 1080), 24, 80), ((1280, 720), 16, 55),
    ((1280, 720), 20, 50)])
def test_the_gauges_stay_readable_with_the_radio(size, line_height, smallest):
    """The radio takes room from the gauges; their dials must keep a radius that holds the numbers."""
    rects = recorder_layout(*size, ALL, line_height).rects
    assert rects[RADIO].width > 0
    for name in SIDE_GAUGES:
        parts = panel_parts(rects[name], line_height, True, name in (ALTITUDE, VERTICAL_SPEED, BATTERY, RPM_THROTTLE))
        assert parts.dial is not None and parts.dial.radius >= smallest, (name, parts.dial.radius)


def test_without_the_radio_the_gauges_move_up_and_the_layout_stays_valid():
    with_radio = recorder_layout(1920, 1080, {HORIZON, ALTITUDE, BATTERY, RADIO}, 16)
    without = recorder_layout(1920, 1080, {HORIZON, ALTITUDE, BATTERY}, 16)
    assert RADIO not in without.rects
    assert without.rects[HORIZON].width >= with_radio.rects[HORIZON].width
    assert without.rects[ALTITUDE].height >= with_radio.rects[ALTITUDE].height


@pytest.mark.parametrize("size, line_height", SIZES)
def test_the_aircraft_sits_next_to_the_radio_and_alone_in_its_place(size, line_height):
    layout = recorder_layout(*size, ALL, line_height)
    if layout.mode == MINIMAL:
        assert AIRCRAFT not in layout.rects                       # the minimal layout has no aircraft
        return
    rects = layout.rects
    aircraft, radio = rects[AIRCRAFT], rects[RADIO]
    assert aircraft.y == radio.y and aircraft.height == radio.height and aircraft.y >= rects[HORIZON].bottom - 1
    assert aircraft.x >= radio.right                               # the aircraft to the right of the radio
    alone = recorder_layout(*size, ALL - {RADIO}, line_height).rects[AIRCRAFT]
    assert alone.width >= aircraft.width > 0
    assert aircraft.width <= aircraft.height * 1.6 + 1
