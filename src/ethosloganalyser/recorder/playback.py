# -*- coding: utf-8 -*-
"""The playback clock of the flight recorder.

The position is not counted up tick by tick but worked out from a wall clock: position = position at the start
+ (now - start time) x speed. A timer tick that Windows delivers late therefore does not slow the playback down.
The wall clock is passed in (default ``time.perf_counter``), so tests can move it without waiting.

The clock knows the log times of the rows of the flight (``FlightTrack.time`` up to its end row) and stops at the
end of the flight; playing again from there starts at the beginning.
"""

import time

import numpy as np

SPEEDS = (0.25, 0.5, 1, 2, 4, 8, 16)   # playback speed steps (x real time)
DEFAULT_SPEED = 1
TICK_MS = 40                           # timer interval of the page: 25 checks per second
JUMP_S = 10.0                          # Shift+arrow jumps this far


class PlaybackClock:
    """Position, speed and running state of a playback over the rows of one flight."""

    def __init__(self, row_times, clock=time.perf_counter):
        self.row_times = np.asarray(row_times, dtype=float)
        self.clock = clock
        self.speed = DEFAULT_SPEED
        self.running = False
        self._position = self.start            # position when the clock was last anchored
        self._anchor_wall = None               # wall-clock time of that anchor while running

    # ---------------- limits ----------------
    @property
    def start(self):
        return float(self.row_times[0]) if len(self.row_times) else 0.0

    @property
    def end(self):
        return float(self.row_times[-1]) if len(self.row_times) else 0.0

    @property
    def at_end(self):
        return self.position >= self.end

    # ---------------- position ----------------
    @property
    def position(self):
        """The current log time [s] (moves with the wall clock while running; not beyond the end)."""
        if not self.running:
            return self._position
        return min(self._position + (self.clock() - self._anchor_wall) * self.speed, self.end)

    @property
    def row(self):
        """Index of the row that holds at the current position."""
        if not len(self.row_times):
            return 0
        return max(int(np.searchsorted(self.row_times, self.position, side="right")) - 1, 0)

    def _anchor(self, position):
        """Continues from position (running or not)."""
        self._position = min(max(float(position), self.start), self.end)
        self._anchor_wall = self.clock() if self.running else None

    def advance(self):
        """Called by the timer: stops the clock at the end of the flight. Returns the current position."""
        if self.running and self.position >= self.end:
            self._position, self.running, self._anchor_wall = self.end, False, None
        return self.position

    def seek(self, position):
        """Jumps to a log time (limited to the flight); a running clock keeps running from there."""
        self._anchor(position)

    def jump(self, seconds):
        """Moves the position by seconds (e.g. +/- JUMP_S)."""
        self.seek(self.position + seconds)

    def step_rows(self, count):
        """Stops and moves count log rows forward (count > 0) or back."""
        self.stop()
        row = min(max(self.row + count, 0), len(self.row_times) - 1) if len(self.row_times) else 0
        self._anchor(self.row_times[row] if len(self.row_times) else 0.0)

    def go_to_start(self):
        self.seek(self.start)

    def go_to_end(self):
        self.stop()
        self.seek(self.end)

    # ---------------- running ----------------
    def play(self):
        """Starts the playback; at the end of the flight it starts again from the beginning."""
        if self.running:
            return
        position = self.start if self.at_end else self._position
        self.running = True
        self._anchor(position)

    def stop(self):
        """Stops the playback at the current position."""
        if not self.running:
            return
        position = self.position
        self.running = False
        self._anchor(position)

    def toggle(self):
        """Play/stop with one button."""
        if self.running:
            self.stop()
        else:
            self.play()

    def set_speed(self, speed):
        """Changes the speed without a jump of the position."""
        if speed not in SPEEDS:
            raise ValueError(f"unknown speed {speed!r}")
        position = self.position
        self.speed = speed
        self._anchor(position)
