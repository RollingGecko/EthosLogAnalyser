# -*- coding: utf-8 -*-
"""Geometry of the recorder instruments as plain functions (canvas pixels, y pointing down).

The artificial horizon is a round window in a square instrument: sky above, ground below, a horizon line that
turns with the bank and moves with the pitch, a pitch ladder every 10 degrees and a bank pointer that moves over a
fixed scale at the top. The aircraft symbol in the middle is fixed. Angles follow the cockpit convention of
``recorder.flight_track.displayed_attitude``: bank > 0 = right wing down, pitch > 0 = nose up. Everything is
computed with sine and cosine, so inverted flight (|bank| > 90) and a jump across +/-180 degrees need no special
case.
"""

import math
from dataclasses import dataclass, field

CIRCLE_POINTS = 72                         # corners of the polygon that stands for the round window
PITCH_STEP_DEG = 10                        # one ladder line every 10 degrees
PITCH_VISIBLE_DEG = 30                     # ladder lines up to 30 degrees from the current pitch are shown
DEGREES_PER_RADIUS = 30                    # the radius of the window spans 30 degrees of pitch
LADDER_SLOTS = 2 * PITCH_VISIBLE_DEG // PITCH_STEP_DEG + 1   # most ladder lines that can be visible at once
BANK_SCALE_DEG = (-90, -60, -45, -30, -20, -10, 0, 10, 20, 30, 45, 60, 90)
LABEL_SPACE = 1.7                          # lines of text below the window (bank and pitch in digits)


@dataclass(frozen=True)
class Dial:
    """The round window of the horizon: centre and radius in pixels."""
    cx: float
    cy: float
    radius: float


@dataclass
class LadderLine:
    """One line of the pitch ladder: its pitch, the two ends and the positions of its two labels."""
    pitch: int
    line: tuple
    labels: tuple


@dataclass
class HorizonShape:
    """Everything that moves on the horizon for one attitude."""
    sky: list                                   # flat [x0, y0, x1, y1, ...]; empty if no sky is visible
    ground: list                                # the same for the ground
    horizon_line: tuple                         # (x0, y0, x1, y1) or () if the horizon is outside the window
    ladder: list = field(default_factory=list)  # LadderLine, at most LADDER_SLOTS
    bank_pointer: list = field(default_factory=list)   # triangle [x0, y0, x1, y1, x2, y2]


def horizon_dial(x, y, width, height, line_height):
    """The round window inside the instrument rectangle, leaving room for the digits below it."""
    label_height = line_height * LABEL_SPACE
    radius = max(min(width, height - label_height) / 2 * 0.86, 1.0)
    return Dial(cx=x + width / 2, cy=y + (height - label_height) / 2, radius=radius)


def _directions(bank_deg):
    """(along, up): unit vector along the horizon line to its right end, and the one pointing into the sky."""
    angle = math.radians(bank_deg)
    return (math.cos(angle), -math.sin(angle)), (-math.sin(angle), -math.cos(angle))


def circle_polygon(dial, points=CIRCLE_POINTS):
    """Corners of the round window, clockwise on the screen."""
    return [(dial.cx + dial.radius * math.cos(2 * math.pi * k / points),
             dial.cy + dial.radius * math.sin(2 * math.pi * k / points)) for k in range(points)]


def clip_half_plane(polygon, point, normal):
    """The part of a convex polygon on the side of a line (through point) that normal points to."""
    def side(corner):
        return (corner[0] - point[0]) * normal[0] + (corner[1] - point[1]) * normal[1]

    clipped = []
    for index, current in enumerate(polygon):
        following = polygon[(index + 1) % len(polygon)]
        current_side, following_side = side(current), side(following)
        if current_side >= 0:
            clipped.append(current)
        if (current_side >= 0) != (following_side >= 0):
            share = current_side / (current_side - following_side)
            clipped.append((current[0] + share * (following[0] - current[0]),
                            current[1] + share * (following[1] - current[1])))
    return clipped


def line_in_circle(dial, point, along, half_length=None):
    """The segment of the line through point (direction along) inside the window, or () if it misses it. With
    half_length, the segment is also limited to that distance from point."""
    offset = (point[0] - dial.cx, point[1] - dial.cy)
    middle = -(offset[0] * along[0] + offset[1] * along[1])         # parameter of the point nearest the centre
    distance_sq = offset[0] ** 2 + offset[1] ** 2 - middle ** 2
    if distance_sq >= dial.radius ** 2:
        return ()
    reach = math.sqrt(dial.radius ** 2 - distance_sq)
    low, high = middle - reach, middle + reach
    if half_length is not None:
        low, high = max(low, -half_length), min(high, half_length)
        if low >= high:
            return ()
    return (point[0] + low * along[0], point[1] + low * along[1], point[0] + high * along[0], point[1] + high * along[1])


