# -*- coding: utf-8 -*-
"""The cockpit gauges of the flight recorder on a Tk canvas: round dials with a bar (altitude, vertical speed,
drive, battery) and, in the minimal layout, a column of numbers.

The same rules as for the horizon (gui/recorder_instruments.py) keep the playback smooth:

* moving parts (pointer, numbers, bar fill) are created once and then only moved or changed;
* static parts (bezel, dial face, scale, labels, title) are drawn again only when the size or the flight changes
  (``place``).

Numbers are right-aligned at a fixed place, so the digits do not jump when the number of digits changes. A missing
or stale value shows "—" with a grey pointer; the pointer stays where it was, like the "OFF" flag of a real
instrument. The geometry comes from recorder/dials.py, the values and texts from recorder/readouts.py.
"""

from ..db import sensor_roles as roles
from ..i18n import tr
from ..recorder.dials import (hub_box, label_divisor, label_text, panel_parts, pointer_angle, pointer_polygon,
                              scale_labels, scale_ticks, bar_fill)
from ..recorder.readouts import (PANEL_TITLES, QUANTITY_NAMES, RPM_UNIT, arc_of, dial_scale, reading,
                                 widest_text)
from .recorder_instruments import BEZEL, RIM, SCALE, SYMBOL

STALE = "#7d8590"
FACE = "#24282e"
TROUGH = "#3a3f47"
DIAL_UNITS = {roles.ALTITUDE: "m", roles.VERTICAL_SPEED: "m/s", roles.MOTOR_CURRENT: "A"}


def _fitting_size(family, start, smallest, fits):
    """Largest pixel size from start down to smallest at which fits(font, bold font) is True."""
    from tkinter import font as tkfont
    size = max(int(round(start)), smallest)
    while size > smallest and not fits(tkfont.Font(family=family, size=-size),
                                       tkfont.Font(family=family, size=-size, weight="bold")):
        size -= 1
    return size


def dial_unit(role, scale):
    """Unit printed on the dial face, e.g. "m/s", or "U/min" with "×1000" below it when the labels are in
    thousands."""
    if role == roles.RPM:
        unit = tr(RPM_UNIT)
        return f"{unit}\n×1000" if label_divisor(scale) == 1000 else unit
    return DIAL_UNITS.get(role, "")


