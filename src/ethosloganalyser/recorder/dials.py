# -*- coding: utf-8 -*-
"""Geometry of the round gauges and bars of the flight recorder as plain functions (canvas pixels, y down).

A scale is chosen once per flight from the values of the flight ("nice" full-scale values such as 25, 120 or
250), so a park flyer and a big jet both use the whole dial. Angles are clock angles in degrees: 0 = 12 o'clock,
positive clockwise (90 = 3 o'clock, -90 = 9 o'clock).

Two kinds of dial:

* ``ARC``: 0 at 7:30, full scale at 4:30 (270 degrees), for altitude, RPM and current;
* ``CENTRED_ARC``: 0 at 9 o'clock like the vertical speed indicator of an aircraft, climbing clockwise (up),
  sinking anticlockwise (down), +/- full scale near 3 o'clock.

A pointer never leaves its scale: values beyond the ends stop at the end.
"""

import math
from dataclasses import dataclass

from ..i18n import get_language

# factors of a "nice" full-scale value per decade, e.g. 1.2 -> 120 A, 2.5 -> 250 m
NICE_FACTORS = (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10)
# steps between labelled ticks per decade, preferred in this order (2.5 only if nothing else divides the scale)
STEP_FACTORS = (1, 2, 5, 2.5)
MAJOR_TICKS = (4, 8)                # labelled intervals of a full scale
CENTRED_MAJOR_TICKS = (2, 5)        # labelled intervals per side of a scale centred on 0
VERTICAL_SPEED_SCALES = (5, 10, 20)  # m/s, the decision of the user; larger values get a nice value


@dataclass(frozen=True)
class Arc:
    """Where a dial puts its scale: the clock angle of the value 0, the sweep to full scale (clockwise) and
    whether the scale runs from -full to +full around 0."""
    zero_angle: float
    sweep: float
    centred: bool = False


ARC = Arc(zero_angle=-135, sweep=270)
CENTRED_ARC = Arc(zero_angle=-90, sweep=165, centred=True)


@dataclass(frozen=True)
class Scale:
    """A scale from 0 (or -full) to full with labelled ticks every step."""
    full: float
    step: float
    centred: bool = False

    @property
    def low(self):
        return -self.full if self.centred else 0.0

    def major_values(self):
        """The labelled values from low to full."""
        count = int(round((self.full - self.low) / self.step))
        return [self.low + index * self.step for index in range(count + 1)]

    def minor_values(self):
        """Unlabelled ticks halfway between the labelled ones."""
        majors = self.major_values()
        return [(first + second) / 2 for first, second in zip(majors, majors[1:])]


@dataclass(frozen=True)
class Dial:
    """A round dial: centre and radius in pixels."""
    cx: float
    cy: float
    radius: float


def nice_ceiling(value, minimum):
    """The smallest nice value (NICE_FACTORS x 10^n) that is at least value and at least minimum."""
    value = max(float(value) if value is not None and math.isfinite(value) else 0.0, float(minimum))
    decade = 10.0 ** math.floor(math.log10(value))
    for factor in NICE_FACTORS:
        if factor * decade >= value * (1 - 1e-9):
            return _clean(factor * decade)
    return _clean(10 * decade)


def _clean(number):
    """Removes floating point noise (0.30000000000000004 -> 0.3)."""
    return float(f"{number:.10g}")


def tick_step(full, intervals):
    """Step between labelled ticks: a nice step that divides full into intervals[0] to intervals[1] parts; the
    largest such step of the preferred kinds, else full / intervals[0]."""
    fewest, most = intervals
    candidates = []
    decade = 10.0 ** math.floor(math.log10(full))
    for scale in (decade / 10, decade, decade * 10):
        for preference, factor in enumerate(STEP_FACTORS):
            step = _clean(factor * scale)
            parts = full / step
            if abs(parts - round(parts)) < 1e-9 and fewest <= round(parts) <= most:
                candidates.append((preference == len(STEP_FACTORS) - 1, -step, step))
    return min(candidates)[2] if candidates else _clean(full / fewest)


def scale_for(maximum, minimum_full):
    """Scale from 0 to the nice value above the largest value of the flight (at least minimum_full)."""
    full = nice_ceiling(maximum, minimum_full)
    return Scale(full=full, step=tick_step(full, MAJOR_TICKS))


def vertical_speed_scale(largest_magnitude):
    """Scale around 0 up to +/- the largest climb or sink rate of the flight, rounded to 5, 10 or 20 m/s."""
    magnitude = largest_magnitude if largest_magnitude is not None and math.isfinite(largest_magnitude) else 0.0
    full = next((value for value in VERTICAL_SPEED_SCALES if abs(magnitude) <= value), None)
    if full is None:
        full = nice_ceiling(abs(magnitude), VERTICAL_SPEED_SCALES[-1])
    return Scale(full=full, step=tick_step(full, CENTRED_MAJOR_TICKS), centred=True)


def fraction(value, low, high):
    """Where value lies between low and high, limited to 0..1 (0 for a missing value or an empty range)."""
    if value is None or not math.isfinite(value) or high <= low:
        return 0.0
    return min(max((value - low) / (high - low), 0.0), 1.0)


