# -*- coding: utf-8 -*-
"""Layout of the flight recorder (recorder/layout.py): modes, all rectangles inside, no overlap."""

import itertools

import pytest

from ethosloganalyser.recorder.layout import (AIRCRAFT, ALTITUDE, BATTERY, COMPACT, HORIZON, MINIMAL, NORMAL, RADIO,
                                              READOUTS, RPM_THROTTLE, SIDE_GAUGES, TIMELINE, VERTICAL_SPEED, Rect,
                                              recorder_layout, timeline_height)

ALL = {HORIZON, ALTITUDE, VERTICAL_SPEED, RPM_THROTTLE, BATTERY, RADIO, AIRCRAFT}
SIZES = [((1920, 1080), 16), ((1920, 1080), 24), ((1280, 720), 24), ((900, 600), 16), ((600, 400), 16),
         ((600, 400), 24)]


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
                                     {HORIZON, RADIO, AIRCRAFT}, ALL - {HORIZON}])
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
    assert recorder_layout(1280, 720, ALL, 24).mode == NORMAL
    assert recorder_layout(900, 600, ALL, 16).mode == COMPACT
    assert recorder_layout(600, 400, ALL, 16).mode == MINIMAL


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
