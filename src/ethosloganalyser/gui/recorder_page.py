# -*- coding: utf-8 -*-
"""Tab "Flight recorder" of the single flight: plays the flight back from its stored time series.

The page loads the track of the selected log (recorder/flight_track.py) only when the tab is shown, plays it with
the playback clock (recorder/playback.py) and draws the horizon (gui/recorder_instruments.py), the cockpit gauges
(gui/recorder_dials.py), the radio (gui/recorder_radio.py), the aircraft (gui/recorder_aircraft.py) and the
timeline (gui/recorder_timeline.py) where recorder/layout.py puts them. The scales of the gauges are chosen once per flight (recorder/readouts.py); the stick
mode of the radio is a setting of the pilot (``set_stick_mode``, changes show at once, the playback goes on).

Timer: Tk ``after`` every TICK_MS. A tick only checks whether the log row at the current position changed; only
then the instruments are moved. Without interpolation the picture therefore changes about 3.7 times per second at
1x. A size change draws the static parts again after RESIZE_DELAY_MS, so dragging the window edge stays smooth.

Keys (while the tab is shown and has the focus): space play/stop, left/right one row, Shift+left/right 10 s,
Home/End first and last row.
"""

import time

from ..i18n import N_, tr
from ..recorder.aircraft_shape import has_aircraft
from ..recorder.chart_position import position_from_click
from ..recorder.layout import AIRCRAFT, HORIZON, RADIO, READOUTS, SIDE_GAUGES, TIMELINE, recorder_layout
from ..recorder.playback import JUMP_S, TICK_MS, PlaybackClock
from ..recorder.readouts import flight_scales, present_panels, readout_lines
from ..recorder.stick_modes import DEFAULT_STICK_MODE, has_sticks, valid_stick_mode
from .recorder_aircraft import AircraftPanel
from .recorder_dials import GaugePanel, ReadoutPanel
from .recorder_instruments import HorizonGauge
from .recorder_radio import RadioPanel
from .recorder_timeline import Timeline

RESIZE_DELAY_MS = 150
KEY_SEQUENCES = ("<space>", "<Left>", "<Right>", "<Shift-Left>", "<Shift-Right>", "<Home>", "<End>")
NO_INSTRUMENTS = N_("Für diesen Flug sind keine Daten für die Anzeigen des Flugrekorders im Log "
                    "(Lage, Höhe, Steigen/Sinken, Antrieb, Akku, Knüppel).")
NO_ROWS = N_("Dieser Log enthält keine Zeitreihen.")


