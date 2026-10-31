# -*- coding: utf-8 -*-
"""Where the instruments and the timeline of the flight recorder go: a plain function of the size of the page.

``recorder_layout(width, height, present, line_height)`` returns one rectangle per shown instrument and one for
the timeline at the bottom (full width). Instruments that the log has no data for are not in ``present`` and get no
rectangle; the others move up, so no empty space is left. Sizes that hold text follow the line height of the font,
so the layout fits at a Windows display scaling of 100 to 150 % (see gui/table_fit.py).

Three modes; the first one whose instruments keep their least sizes is used:

* normal (instrument area at least NORMAL_MIN_SIZE): horizon in the middle, the gauges left and right of it in the
  order of the user (altitude, vertical speed, RPM/throttle, battery), radio and aircraft side by side at the
  bottom right;
* compact: horizon on the left, the gauges in a 2 x 2 grid next to it (or in one row, if two rows do not fit
  above the radio), radio and aircraft below; the horizon gets what the gauges leave, also less than half the
  width;
* minimal (if not even the compact layout fits): only the horizon and a column of numbers for the gauges.

The least sizes are counted in lines of text, so the same rules hold at a Windows display scaling of 100 to 150 %:
a dial keeps a radius of DIAL_MIN_LINES lines (plus the texts of its gauge), a stick field of the radio a side of
STICK_MIN_LINES lines (plus its texts), the horizon HORIZON_MIN_LINES lines. A larger font therefore takes room
from the horizon first instead of dropping the gauges, the radio and the aircraft.

The bottom row (radio, aircraft) takes ROW_SHARE of the area, or only as much as the stick fields need if the
gauges would not fit otherwise. The radio is as wide as its two stick fields need, the aircraft box is 1.6 times
as wide as high.
"""

import math
from dataclasses import dataclass

from .dials import panel_parts
from .radio import overhead, radio_parts, radio_width

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
NORMAL_MIN_SIZE = (1100, 560)          # instrument area in pixels from which the normal layout is tried
ROW_SHARE = 0.28                       # height of the bottom row (radio, aircraft) in the area
# least radius of a dial, in lines of text; 1.35 keeps the normal layout of a maximized 1920 x 1080 window at
# 150 % (radius 39 px at a line of 28 px), which the owner accepted, and still keeps the dials readable
DIAL_MIN_LINES = 1.35
STICK_MIN_LINES = 3.0                  # least side of a stick field of the radio, in lines of text
HORIZON_MIN_LINES = 8.0                # least side of the horizon, in lines of text
AIRCRAFT_ASPECT = 1.6                  # width / height of the box of the aircraft


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


def least_row_height(line_height, margin):
    """Height of the bottom row whose stick fields have a side of STICK_MIN_LINES lines."""
    return math.ceil(overhead(line_height) + STICK_MIN_LINES * line_height) + margin


def least_gauge_side(line_height):
    """Side of the smallest square gauge (with a bar) whose dial has a radius of DIAL_MIN_LINES lines."""
    reference = 1000                                    # large enough that the height limits the dial
    texts = reference - 2 * panel_parts(Rect(0, 0, reference, reference), line_height, True, True).dial.radius
    return math.ceil(2 * DIAL_MIN_LINES * line_height + texts) + 1


def fits(rects, present, line_height):
    """True if every instrument of present has a rectangle in rects with its least size (see the module text)."""
    for name in (HORIZON,) + SIDE_GAUGES + BOTTOM_INSTRUMENTS:
        if name not in present:
            continue
        rect = rects.get(name)
        if rect is None or rect.width <= 0 or rect.height <= 0:
            return False
        if name == HORIZON:
            ok = min(rect.width, rect.height) >= HORIZON_MIN_LINES * line_height
        elif name == RADIO:
            ok = radio_parts(rect, line_height).side >= STICK_MIN_LINES * line_height
        elif name == AIRCRAFT:
            ok = min(rect.width, rect.height) >= STICK_MIN_LINES * line_height
        else:                                           # a gauge, counted with a bar below the dial
            ok = panel_parts(rect, line_height, True, True).dial.radius >= DIAL_MIN_LINES * line_height
        if not ok:
            return False
    return True


