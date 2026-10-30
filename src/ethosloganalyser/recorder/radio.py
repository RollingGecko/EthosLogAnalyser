# -*- coding: utf-8 -*-
"""Geometry of the radio (transmitter) of the flight recorder as plain functions (canvas pixels, y down).

The radio has two stick fields side by side: a square with a cross hair and a dot at the stick position. Below
each field a line names the two axes of the stick ("Throttle / Rudder") and a line shows their values in percent.
The parts follow the line height of the font, so they fit at a Windows display scaling of 100 to 150 %.
"""

from dataclasses import dataclass

LABEL_LINES = 1.2             # height of the line naming the axes, in lines of text
VALUE_LINES = 1.2             # height of the line with the values
DOT_TRAVEL = 0.9              # the dot reaches this share of the half width of its field at full deflection
MIN_SIDE = 2.0


def padding(line_height):
    """Space between the rectangle of the radio and its content."""
    return max(4.0, line_height * 0.3)


def gap(line_height):
    """Space between the two stick fields."""
    return max(6.0, line_height * 0.5)


def text_height(line_height):
    """Height of the two lines of text below the fields."""
    return line_height * (LABEL_LINES + VALUE_LINES)


def overhead(line_height):
    """Height of the radio without the stick fields: padding above and below and the two lines of text."""
    return 2 * padding(line_height) + text_height(line_height)


def radio_width(box_height, line_height):
    """Width at which the two fields fill a radio of box_height pixels (the fields are as high as it allows)."""
    side = max(box_height - overhead(line_height), 0.0)
    return 2 * side + gap(line_height) + 2 * padding(line_height)


@dataclass(frozen=True)
class RadioParts:
    """Where the parts of the radio go inside its rectangle."""
    side: float                   # side of one stick field
    fields: tuple                 # two (x0, y0, x1, y1), left field first
    labels: tuple                 # two (x, y) centres of the line naming the axes
    values: tuple                 # two (x, y) centres of the line with the values
    text_width: float             # width a line of text may take


def radio_parts(rect, line_height):
    """The parts of the radio in rect (anything with x, y, width, height) at a font of line_height pixels."""
    pad, between = padding(line_height), gap(line_height)
    side = max(min((rect.width - 2 * pad - between) / 2, rect.height - overhead(line_height)), MIN_SIDE)
    content_width = 2 * side + between
    left = rect.x + (rect.width - content_width) / 2
    top = rect.y + (rect.height - side - text_height(line_height)) / 2
    fields, labels, values = [], [], []
    for index in range(2):
        x0 = left + index * (side + between)
        fields.append((x0, top, x0 + side, top + side))
        labels.append((x0 + side / 2, top + side + line_height * LABEL_LINES / 2))
        values.append((x0 + side / 2, top + side + line_height * (LABEL_LINES + VALUE_LINES / 2)))
    return RadioParts(side=side, fields=tuple(fields), labels=tuple(labels), values=tuple(values),
                      text_width=side + between * 0.9)


def dot_position(field, x, y):
    """Pixel of the dot in a field for a stick position x (right = +1) and y (up = +1), both -1 .. +1."""
    x0, y0, x1, y1 = field
    travel = (x1 - x0) / 2 * DOT_TRAVEL
    return (x0 + x1) / 2 + x * travel, (y0 + y1) / 2 - y * travel


def dot_radius(field):
    """Radius of the dot: a few percent of the field, at least 3 pixels."""
    return max(3.0, (field[2] - field[0]) * 0.045)
