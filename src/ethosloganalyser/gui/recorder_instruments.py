# -*- coding: utf-8 -*-
"""Instruments of the flight recorder drawn on a Tk canvas (so far: the artificial horizon).

Drawing follows two rules so the playback stays smooth on Windows:

* the moving parts are created once and then only moved (``coords``, ``itemconfigure``), never deleted and
  created again;
* the static parts (bezel, scale, aircraft symbol) are drawn again only when the size changes (``place``).

The geometry comes from recorder/gauges.py. Style: a classic cockpit instrument (dark bezel, blue sky, brown
ground) inside the light window.
"""

from ..i18n import N_, tr
from ..recorder.gauges import (LADDER_SLOTS, aircraft_symbol, bank_scale_ticks, format_attitude, horizon_dial,
                               horizon_shape)

BEZEL = "#1c1f24"
RIM = "#33383f"
SCALE = "#e8ecf1"
SYMBOL = "#f2b134"
COLOURS = {False: {"sky": "#2f6db5", "ground": "#7a4a24", "line": "#ffffff", "ladder": "#ffffff"},
           True: {"sky": "#7d8590", "ground": "#5a5f66", "line": "#c9ced4", "ladder": "#c9ced4"}}   # True: stale

ATTITUDE_TEXT = N_("Roll {bank}° · Nick {pitch}°")
NO_ATTITUDE = N_("keine Lagedaten")


def _hidden_polygon(canvas, **options):
    return canvas.create_polygon(0, 0, 0, 0, 0, 0, state="hidden", **options)


