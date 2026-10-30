# -*- coding: utf-8 -*-
"""The radio (transmitter) of the flight recorder on a Tk canvas: two stick fields with a dot each, the axes of the
stick below the field and its values in percent.

Same rules as for the gauges (gui/recorder_dials.py): the dots and the numbers are created once and only moved or
changed; the static parts (bezel, fields, cross hairs, axis names) are drawn again only when the size, the stick
mode or the language changes (``place``). A channel without a recent value shows "—" and its dot turns grey.
The geometry comes from recorder/radio.py, the values and texts from recorder/stick_modes.py.
"""

from ..recorder.radio import dot_position, dot_radius, radio_parts
from ..recorder.stick_modes import axes_label, radio_readings, stick_axes
from .recorder_dials import STALE, fitting_size
from .recorder_instruments import BEZEL, RIM, SCALE, SYMBOL

FIELD = "#24282e"


class RadioPanel:
    """The radio: place() draws the static parts for a rectangle and a stick mode, show() moves the dots."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.tag = "radio"
        self.parts = None
        self.visible = False
        dynamic = (self.tag, self.tag + "-dynamic")
        self.dots = [canvas.create_oval(0, 0, 0, 0, fill=SYMBOL, outline=BEZEL, state="hidden", tags=dynamic)
                     for _field in range(2)]
        self.values = [canvas.create_text(0, 0, fill=SCALE, state="hidden", tags=dynamic) for _field in range(2)]

    # ---------------- static parts ----------------
    def place(self, rect, line_height, family, mode):
        """Draws the static parts in rect for a stick mode (again after a size, mode or language change)."""
        canvas, tag = self.canvas, self.tag
        canvas.delete(tag + "-back")
        canvas.delete(tag + "-front")
        self.parts = parts = radio_parts(rect, line_height)
        back, front = (tag, tag + "-back"), (tag, tag + "-front")
        canvas.create_rectangle(rect.x, rect.y, rect.right, rect.bottom, fill=BEZEL, outline=RIM, width=2, tags=back)
        axes = stick_axes(mode)
        labels = [axes_label(stick) for stick in axes]
        label_size = fitting_size(family, line_height * 0.8, 7,
                                  lambda _font, bold: all(bold.measure(label) <= parts.text_width for label in labels))
        value_size = fitting_size(family, line_height * 0.85, 7,
                                  lambda _font, bold: bold.measure("−100 % / −100 %") <= parts.text_width)
        for index, field in enumerate(parts.fields):
            x0, y0, x1, y1 = field
            canvas.create_rectangle(x0, y0, x1, y1, fill=FIELD, outline=RIM, width=2, tags=back)
            canvas.create_line((x0 + x1) / 2, y0, (x0 + x1) / 2, y1, fill=RIM, tags=back)
            canvas.create_line(x0, (y0 + y1) / 2, x1, (y0 + y1) / 2, fill=RIM, tags=back)
            canvas.create_text(*parts.labels[index], text=labels[index], fill=SCALE, font=(family, -label_size),
                               tags=back)
            canvas.coords(self.values[index], *parts.values[index])
            canvas.itemconfigure(self.values[index], font=(family, -value_size, "bold"))
        canvas.tag_lower(tag + "-back")
        canvas.tag_raise(tag + "-dynamic")
        self.visible = True
        canvas.itemconfigure(tag, state="normal")

    def hide(self):
        """The radio is not shown (the log has no stick channels, or the layout leaves it out)."""
        self.visible = False
        self.canvas.delete(self.tag + "-back")
        self.canvas.delete(self.tag + "-front")
        self.canvas.itemconfigure(self.tag, state="hidden")

    # ---------------- moving parts ----------------
    def show(self, track, row, mode):
        """Moves the dots and changes the numbers to the values of a row."""
        if not self.visible or track is None:
            return
        canvas = self.canvas
        for index, reading in enumerate(radio_readings(track, row, mode)):
            field = self.parts.fields[index]
            x, y = dot_position(field, reading.x, reading.y)
            size = dot_radius(field)
            canvas.coords(self.dots[index], x - size, y - size, x + size, y + size)
            canvas.itemconfigure(self.dots[index], fill=STALE if reading.stale else SYMBOL)
            canvas.itemconfigure(self.values[index], text=reading.text, fill=STALE if reading.stale else SCALE)