class GaugePanel:
    """One gauge next to the horizon: a round dial (dial_role) and/or a bar (bar_role) with a title."""

    def __init__(self, canvas, name):
        self.canvas = canvas
        self.name = name
        self.tag = f"gauge-{name}"
        self.dial_role = self.bar_role = None
        self.parts = self.scales = None
        self.visible = False
        dynamic = (self.tag, self.tag + "-dynamic")
        self.pointer = canvas.create_polygon(0, 0, 0, 0, 0, 0, fill=SYMBOL, outline="", state="hidden", tags=dynamic)
        self.number = canvas.create_text(0, 0, anchor="e", fill=SCALE, state="hidden", tags=dynamic)
        self.bar = canvas.create_rectangle(0, 0, 0, 0, fill=SYMBOL, outline="", state="hidden", tags=dynamic)
        self.bar_number = canvas.create_text(0, 0, anchor="e", fill=SCALE, state="hidden", tags=dynamic)

    # ---------------- static parts ----------------
    def place(self, rect, line_height, family, roles_shown, scales):
        """Draws the static parts in rect for (dial role, bar role) and the scales of the flight."""
        canvas, tag = self.canvas, self.tag
        canvas.delete(tag + "-back")
        canvas.delete(tag + "-front")
        self.dial_role, self.bar_role = roles_shown
        self.scales = scales
        self.parts = parts = panel_parts(rect, line_height, self.dial_role is not None, self.bar_role is not None)
        back, front = (tag, tag + "-back"), (tag, tag + "-front")
        canvas.create_rectangle(rect.x, rect.y, rect.right, rect.bottom, fill=BEZEL, outline=RIM, width=2, tags=back)
        title = tr(PANEL_TITLES[self.name])
        title_size = _fitting_size(family, line_height * 0.8, 7,
                                   lambda _font, bold: bold.measure(title) <= parts.text_width)
        canvas.create_text(*parts.title, text=title, fill=SCALE, font=(family, -title_size, "bold"), tags=back)
        if parts.dial is not None:
            self._place_dial(line_height, family, back, front)
        if parts.bar_box is not None:
            self._place_bar(line_height, family, back)
        canvas.tag_lower(tag + "-back")
        canvas.tag_raise(tag + "-dynamic")
        canvas.tag_raise(tag + "-front")
        self.visible = True
        canvas.itemconfigure(tag, state="normal")
        self._hide_unused()

    def _place_dial(self, line_height, family, back, front):
        canvas, dial, role = self.canvas, self.parts.dial, self.dial_role
        scale, arc = dial_scale(self.scales, role), arc_of(role)
        radius = dial.radius
        canvas.create_oval(dial.cx - radius, dial.cy - radius, dial.cx + radius, dial.cy + radius, fill=FACE,
                           outline=RIM, width=max(2, round(radius * 0.04)), tags=back)
        for _value, labelled, x0, y0, x1, y1 in scale_ticks(dial, scale, arc):
            canvas.create_line(x0, y0, x1, y1, fill=SCALE, width=2 if labelled else 1, tags=back)
        label_font = (family, -max(7, round(radius * 0.17)))
        for value, x, y in scale_labels(dial, scale, arc):
            canvas.create_text(x, y, text=label_text(value, scale), fill=SCALE, font=label_font, tags=back)
        unit = dial_unit(role, scale)
        widest_unit_line = max(unit.split("\n"), key=len)
        unit_size = _fitting_size(family, radius * 0.14, 7,
                                  lambda font, _bold: font.measure(widest_unit_line) <= radius * 0.7)
        canvas.create_text(dial.cx, dial.cy + radius * 0.32, text=unit, fill=SCALE, justify="center",
                           font=(family, -unit_size), tags=back)
        canvas.create_oval(*hub_box(dial), fill=SYMBOL, outline=BEZEL, tags=front)
        widest = widest_text(role, self.scales)
        size = _fitting_size(family, max(line_height * 0.95, radius * 0.15), 7,
                             lambda _font, bold: bold.measure(widest) <= self.parts.text_width)
        from tkinter import font as tkfont
        width = tkfont.Font(family=family, size=-size, weight="bold").measure(widest)
        x, y = self.parts.value_line
        canvas.coords(self.number, x + min(width, self.parts.text_width) / 2, y)
        canvas.itemconfigure(self.number, font=(family, -size, "bold"))
        canvas.coords(self.pointer, *pointer_polygon(dial, pointer_angle(0.0, scale, arc)))

    def _place_bar(self, line_height, family, back):
        canvas, role = self.canvas, self.bar_role
        left, right, y = self.parts.bar_label_line
        name = tr(QUANTITY_NAMES[role])
        widest = widest_text(role, self.scales)
        size = _fitting_size(family, line_height * 0.8, 7, lambda font, bold: font.measure(name) + font.measure("  ")
                             + bold.measure(widest) <= right - left)
        canvas.create_text(left, y, text=name, anchor="w", fill=SCALE, font=(family, -size), tags=back)
        canvas.coords(self.bar_number, right, y)
        canvas.itemconfigure(self.bar_number, font=(family, -size, "bold"))
        canvas.create_rectangle(*self.parts.bar_box, fill=TROUGH, outline=RIM, tags=back)

    def _hide_unused(self):
        if self.parts.dial is None:
            for item in (self.pointer, self.number):
                self.canvas.itemconfigure(item, state="hidden")
        if self.parts.bar_box is None:
            for item in (self.bar, self.bar_number):
                self.canvas.itemconfigure(item, state="hidden")

    def hide(self):
        """The gauge is not shown (no data, or not in the layout)."""
        self.visible = False
        self.canvas.delete(self.tag + "-back")
        self.canvas.delete(self.tag + "-front")
        self.canvas.itemconfigure(self.tag, state="hidden")

    # ---------------- moving parts ----------------
    def show(self, track, row):
        """Moves pointer, numbers and bar to the values of a row."""
        if not self.visible or track is None:
            return
        canvas = self.canvas
        if self.dial_role is not None:
            value = reading(track, self.dial_role, row, self.scales)
            if not value.stale:
                angle = pointer_angle(value.value, dial_scale(self.scales, self.dial_role), arc_of(self.dial_role))
                canvas.coords(self.pointer, *pointer_polygon(self.parts.dial, angle))
            canvas.itemconfigure(self.pointer, fill=STALE if value.stale else SYMBOL)
            canvas.itemconfigure(self.number, text=value.text, fill=STALE if value.stale else SCALE)
        if self.bar_role is not None:
            value = reading(track, self.bar_role, row, self.scales)
            fill = bar_fill(self.parts.bar_box, value.share) if not value.stale else ()
            if fill:
                canvas.coords(self.bar, *fill)
                canvas.itemconfigure(self.bar, state="normal")
            else:
                canvas.itemconfigure(self.bar, state="hidden")
            canvas.itemconfigure(self.bar_number, text=value.text, fill=STALE if value.stale else SCALE)


class ReadoutPanel:
    """The minimal layout: one line per sensor with its name on the left and its number on the right."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.tag = "readouts"
        self.numbers = {}                      # role -> text item
        self.scales = None

    def place(self, rect, line_height, family, line_roles, scales):
        """Draws the names and creates the numbers for the roles of the lines."""
        canvas = self.canvas
        canvas.delete(self.tag)
        self.scales = scales
        self.numbers = {}
        if not line_roles:
            return
        padding = max(4.0, line_height * 0.35)
        names = {role: tr(QUANTITY_NAMES[role]) for role in line_roles}
        widest = {role: widest_text(role, scales) for role in line_roles}
        spacing = min(line_height * 1.6, (rect.height - 2 * padding) / len(line_roles))
        size = _fitting_size(family, min(line_height * 0.9, spacing * 0.7), 7, lambda font, bold: all(
            font.measure(names[role]) + font.measure("  ") + bold.measure(widest[role])
            <= rect.width - 2 * padding for role in line_roles))
        height = spacing * len(line_roles)
        canvas.create_rectangle(rect.x, rect.y, rect.right, rect.y + height + 2 * padding, fill=BEZEL,
                                outline=RIM, width=2, tags=self.tag)
        for index, role in enumerate(line_roles):
            y = rect.y + padding + spacing * (index + 0.5)
            canvas.create_text(rect.x + padding, y, text=names[role], anchor="w", fill=SCALE,
                               font=(family, -size), tags=self.tag)
            self.numbers[role] = canvas.create_text(rect.right - padding, y, text="", anchor="e", fill=SCALE,
                                                    font=(family, -size, "bold"), tags=self.tag)

    def hide(self):
        self.canvas.delete(self.tag)
        self.numbers = {}

    def show(self, track, row):
        for role, item in self.numbers.items():
            value = reading(track, role, row, self.scales)
            self.canvas.itemconfigure(item, text=value.text, fill=STALE if value.stale else SCALE)