class HorizonGauge:
    """The artificial horizon on a canvas: place() draws it for a rectangle, show() moves it to an attitude."""

    def __init__(self, canvas, tag="horizon"):
        self.canvas = canvas
        self.tag = tag
        self.dial = None
        self.visible = False
        dynamic = (tag, tag + "-dynamic")
        self.sky = _hidden_polygon(canvas, tags=dynamic, outline="")
        self.ground = _hidden_polygon(canvas, tags=dynamic, outline="")
        self.ladder_lines = [canvas.create_line(0, 0, 0, 0, state="hidden", tags=dynamic, width=2)
                             for _slot in range(LADDER_SLOTS)]
        self.ladder_labels = [canvas.create_text(0, 0, state="hidden", tags=dynamic, fill="#ffffff")
                              for _slot in range(2 * LADDER_SLOTS)]
        self.horizon_line = canvas.create_line(0, 0, 0, 0, state="hidden", tags=dynamic, width=2)
        self.bank_pointer = _hidden_polygon(canvas, tags=dynamic, fill=SCALE, outline="")
        text = (tag, tag + "-text")
        self.digits = canvas.create_text(0, 0, state="hidden", tags=text, fill=SCALE)
        self.status = canvas.create_text(0, 0, state="hidden", tags=text, fill="#ffffff")

    # ---------------- static parts ----------------
    def place(self, rect, line_height, font_family):
        """Draws the static parts for the instrument rectangle (again after a size change)."""
        from tkinter import font as tkfont
        canvas, tag = self.canvas, self.tag
        canvas.delete(tag + "-back")
        canvas.delete(tag + "-front")
        self.dial = dial = horizon_dial(rect.x, rect.y, rect.width, rect.height, line_height)
        back, front = (tag, tag + "-back"), (tag, tag + "-front")
        canvas.create_rectangle(rect.x, rect.y, rect.right, rect.bottom, fill=BEZEL, outline=RIM, width=2, tags=back)
        radius = dial.radius
        canvas.create_oval(dial.cx - radius, dial.cy - radius, dial.cx + radius, dial.cy + radius,
                           outline=RIM, width=max(2, round(radius * 0.04)), tags=front)
        for bank, x0, y0, x1, y1 in bank_scale_ticks(dial):
            canvas.create_line(x0, y0, x1, y1, fill=SCALE, width=3 if bank % 30 == 0 else 2, tags=front)
        wings, dot = aircraft_symbol(dial)
        for wing in wings:
            canvas.create_line(*wing, fill=SYMBOL, width=max(3, round(radius * 0.045)), capstyle="round", tags=front)
        canvas.create_oval(*dot, fill=SYMBOL, outline=SYMBOL, tags=front)

        ladder_font = (font_family, -max(8, round(radius * 0.1)))
        for label in self.ladder_labels:
            canvas.itemconfigure(label, font=ladder_font)
        digits_font = self._fitting_font(font_family, line_height, rect.width * 0.92, tkfont)
        label_y = dial.cy + radius * 1.13 + (rect.bottom - dial.cy - radius * 1.13) / 2
        canvas.coords(self.digits, dial.cx, label_y)
        canvas.itemconfigure(self.digits, font=digits_font)
        canvas.coords(self.status, dial.cx, dial.cy - radius * 0.45)
        canvas.itemconfigure(self.status, font=(font_family, digits_font[1], "bold"), text=tr(NO_ATTITUDE))
        canvas.tag_lower(tag + "-back")
        canvas.tag_raise(tag + "-front")
        canvas.tag_raise(tag + "-text")
        if not self.visible:
            canvas.itemconfigure(tag, state="hidden")

    @staticmethod
    def _fitting_font(family, line_height, width, tkfont):
        """Font for the digits: the size of the default font, smaller if the widest text does not fit."""
        widest = tr(ATTITUDE_TEXT, bank="−180", pitch="−90")
        size = round(line_height * 0.8)
        while size > 7 and tkfont.Font(family=family, size=-size).measure(widest) > width:
            size -= 1
        return (family, -size)

    # ---------------- moving parts ----------------
    def show(self, attitude):
        """Moves the horizon to (bank, pitch, stale) in the cockpit convention; None hides the instrument."""
        canvas = self.canvas
        if attitude is None or self.dial is None:
            self.visible = False
            canvas.itemconfigure(self.tag, state="hidden")
            return
        if not self.visible:
            self.visible = True
            canvas.itemconfigure(self.tag + "-back", state="normal")
            canvas.itemconfigure(self.tag + "-front", state="normal")
            canvas.itemconfigure(self.digits, state="normal")
        bank, pitch, stale = attitude
        shape = horizon_shape(self.dial, bank, pitch)
        colours = COLOURS[stale]
        self._set_polygon(self.sky, shape.sky, fill=colours["sky"])
        self._set_polygon(self.ground, shape.ground, fill=colours["ground"])
        self._set_line(self.horizon_line, shape.horizon_line, fill=colours["line"])
        for slot, item in enumerate(self.ladder_lines):
            entry = shape.ladder[slot] if slot < len(shape.ladder) else None
            self._set_line(item, entry.line if entry else (), fill=colours["ladder"])
            for side in (0, 1):
                label = self.ladder_labels[2 * slot + side]
                if entry is None:
                    canvas.itemconfigure(label, state="hidden")
                else:
                    canvas.coords(label, *entry.labels[side])
                    canvas.itemconfigure(label, state="normal", text=str(abs(entry.pitch)), fill=colours["ladder"])
        self._set_polygon(self.bank_pointer, shape.bank_pointer)
        bank_text, pitch_text = format_attitude(bank, pitch)
        canvas.itemconfigure(self.digits, text=tr(ATTITUDE_TEXT, bank=bank_text, pitch=pitch_text))
        canvas.itemconfigure(self.status, state="normal" if stale else "hidden")

    def _set_polygon(self, item, flat, **options):
        if len(flat) >= 6:
            self.canvas.coords(item, *flat)
            self.canvas.itemconfigure(item, state="normal", **options)
        else:
            self.canvas.itemconfigure(item, state="hidden")

    def _set_line(self, item, segment, **options):
        if segment:
            self.canvas.coords(item, *segment)
            self.canvas.itemconfigure(item, state="normal", **options)
        else:
            self.canvas.itemconfigure(item, state="hidden")
