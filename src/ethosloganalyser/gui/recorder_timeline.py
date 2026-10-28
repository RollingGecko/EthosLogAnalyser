# -*- coding: utf-8 -*-
"""The timeline of the flight recorder: track with the position, telemetry band, buttons, time and speed.

The track spans the flight from its start to its end (the last row with telemetry). A click on it jumps there,
dragging moves the position (also while the flight plays; it plays on when the mouse is released). The thin band
below the track marks where telemetry is there, so gaps within the flight show. Below the track: play/stop, first
row, one row back, one row forward, end, the time "3:12 / 8:58" (log time) and the speed in fixed steps.
"""

from ..i18n import N_, get_language, tr
from ..recorder.playback import DEFAULT_SPEED, SPEEDS
from ..utils import fmt_duration

TRACK_COLOUR = "#c3ccd8"
PLAYED_COLOUR = "#1f5fa8"
KNOB_COLOUR = "#1f5fa8"
BAND_COLOUR = "#5f9e6e"
PLAY_TEXT = N_("▶ Abspielen")
STOP_TEXT = N_("■ Stopp")
SPEED_SCALE_LENGTH = (60, 150)        # the speed slider shrinks to this range when the window is narrow


def speed_text(speed):
    """Speed for the label, with the decimal sign of the language: "0,25×" in German and Spanish, "0.25×" in
    English."""
    text = f"{speed:g}×"
    return text.replace(".", ",") if get_language() in ("de", "es") else text


def time_text(position, start, end):
    """ "3:12 / 8:58": the position and the end of the flight in log time."""
    return f"{fmt_duration(position - start)} / {fmt_duration(end - start)}"


def x_for_time(t, start, end, left, right):
    """Pixel of a log time on the track from left to right."""
    span = end - start
    share = (t - start) / span if span > 0 else 0.0
    return left + min(max(share, 0.0), 1.0) * (right - left)


def time_for_x(x, start, end, left, right):
    """Log time of a pixel on the track (limited to the flight)."""
    width = right - left
    share = (x - left) / width if width > 0 else 0.0
    return start + min(max(share, 0.0), 1.0) * (end - start)