def _flat(points):
    return [coordinate for corner in points for coordinate in corner]


def horizon_shape(dial, bank_deg, pitch_deg):
    """Sky, ground, horizon line, ladder and bank pointer for one attitude (cockpit convention, degrees)."""
    along, up = _directions(bank_deg)
    pixels_per_degree = dial.radius / DEGREES_PER_RADIUS
    # nose up moves the horizon away from the sky side (down on the screen when wings are level)
    horizon_point = (dial.cx - up[0] * pitch_deg * pixels_per_degree, dial.cy - up[1] * pitch_deg * pixels_per_degree)
    window = circle_polygon(dial)
    sky = clip_half_plane(window, horizon_point, up)
    ground = clip_half_plane(window, horizon_point, (-up[0], -up[1]))
    shape = HorizonShape(sky=_flat(sky) if len(sky) >= 3 else [], ground=_flat(ground) if len(ground) >= 3 else [],
                         horizon_line=line_in_circle(dial, horizon_point, along))
    shape.ladder = _ladder(dial, horizon_point, along, up, pitch_deg, pixels_per_degree)
    shape.bank_pointer = _bank_pointer(dial, along, up)
    return shape


def _ladder(dial, horizon_point, along, up, pitch_deg, pixels_per_degree):
    """Ladder lines within PITCH_VISIBLE_DEG of the pitch (not the horizon itself), inside the window."""
    lines = []
    first = math.ceil((pitch_deg - PITCH_VISIBLE_DEG) / PITCH_STEP_DEG) * PITCH_STEP_DEG
    for pitch in range(int(first), int(pitch_deg + PITCH_VISIBLE_DEG) + 1, PITCH_STEP_DEG):
        if pitch == 0 or abs(pitch) > 90:
            continue
        centre = (horizon_point[0] + up[0] * pitch * pixels_per_degree,
                  horizon_point[1] + up[1] * pitch * pixels_per_degree)
        half_length = dial.radius * (0.32 if pitch % 20 == 0 else 0.2)
        segment = line_in_circle(dial, centre, along, half_length)
        if not segment or math.hypot(centre[0] - dial.cx, centre[1] - dial.cy) > dial.radius * 0.85:
            continue
        label_offset = half_length + dial.radius * 0.12
        labels = ((centre[0] - along[0] * label_offset, centre[1] - along[1] * label_offset),
                  (centre[0] + along[0] * label_offset, centre[1] + along[1] * label_offset))
        lines.append(LadderLine(pitch=pitch, line=segment, labels=labels))
    return lines[:LADDER_SLOTS]


def _bank_pointer(dial, along, up):
    """Triangle on the sky side that turns with the horizon and points at the bank on the fixed scale."""
    tip, base, half_width = dial.radius * 0.84, dial.radius * 0.97, dial.radius * 0.07
    tip_point = (dial.cx + up[0] * tip, dial.cy + up[1] * tip)
    base_centre = (dial.cx + up[0] * base, dial.cy + up[1] * base)
    return _flat([tip_point, (base_centre[0] - along[0] * half_width, base_centre[1] - along[1] * half_width),
                  (base_centre[0] + along[0] * half_width, base_centre[1] + along[1] * half_width)])


def bank_scale_ticks(dial):
    """Fixed ticks of the bank scale on the rim, from the top: [(bank, x0, y0, x1, y1)]; 0, 30, 60 and 90 are
    longer."""
    ticks = []
    for bank in BANK_SCALE_DEG:
        angle = math.radians(bank)
        direction = (math.sin(angle), -math.cos(angle))
        outer = dial.radius * (1.13 if bank % 30 == 0 else 1.08)
        ticks.append((bank, dial.cx + direction[0] * dial.radius * 1.01, dial.cy + direction[1] * dial.radius * 1.01,
                      dial.cx + direction[0] * outer, dial.cy + direction[1] * outer))
    return ticks


def aircraft_symbol(dial):
    """Fixed aircraft symbol in the middle: two wing bars (each with a short bend down) and a centre dot.
    Returns ([line coordinates], dot box (x0, y0, x1, y1))."""
    cx, cy, radius = dial.cx, dial.cy, dial.radius
    inner, outer, bend = radius * 0.16, radius * 0.55, radius * 0.08
    left = (cx - outer, cy, cx - inner, cy, cx - inner, cy + bend)
    right = (cx + outer, cy, cx + inner, cy, cx + inner, cy + bend)
    dot = radius * 0.035
    return [left, right], (cx - dot, cy - dot, cx + dot, cy + dot)


def format_attitude(bank_deg, pitch_deg):
    """Whole degrees with a real minus sign, e.g. (23, '−4'); -0 becomes 0."""
    def whole(value):
        number = int(round(value))
        return f"−{abs(number)}" if number < 0 else str(number)
    return whole(bank_deg), whole(pitch_deg)