def pointer_angle(value, scale, arc):
    """Clock angle of the pointer for value, stopped at the ends of the scale."""
    if arc.centred:
        share = fraction(value, -scale.full, scale.full) * 2 - 1            # -1 .. +1, 0 for the value 0
        if value is None or not math.isfinite(value):
            share = 0.0
        return arc.zero_angle + share * arc.sweep
    return arc.zero_angle + fraction(value, 0.0, scale.full) * arc.sweep


def point_on_dial(dial, angle, distance):
    """Point at a clock angle and a distance from the centre of the dial."""
    radians = math.radians(angle)
    return dial.cx + distance * math.sin(radians), dial.cy - distance * math.cos(radians)


def scale_ticks(dial, scale, arc):
    """Ticks of the scale: [(value, is_labelled, x0, y0, x1, y1)] on the rim, from low to full."""
    ticks = []
    for values, labelled in ((scale.major_values(), True), (scale.minor_values(), False)):
        inner = dial.radius * (0.80 if labelled else 0.87)
        for value in values:
            angle = pointer_angle(value, scale, arc)
            ticks.append((value, labelled) + point_on_dial(dial, angle, inner)
                         + point_on_dial(dial, angle, dial.radius * 0.97))
    return sorted(ticks, key=lambda tick: tick[0])


def scale_labels(dial, scale, arc):
    """Positions of the labels of the scale: [(value, x, y)] inside the labelled ticks."""
    return [(value,) + point_on_dial(dial, pointer_angle(value, scale, arc), dial.radius * 0.62)
            for value in scale.major_values()]


def label_divisor(scale):
    """1000 if the labels are written in thousands (e.g. RPM: 20, 40, ... with "x1000"), else 1."""
    return 1000 if scale.full >= 10000 else 1


def label_text(value, scale):
    """Text of a scale label: whole numbers where possible, the decimal sign of the language, the amount only (a
    centred scale has 0 in the middle and the same numbers above and below, like the instrument)."""
    number = abs(value) if scale.centred else value
    number /= label_divisor(scale)
    text = f"{number:g}".replace("-", "−")
    return text.replace(".", ",") if get_language() in ("de", "es") else text


def pointer_polygon(dial, angle):
    """Needle of a gauge: a narrow quadrilateral from a short tail behind the centre to the tip near the scale."""
    tip = point_on_dial(dial, angle, dial.radius * 0.78)
    tail = point_on_dial(dial, angle + 180, dial.radius * 0.16)
    left = point_on_dial(dial, angle - 90, dial.radius * 0.045)
    right = point_on_dial(dial, angle + 90, dial.radius * 0.045)
    return [tip[0], tip[1], left[0], left[1], tail[0], tail[1], right[0], right[1]]


def hub_box(dial):
    """The round cap over the centre of the needle: (x0, y0, x1, y1)."""
    size = dial.radius * 0.08
    return dial.cx - size, dial.cy - size, dial.cx + size, dial.cy + size


def bar_fill(box, share):
    """The filled part of a horizontal bar (x0, y0, x1, y1) for a share 0..1, from the left; () when empty."""
    x0, y0, x1, y1 = box
    share = min(max(share, 0.0), 1.0)
    if share <= 0:
        return ()
    return x0, y0, x0 + (x1 - x0) * share, y1


@dataclass(frozen=True)
class PanelParts:
    """Where the parts of one gauge go inside its rectangle: a title line at the top, then a round dial with the
    number below it, then a bar with a label line above it. A part the gauge does not have is None."""
    title: tuple                  # (x, y) centre of the title line
    dial: object                  # Dial or None
    value_line: object            # (x, y) centre of the number below the dial, or None
    bar_label_line: object        # (x left, x right, y) of the label line above the bar, or None
    bar_box: object               # (x0, y0, x1, y1) of the bar, or None
    text_width: float             # width a number may take


def panel_parts(rect, line_height, has_dial, has_bar):
    """The parts of a gauge in rect (a layout.Rect) at a font of line_height pixels."""
    padding = max(4.0, line_height * 0.3)
    left, right = rect.x + padding, rect.right - padding
    title = (rect.x + rect.width / 2, rect.y + padding + line_height / 2)
    top = rect.y + padding + line_height * 1.1
    bottom = rect.bottom - padding
    bar_height = max(6.0, line_height * 0.5)
    bar_section = line_height * 1.1 + bar_height if has_bar else 0.0
    value_height = line_height * 1.2 if has_dial else 0.0
    dial = value_line = None
    if has_dial:
        gap = padding if has_bar else 0.0
        diameter = max(min(right - left, bottom - top - value_height - bar_section - gap), 2.0)
        dial = Dial(cx=rect.x + rect.width / 2, cy=top + diameter / 2, radius=diameter / 2)
        value_line = (dial.cx, top + diameter + value_height / 2)
        bar_top = top + diameter + value_height + gap
    else:
        bar_top = top + (bottom - top - bar_section) / 2
    bar_label_line = bar_box = None
    if has_bar:
        bar_label_line = (left, right, bar_top + line_height * 0.5)
        bar_box = (left, bar_top + line_height * 1.1, right, bar_top + line_height * 1.1 + bar_height)
    return PanelParts(title=title, dial=dial, value_line=value_line, bar_label_line=bar_label_line,
                      bar_box=bar_box, text_width=right - left)