class Timeline:
    """The widgets of the timeline. actions: callables "toggle", "start", "back", "forward", "end", "seek(t)",
    "drag_start", "drag_end" and "speed(value)"."""

    def __init__(self, parent, actions, line_height):
        import tkinter as tk
        from tkinter import ttk
        from .style import BG

        self.actions = actions
        self.start, self.end, self.ranges = 0.0, 0.0, []
        self.position = 0.0
        self.speed_index = SPEEDS.index(DEFAULT_SPEED)
        self.frame = ttk.Frame(parent, padding=(8, 4, 8, 4))
        self.frame.columnconfigure(0, weight=1)
        track_height = round(line_height * 1.4) + max(4, round(line_height * 0.35)) + 6
        self.track = tk.Canvas(self.frame, height=track_height, background=BG, highlightthickness=0, cursor="hand2")
        self.track.grid(row=0, column=0, sticky="ew")
        self._build_items(line_height)
        ttk.Style(self.frame).configure("Recorder.TButton", padding=(4, 2))     # narrow buttons: fits small windows
        self.controls = controls = ttk.Frame(self.frame)
        controls.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        play_width = max(len(tr(PLAY_TEXT)), len(tr(STOP_TEXT))) + 1      # the button does not change its width
        self.play_button = ttk.Button(controls, text=tr(PLAY_TEXT), width=play_width, takefocus=False,
                                      style="Recorder.TButton", command=actions["toggle"])
        self.play_button.pack(side="left", padx=(0, 8))
        self.step_buttons = []
        for text, key in (("⏮", "start"), ("◀", "back"), ("▶", "forward"), ("⏭", "end")):
            button = ttk.Button(controls, text=text, width=2, takefocus=False, style="Recorder.TButton",
                                command=actions[key])
            button.pack(side="left", padx=1)
            self.step_buttons.append(button)
        self.time_label = ttk.Label(controls, text=time_text(0, 0, 0), anchor="center")
        self.time_label.pack(side="left", padx=(10, 0))
        self.speed_label = ttk.Label(controls, text=speed_text(DEFAULT_SPEED), width=6)
        self.speed_label.pack(side="right")
        self.speed_scale = ttk.Scale(controls, from_=0, to=len(SPEEDS) - 1, orient="horizontal",
                                     length=SPEED_SCALE_LENGTH[1], takefocus=False, command=self._speed_moved)
        self.speed_scale.set(self.speed_index)
        self.speed_scale.pack(side="right", padx=4)
        self.speed_title = ttk.Label(controls, text=tr("Tempo"))
        self.speed_title.pack(side="right")
        self.track.bind("<Configure>", lambda _event: self._redraw_track())
        self.frame.bind("<Configure>", lambda event: self._fit_controls(event.width))
        self.track.bind("<ButtonPress-1>", self._pressed)
        self.track.bind("<B1-Motion>", lambda event: self._seek_to(event.x))
        self.track.bind("<ButtonRelease-1>", lambda _event: actions["drag_end"]())

    def _build_items(self, line_height):
        """Items of the track: created once, later only moved."""
        canvas = self.track
        self.line_width = max(4, round(line_height * 0.3))
        self.knob_radius = max(6, round(line_height * 0.55))
        self.band_height = max(4, round(line_height * 0.35))
        self.rail = canvas.create_line(0, 0, 0, 0, fill=TRACK_COLOUR, width=self.line_width, capstyle="round")
        self.played = canvas.create_line(0, 0, 0, 0, fill=PLAYED_COLOUR, width=self.line_width, capstyle="round")
        self.knob = canvas.create_oval(0, 0, 0, 0, fill=KNOB_COLOUR, outline="#ffffff", width=2)

    # ---------------- geometry ----------------
    @property
    def _ends(self):
        """Pixels of the start and the end of the flight on the track."""
        return self.knob_radius + 2, max(self.track.winfo_width() - self.knob_radius - 2, self.knob_radius + 3)

    @property
    def _rail_y(self):
        return self.knob_radius + 2

    def _redraw_track(self):
        """Rail and telemetry band for the current size (the band is drawn again, the knob is moved)."""
        canvas = self.track
        left, right = self._ends
        y = self._rail_y
        canvas.coords(self.rail, left, y, right, y)
        canvas.delete("band")
        band_top = y + self.knob_radius + 3
        for start, end in self.ranges:
            x0 = x_for_time(start, self.start, self.end, left, right)
            x1 = max(x_for_time(end, self.start, self.end, left, right), x0 + 1)
            canvas.create_rectangle(x0, band_top, x1, band_top + self.band_height, fill=BAND_COLOUR, outline="",
                                    tags="band")
        self._move_knob()

    def _move_knob(self):
        left, right = self._ends
        x = x_for_time(self.position, self.start, self.end, left, right)
        y, radius = self._rail_y, self.knob_radius
        self.track.coords(self.played, left, y, x, y)
        self.track.coords(self.knob, x - radius, y - radius, x + radius, y + radius)

    def _fit_controls(self, width):
        """Shortens the speed slider (and leaves out the word "Tempo" if that is not enough) so that the buttons,
        the time and the speed fit into a narrow window."""
        fixed = [child for child in self.controls.winfo_children() if child not in (self.speed_scale, self.speed_title)]
        room = width - sum(child.winfo_reqwidth() + 10 for child in fixed) - 24
        show_title = room - self.speed_title.winfo_reqwidth() - 10 >= SPEED_SCALE_LENGTH[0]
        if show_title:
            room -= self.speed_title.winfo_reqwidth() + 10
        length = min(max(room, SPEED_SCALE_LENGTH[0]), SPEED_SCALE_LENGTH[1])
        if int(float(str(self.speed_scale.cget("length")))) != length:
            self.speed_scale.configure(length=length)
        if show_title and not self.speed_title.winfo_ismapped():
            self.speed_title.pack(side="right", after=self.speed_scale)
        elif not show_title:
            self.speed_title.pack_forget()

    # ---------------- showing ----------------
    def set_flight(self, start, end, ranges):
        """A new flight: its start and end and the log times with telemetry [(start, end)]."""
        self.start, self.end, self.ranges = start, end, list(ranges)
        self.position = start
        self._redraw_track()
        # as wide as the longest time of this flight, so the digits do not make the buttons jump while it plays
        self.time_label.configure(text=time_text(start, start, end), width=len(time_text(end, start, end)) + 1)

    def show(self, position, running):
        """Position of the playback (log time) and whether it plays."""
        self.position = position
        self._move_knob()
        self.time_label.configure(text=time_text(position, self.start, self.end))
        self.play_button.configure(text=tr(STOP_TEXT) if running else tr(PLAY_TEXT))

    def set_speed(self, speed):
        """Shows a speed (e.g. restored after a language switch) without telling the page."""
        self.speed_index = SPEEDS.index(speed)
        self.speed_scale.set(self.speed_index)
        self.speed_label.configure(text=speed_text(speed))

    # ---------------- user ----------------
    def _pressed(self, event):
        self.actions["drag_start"]()
        self._seek_to(event.x)

    def _seek_to(self, x):
        left, right = self._ends
        self.actions["seek"](time_for_x(x, self.start, self.end, left, right))

    def _speed_moved(self, value):
        """The slider snaps to the fixed speed steps."""
        index = min(max(int(round(float(value))), 0), len(SPEEDS) - 1)
        if abs(float(value) - index) > 1e-6:
            self.speed_scale.set(index)                  # calls this again with the snapped value
            return
        if index != self.speed_index:
            self.speed_index = index
            self.speed_label.configure(text=speed_text(SPEEDS[index]))
            self.actions["speed"](SPEEDS[index])