def _candidates(area, present, margin, line_height):
    """The layouts to try, in the order of preference: (mode, rects)."""
    if area.width >= NORMAL_MIN_SIZE[0] and area.height >= NORMAL_MIN_SIZE[1]:
        yield NORMAL, _normal(area, present, margin, line_height, round(area.height * ROW_SHARE))
    count = len(_side_gauges(present))
    shapes = [(math.ceil(count / 2), min(count, 2))]
    if count > 2:
        shapes.append((1, count))                       # one row of gauges, if two do not fit above the radio
    least_row = least_row_height(line_height, margin)
    row_heights = [max(round(area.height * ROW_SHARE), least_row)]
    if least_row < row_heights[0]:
        row_heights.append(least_row)
    for shape in shapes:
        for row_height in row_heights:
            yield COMPACT, _compact(area, present, margin, line_height, row_height, shape)


def _place(area, present, line_height):
    """Mode and rectangles of the instruments in the instrument area."""
    margin = margin_for(line_height)
    for mode, rects in _candidates(area, present, margin, line_height):
        if fits(rects, present, line_height):
            return mode, rects
    return MINIMAL, _minimal(area, present, margin, line_height)


def recorder_mode(width, height, present, line_height):
    """Mode for an instrument area of width x height pixels with the instruments of present."""
    return _place(_rect(0, 0, width, height), set(present), line_height)[0]


def recorder_layout(width, height, present, line_height):
    """Rectangles of the recorder for a page of width x height pixels.

    present: names of the instruments the log has data for (HORIZON, SIDE_GAUGES, RADIO, AIRCRAFT); line_height:
    height of one line of the default font in pixels.
    """
    width, height = max(int(width), 0), max(int(height), 0)
    timeline = _rect(0, max(height - timeline_height(line_height), 0), width,
                     min(timeline_height(line_height), height))
    area = _rect(0, 0, width, timeline.y)
    mode, rects = _place(area, set(present), line_height)
    rects[TIMELINE] = timeline
    return RecorderLayout(mode=mode, rects=rects)


def _side_gauges(present):
    return [name for name in SIDE_GAUGES if name in present]


def _bottom_row(area, present, margin, row_height, align_right, line_height):
    """Radio and aircraft side by side at the bottom of the area. Returns (rects, height taken)."""
    shown = [name for name in BOTTOM_INSTRUMENTS if name in present]
    if not shown:
        return {}, 0
    box_height = row_height - margin
    room = (area.width - (len(shown) + 1) * margin) / len(shown)
    natural = {RADIO: radio_width(box_height, line_height), AIRCRAFT: box_height * AIRCRAFT_ASPECT}
    widths = [min(natural[name], room) for name in shown]
    total = sum(widths) + (len(shown) - 1) * margin
    x = area.right - margin - total if align_right else area.x + (area.width - total) / 2
    rects = {}
    for name, width in zip(shown, widths):
        rects[name] = _rect(x, area.bottom - row_height, width, box_height)
        x += width + margin
    return rects, row_height


def _normal(area, present, margin, line_height, row_height):
    """Horizon in the middle, gauges left and right of it, radio and aircraft at the bottom right."""
    rects, bottom = _bottom_row(area, present, margin, row_height, True, line_height)
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


def _compact(area, present, margin, line_height, row_height, shape):
    """Horizon on the left, the gauges in a grid of shape (rows, columns) next to it, radio and aircraft below.

    The horizon takes at most half the width, less if the gauges need more for their least size.
    """
    rects, bottom = _bottom_row(area, present, margin, row_height, False, line_height)
    top = _rect(area.x, area.y, area.width, area.height - bottom)
    gauges = _side_gauges(present)
    rows, columns = shape
    side = 0
    if HORIZON in present:
        side = top.height - 2 * margin
        if gauges:
            grid_least = columns * least_gauge_side(line_height) + (columns - 1) * margin
            side = min(side, (area.width - 3 * margin) / 2, area.width - 3 * margin - grid_least)
        side = max(min(side, area.width - 3 * margin), 0)
    if not gauges:
        if side:
            rects[HORIZON] = _rect(area.x + (area.width - side) / 2, top.y + (top.height - side) / 2, side, side)
        return rects
    grid_x = area.x + margin + (side + margin if side else 0)
    grid_width = area.right - margin - grid_x
    gauge = max(min((grid_width - (columns - 1) * margin) / columns, (top.height - (rows + 1) * margin) / rows), 0)
    if side:
        rects[HORIZON] = _rect(area.x + margin, top.y + (top.height - side) / 2, side, side)
    stack_top = top.y + (top.height - rows * gauge - (rows - 1) * margin) / 2
    for index, name in enumerate(gauges):
        row, column = divmod(index, columns)
        rects[name] = _rect(grid_x + column * (gauge + margin), stack_top + row * (gauge + margin), gauge, gauge)
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
