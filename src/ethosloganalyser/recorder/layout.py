# -*- coding: utf-8 -*-
"""Where the instruments and the timeline of the flight recorder go: a plain function of the size of the page.

``recorder_layout(width, height, present, line_height)`` returns one rectangle per shown instrument and one for
the timeline at the bottom (full width). Instruments that the log has no data for are not in ``present`` and get no
rectangle; the others move up, so no empty space is left. Sizes that hold text follow the line height of the font,
so the layout fits at a Windows display scaling of 100 to 150 % (see gui/table_fit.py).

Three modes, chosen by the size of the instrument area (the page without the timeline):

* normal (at least NORMAL_MIN_SIZE): horizon in the middle, the gauges left and right of it in the order of the
  user (altitude, vertical speed, RPM/throttle, battery), radio and aircraft side by side at the bottom right;
* compact (smaller): horizon on the left, the gauges in a 2 x 2 grid next to it, radio and aircraft below;
* minimal (below COMPACT_MIN_SIZE): only the horizon and a column of numbers for the gauges.

So far only the horizon is drawn; the other instruments follow in later packages and only need to be passed in
``present``.
"""

import math
from dataclasses import dataclass

HORIZON = "horizon"
ALTITUDE = "altitude"
VERTICAL_SPEED = "vertical_speed"
RPM_THROTTLE = "rpm_throttle"
BATTERY = "battery"
RADIO = "radio"
AIRCRAFT = "aircraft"
READOUTS = "readouts"          # minimal mode: the gauges as numbers
TIMELINE = "timeline"

SIDE_GAUGES = (ALTITUDE, VERTICAL_SPEED, RPM_THROTTLE, BATTERY)   # in the order of the user
BOTTOM_INSTRUMENTS = (RADIO, AIRCRAFT)

NORMAL, COMPACT, MINIMAL = "normal", "compact", "minimal"
NORMAL_MIN_SIZE = (1100, 560)          # instrument area in pixels
COMPACT_MIN_SIZE = (640, 420)


@dataclass(frozen=True)
class Rect:
    """A rectangle in canvas pixels."""
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def center(self):
        return self.x + self.width / 2, self.y + self.height / 2

    def overlaps(self, other):
        return (self.x < other.right and other.x < self.right and self.y < other.bottom and other.y < self.bottom)

    def inside(self, other):
        return self.x >= other.x and self.y >= other.y and self.right <= other.right and self.bottom <= other.bottom


@dataclass(frozen=True)
class RecorderLayout:
    """The mode and the rectangle of every shown instrument and of the timeline."""
    mode: str
    rects: dict


def _rect(x, y, width, height):
    """Rect with whole pixels and no negative size."""
    return Rect(int(round(x)), int(round(y)), max(int(round(width)), 0), max(int(round(height)), 0))


def margin_for(line_height):
    """Space between instruments: half a line, at least 6 pixels."""
    return max(6, round(line_height * 0.5))


def timeline_height(line_height):
    """Height of the timeline: the track with the telemetry band and a row of buttons below it."""
    return round(line_height * 3.2) + 36


def recorder_mode(width, height):
    """Mode for an instrument area of width x height pixels."""
    if width >= NORMAL_MIN_SIZE[0] and height >= NORMAL_MIN_SIZE[1]:
        return NORMAL
    if width >= COMPACT_MIN_SIZE[0] and height >= COMPACT_MIN_SIZE[1]:
        return COMPACT
    return MINIMAL


def recorder_layout(width, height, present, line_height):
    """Rectangles of the recorder for a page of width x height pixels.

    present: names of the instruments the log has data for (HORIZON, SIDE_GAUGES, RADIO, AIRCRAFT); line_height:
    height of one line of the default font in pixels.
    """
    width, height = max(int(width), 0), max(int(height), 0)
    timeline = _rect(0, max(height - timeline_height(line_height), 0), width,
                     min(timeline_height(line_height), height))
    area = _rect(0, 0, width, timeline.y)
    mode = recorder_mode(area.width, area.height)
    place = {NORMAL: _normal, COMPACT: _compact, MINIMAL: _minimal}[mode]
    rects = place(area, set(present), margin_for(line_height), line_height)
    rects[TIMELINE] = timeline
    return RecorderLayout(mode=mode, rects=rects)


def _side_gauges(present):
    return [name for name in SIDE_GAUGES if name in present]