class RecorderPage:
    """The recorder tab. load_track(key) returns the FlightTrack of a flight (or None)."""

    def __init__(self, parent, family):
        import tkinter as tk
        from tkinter import font as tkfont, ttk
        from .style import BG

        self.family = family
        self.load_track = lambda key: None
        self.cells_for = lambda key: 0               # cell count of the battery settings of the flight's aircraft
        self.stick_mode = DEFAULT_STICK_MODE         # stick mode 1-4 of the radio (a setting of the pilot)
        self.clock_function = time.perf_counter      # wall clock of the playback (tests put in their own)
        self.track = None
        self.playback = None
        self.scales = None                           # scales of the gauges for the loaded flight
        self.panels = {}                             # gauge -> (dial role, bar role) the loaded flight has data for
        self.key = None                              # flight shown on the page
        self.pending_key = None                      # flight selected while the tab was hidden
        self.active = False
        self.shown_row = None
        self.layout = None
        self._tick_id = None
        self._resize_id = None
        self._was_running = False                    # running when a drag on the timeline started
        self.line_height = tkfont.nametofont("TkDefaultFont").metrics("linespace")

        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.frame, background=BG, highlightthickness=0, takefocus=True)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.horizon = HorizonGauge(self.canvas)
        self.gauges = {name: GaugePanel(self.canvas, name) for name in SIDE_GAUGES}
        self.readouts = ReadoutPanel(self.canvas)
        self.radio = RadioPanel(self.canvas)
        self.aircraft = AircraftPanel(self.canvas)
        self.note = self.canvas.create_text(0, 0, text="", fill="#666666", state="hidden",
                                            font=(family, -round(self.line_height * 0.9)))
        self.timeline = Timeline(self.frame, {
            "toggle": self.toggle, "start": lambda: self._move(lambda clock: clock.go_to_start()),
            "back": lambda: self._move(lambda clock: clock.step_rows(-1)),
            "forward": lambda: self._move(lambda clock: clock.step_rows(1)),
            "end": lambda: self._move(lambda clock: clock.go_to_end()), "seek": self.seek,
            "drag_start": self._drag_started, "drag_end": self._drag_ended, "speed": self.set_speed},
            self.line_height)
        self._bind_keys()
        self.frame.bind("<Configure>", self._resized)
        self.frame.bind("<Destroy>", self._destroyed)

    # ---------------- keys ----------------
    def _bind_keys(self):
        """The keys work on the instrument canvas and on the timeline; the bind tag belongs to this page only
        (a class binding is global, a second page would otherwise take over the keys)."""
        self.key_tag = f"RecorderKeys{id(self)}"
        for widget in (self.canvas, self.timeline.track):
            widget.bindtags((self.key_tag,) + widget.bindtags())
        handlers = (self.toggle,
                    lambda: self._move(lambda clock: clock.step_rows(-1)),
                    lambda: self._move(lambda clock: clock.step_rows(1)),
                    lambda: self._move(lambda clock: clock.jump(-JUMP_S)),
                    lambda: self._move(lambda clock: clock.jump(JUMP_S)),
                    lambda: self._move(lambda clock: clock.go_to_start()),
                    lambda: self._move(lambda clock: clock.go_to_end()))
        self.key_actions = dict(zip(KEY_SEQUENCES, handlers))
        for sequence in KEY_SEQUENCES:
            self.canvas.bind_class(self.key_tag, sequence, lambda _event, key=sequence: (self.press_key(key), "break")[1])
        self.canvas.bind("<ButtonPress-1>", lambda _event: self.canvas.focus_set())
        self.timeline.track.bind("<ButtonPress-1>", lambda _event: self.canvas.focus_set(), add="+")

    def press_key(self, sequence):
        """What a key of KEY_SEQUENCES does (also called by the GUI test, as a window in the background of a test
        machine may not get the keyboard focus)."""
        self.key_actions[sequence]()

    # ---------------- flights ----------------
    def set_flight(self, key):
        """The selected flight changed: stops and loads it now if the tab is shown. The same flight selected again
        (e.g. when its aircraft has been prepared in the background) changes nothing, a playback goes on."""
        if key == self.key and self.track is not None and self.pending_key is None:
            return
        self.stop()
        self.pending_key = key
        if self.active:
            self._load_pending()

    def _load_pending(self):
        key, self.pending_key = self.pending_key, None
        self.key = key
        self.track = self.load_track(key) if key is not None else None
        rows = self.track.time[:self.track.end_row + 1] if self.track is not None else []
        self.playback = PlaybackClock(rows, clock=lambda: self.clock_function())
        if self.track is not None:
            self.scales = flight_scales(self.track, self.cells_for(key))
            self.panels = present_panels(self.track)
        else:
            self.scales, self.panels = None, {}
        if self.track is not None:
            self.timeline.set_flight(self.track.start_time, self.track.end_time, self.track.telemetry)
        else:
            self.timeline.set_flight(0.0, 0.0, [])
        self._relayout()

    def activate(self):
        """The tab is shown: loads a flight selected meanwhile and takes the keys."""
        self.active = True
        if self.pending_key is not None or self.playback is None:
            self._load_pending()
        self._draw()                                 # a position set from the charts while the tab was hidden
        self.canvas.focus_set()

    def deactivate(self):
        """The tab is hidden (other tab, logbook, other area): the playback stops."""
        self.active = False
        self.stop()

    # ---------------- playback ----------------
    def toggle(self):
        if self.playback is None or self.track is None or self.track.is_empty:
            return
        self.playback.toggle()
        self._draw(force=True)
        if self.playback.running:
            self._schedule_tick()

    def stop(self):
        """Stops the playback (the position stays)."""
        if self._tick_id is not None:
            self.canvas.after_cancel(self._tick_id)
            self._tick_id = None
        if self.playback is not None and self.playback.running:
            self.playback.stop()
            self._draw(force=True)

    def position(self):
        """The position [s since the start of the flight] for the position line of the charts: 0 for a flight not
        loaded yet; None if the flight has no track (no line)."""
        if self.pending_key is not None or self.playback is None:
            return 0.0
        return None if self.track is None or self.track.is_empty else self.playback.position

    def place_at(self, seconds):
        """A click in a chart: the position is set (limited to the flight), the playback stays stopped. The
        instruments are drawn at once if the tab is shown, else when it is shown again."""
        if self.pending_key is not None or self.playback is None:
            self._load_pending()
        if self.track is None or self.track.is_empty:
            return
        self.playback.stop()
        self.playback.seek(position_from_click(seconds, self.playback.start, self.playback.end))
        if self.active:
            self._draw(force=True)
        else:
            self.shown_row = None

    def seek(self, position):
        if self.playback is not None:
            self.playback.seek(position)
            self._draw()

    def set_speed(self, speed):
        if self.playback is not None:
            self.playback.set_speed(speed)

    def _move(self, action):
        """A button or key that moves the position: action(playback clock)."""
        if self.playback is None:
            return
        action(self.playback)
        self._draw(force=True)

    def _drag_started(self):
        self._was_running = self.playback is not None and self.playback.running
        self.stop()

    def _drag_ended(self):
        if self._was_running:
            self._was_running = False
            self.toggle()

    def _schedule_tick(self):
        if self._tick_id is None:
            self._tick_id = self.canvas.after(TICK_MS, self.tick)

    def tick(self):
        """Timer: draws only when the row at the position changed; ends at the end of the flight."""
        self._tick_id = None
        if self.playback is None:
            return
        self.playback.advance()
        self._draw(force=not self.playback.running)
        if self.playback.running:
            self._schedule_tick()

    # ---------------- drawing ----------------
    def _draw(self, force=False):
        """Moves the instruments and the timeline to the current row (only if it changed, unless force)."""
        if self.playback is None:
            return
        row = self.playback.row
        if row == self.shown_row and not force:
            return
        self.shown_row = row
        track = self.track
        has_rows = track is not None and not track.is_empty
        self.horizon.show(track.attitude(row) if has_rows else None)
        if has_rows:
            for gauge in self.gauges.values():
                gauge.show(track, row)
            self.readouts.show(track, row)
            self.radio.show(track, row, self.stick_mode)
            self.aircraft.show(track, row)
        row_time = float(track.time[row]) if track is not None and not track.is_empty else 0.0
        self.timeline.show(row_time, self.playback.running)

    def _resized(self, _event=None):
        """Draws the static parts again after the size has settled (the first time at once)."""
        if self._resize_id is not None:
            self.frame.after_cancel(self._resize_id)
        if self.layout is None:
            self._relayout()
            return
        self._resize_id = self.frame.after(RESIZE_DELAY_MS, self._relayout)

    def _present(self):
        """Instruments the loaded flight has data for."""
        if self.track is None or self.track.is_empty:
            return set()
        present = set(self.panels)
        if self.track.attitude(0) is not None:
            present.add(HORIZON)
        if has_sticks(self.track):
            present.add(RADIO)
        if has_aircraft(self.track):
            present.add(AIRCRAFT)
        return present

    def _relayout(self):
        """Places the instruments and the timeline for the current size and draws the static parts."""
        self._resize_id = None
        width, height = self.frame.winfo_width(), self.frame.winfo_height()
        if width <= 1 or height <= 1:
            return
        self.layout = recorder_layout(width, height, self._present(), self.line_height)
        timeline = self.layout.rects[TIMELINE]
        self.timeline.frame.place(x=timeline.x, y=timeline.y, width=timeline.width, height=timeline.height)
        horizon = self.layout.rects.get(HORIZON)
        if horizon is not None:
            self.horizon.place(horizon, self.line_height, self.family)
        else:
            self.horizon.show(None)
        for name, gauge in self.gauges.items():
            rect = self.layout.rects.get(name)
            if rect is not None:
                gauge.place(rect, self.line_height, self.family, self.panels[name], self.scales)
            else:
                gauge.hide()
        radio = self.layout.rects.get(RADIO)
        if radio is not None:
            self.radio.place(radio, self.line_height, self.family, self.stick_mode)
        else:
            self.radio.hide()
        aircraft = self.layout.rects.get(AIRCRAFT)
        if aircraft is not None:
            self.aircraft.place(aircraft, self.line_height, self.family, self.track)
        else:
            self.aircraft.hide()
        readouts = self.layout.rects.get(READOUTS)
        if readouts is not None:
            self.readouts.place(readouts, self.line_height, self.family, readout_lines(self.track), self.scales)
        else:
            self.readouts.hide()
        self._show_note(width, timeline.y)
        self._draw(force=True)

    def _show_note(self, width, height):
        """A note in the middle when nothing can be shown."""
        if self.track is None or self.track.is_empty:
            text = tr(NO_ROWS) if self.key is not None else ""
        elif set(self.layout.rects) == {TIMELINE}:
            text = tr(NO_INSTRUMENTS)
        else:
            text = ""
        self.canvas.coords(self.note, width / 2, height / 2)
        self.canvas.itemconfigure(self.note, text=text, width=max(width - 40, 100),
                                  state="normal" if text else "hidden")

    def set_stick_mode(self, mode):
        """The pilot chose another stick mode: the radio is labelled and drawn again at once; the position and the
        playback stay as they are."""
        mode = valid_stick_mode(mode)
        if mode == self.stick_mode:
            return
        self.stick_mode = mode
        radio = self.layout.rects.get(RADIO) if self.layout is not None else None
        if radio is not None:
            self.radio.place(radio, self.line_height, self.family, mode)
            self._draw(force=True)

    # ---------------- language switch, closing ----------------
    def snapshot(self):
        """Position and speed - restored after a language switch."""
        if self.playback is None:
            return None
        return {"position": self.playback.position, "speed": self.playback.speed}

    def restore(self, snap):
        """Restores position and speed for the flight now selected (loads it at once)."""
        if not snap:
            return
        if self.pending_key is not None or self.playback is None:
            self._load_pending()
        self.playback.set_speed(snap["speed"])
        self.timeline.set_speed(snap["speed"])
        self.playback.seek(snap["position"])
        self._draw(force=True)

    def _destroyed(self, event):
        if event.widget is not self.frame:
            return
        for after_id in (self._tick_id, self._resize_id):
            if after_id is not None:
                try:
                    self.frame.after_cancel(after_id)
                except Exception:                    # the interpreter is already shutting down
                    pass
        self._tick_id = self._resize_id = None
        for sequence in KEY_SEQUENCES:
            self.frame.unbind_class(self.key_tag, sequence)