def _bottom_row(area, present, margin, share, align_right):
    """Radio and aircraft side by side at the bottom of the area. Returns (rects, height taken)."""
    shown = [name for name in BOTTOM_INSTRUMENTS if name in present]
    if not shown:
        return {}, 0
    row_height = round(area.height * share)
    box_height = row_height - margin
    box_width = min(box_height * 1.6, (area.width - (len(shown) + 1) * margin) / len(shown))
    total = len(shown) * box_width + (len(shown) - 1) * margin
    x = area.right - margin - total if align_right else area.x + (area.width - total) / 2
    rects = {}
    for name in shown:
        rects[name] = _rect(x, area.bottom - row_height, box_width, box_height)
        x += box_width + margin
    return rects, row_height


def _normal(area, present, margin, _line_height):
    """Horizon in the middle, gauges left and right of it, radio and aircraft at the bottom right."""
    rects, bottom = _bottom_row(area, present, margin, 0.34, align_right=True)
    top = _rect(area.x, area.y, area.width, area.height - bottom)
    gauges = _side_gauges(present)
    rows, columns = math.ceil(len(gauges) / 2), min(len(gauges), 2)
    gauge = min((top.height - (rows + 1) * margin) / rows, area.width * 0.24) if rows else 0
    side = 0
    if HORIZON in present:
        side = max(min(top.height - 2 * margin, area.width - columns * (gauge + margin) - 2 * margin), 0)
    group_width = side + columns * (gauge + margin) - (margin if not side and columns else 0)
    x = area.x + (area.width - group_width) / 2
    slots = []                                     # left column, then right column, top row first
    if columns >= 1:
        slots.append(x)
        x += gauge + margin
    if side:
        rects[HORIZON] = _rect(x, top.y + (top.height - side) / 2, side, side)
        x += side + margin
    if columns == 2:
        slots.append(x)
    stack_top = top.y + (top.height - rows * gauge - (rows - 1) * margin) / 2
    for index, name in enumerate(gauges):
        column_x = slots[index % 2] if len(slots) == 2 else slots[0]
        rects[name] = _rect(column_x, stack_top + (index // 2) * (gauge + margin), gauge, gauge)
    return rects


def _compact(area, present, margin, _line_height):
    """Horizon on the left, the gauges in a 2 x 2 grid next to it, radio and aircraft below."""
    rects, bottom = _bottom_row(area, present, margin, 0.30, align_right=False)
    top = _rect(area.x, area.y, area.width, area.height - bottom)
    gauges = _side_gauges(present)
    side = 0
    if HORIZON in present:
        side = max(min(top.height - 2 * margin, (area.width - 3 * margin) * (0.5 if gauges else 1.0)), 0)
    if not gauges:
        if side:
            rects[HORIZON] = _rect(area.x + (area.width - side) / 2, top.y + (top.height - side) / 2, side, side)
        return rects
    grid_x = area.x + margin + (side + margin if side else 0)
    grid_width = area.right - margin - grid_x
    rows, columns = math.ceil(len(gauges) / 2), min(len(gauges), 2)
    gauge = max(min((grid_width - (columns - 1) * margin) / columns, (top.height - (rows + 1) * margin) / rows), 0)
    if side:
        rects[HORIZON] = _rect(area.x + margin, top.y + (top.height - side) / 2, side, side)
    stack_top = top.y + (top.height - rows * gauge - (rows - 1) * margin) / 2
    for index, name in enumerate(gauges):
        rects[name] = _rect(grid_x + (index % 2) * (gauge + margin), stack_top + (index // 2) * (gauge + margin),
                            gauge, gauge)
    return rects


def _minimal(area, present, margin, line_height):
    """Only the horizon and a column of numbers for the gauges (radio and aircraft are left out)."""
    rects = {}
    readout_width = min(area.width * 0.4, line_height * 14) if _side_gauges(present) else 0
    side = 0
    if HORIZON in present:
        side = max(min(area.height - 2 * margin, area.width - 2 * margin - (readout_width + margin if readout_width
                                                                                else 0)), 0)
    group_width = side + (readout_width + (margin if side else 0) if readout_width else 0)
    x = area.x + (area.width - group_width) / 2
    if side:
        rects[HORIZON] = _rect(x, area.y + (area.height - side) / 2, side, side)
        x += side + margin
    if readout_width:
        rects[READOUTS] = _rect(x, area.y + margin, readout_width, area.height - 2 * margin)
    return rects
