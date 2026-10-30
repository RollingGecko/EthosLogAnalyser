# -*- coding: utf-8 -*-
"""GUI checks of the flight recorder (called from test_gui.py, which owns the one window of the test session).

The playback runs with a wall clock the checks move themselves, and the timer ticks are called directly, so
nothing waits for real time.
"""

import pytest

from ethosloganalyser.gui.recorder_page import KEY_SEQUENCES
from ethosloganalyser.recorder.layout import (ALTITUDE, BATTERY, HORIZON, MINIMAL, READOUTS, RPM_THROTTLE,
                                              SIDE_GAUGES, TIMELINE, VERTICAL_SPEED)
from ethosloganalyser.recorder.readouts import NO_VALUE
from ethosloganalyser.recorder.playback import SPEEDS


class FakeClock:
    """Wall clock that only moves when a check says so."""

    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def _open_recorder(root):
    """Shows the single flight with the tab Flight recorder; returns (flight page, recorder, clock)."""
    h = root._akku
    page, recorder = h["flight_page"], h["recorder"]
    clock = FakeClock()
    recorder.clock_function = clock
    h["select_page"]("flight")
    page.select_tab("recorder")
    root.update()
    return page, recorder, clock


def check_recorder(root):
    """Tabs, playback with speed and end, timeline click, keys, stopping when the tab or the page is left, and
    position and speed after a language switch."""
    h = root._akku
    page, recorder, clock = _open_recorder(root)
    assert [page.tabs.tab(tab, "text") for tab in page.tabs.tabs()] == ["Diagramme", "Flugrekorder"]
    assert recorder.active and recorder.track is not None and recorder.key == page.current_key()
    assert not page.details_frame.winfo_ismapped()                  # details, note and anomalies: Charts only
    assert recorder.horizon.visible and recorder.layout.rects[HORIZON].width > 100
    timeline = recorder.layout.rects[TIMELINE]
    assert recorder.timeline.frame.winfo_reqheight() <= timeline.height    # buttons and track fit at this font
    _check_gauges(root, recorder)
    _check_playback(root, recorder, clock)
    _check_timeline_and_keys(root, recorder)

    recorder.toggle()
    page.select_flight()                                            # the same flight again (aircraft prepared)
    assert recorder.playback.running                                # ... does not stop the playback
    page.step_flight(-1)                                            # another flight stops it and starts at 0
    root.update()
    assert not recorder.playback.running and recorder.playback.position == recorder.track.start_time
    page.step_flight(1)
    root.update()
    recorder.toggle()
    page.select_tab("charts")                                       # another tab stops the playback
    root.update()
    assert not recorder.playback.running and not recorder.active and page.details_frame.winfo_ismapped()
    page.select_tab("recorder")
    root.update()
    recorder.toggle()
    h["select_page"]("logbook")                                     # leaving the single flight stops it too
    root.update()
    assert not recorder.playback.running
    _check_language_switch(root)
    h = root._akku
    h["flight_page"].select_tab("charts")
    root.update()


def _check_playback(root, recorder, clock):
    """Play at 1x and 4x with the moved wall clock; only a row change draws; the end of the flight stops it."""
    playback, track = recorder.playback, recorder.track
    assert playback.position == track.start_time and recorder.shown_row == 0
    recorder.toggle()
    assert playback.running and recorder.timeline.play_button.cget("text") == "■ Stopp"
    clock.now += 0.1                                                # less than one log row: nothing is drawn
    shown = recorder.shown_row
    recorder.tick()
    assert recorder.shown_row == shown
    clock.now += 1.0
    recorder.tick()
    assert playback.position == pytest.approx(1.1) and recorder.shown_row == track.row_at(1.1) > 0
    recorder.timeline.speed_scale.set(SPEEDS.index(4))               # the slider snaps to the steps
    root.update()
    assert playback.speed == 4 and recorder.timeline.speed_label.cget("text") == "4×"
    clock.now += 1.0
    recorder.tick()
    assert playback.position == pytest.approx(5.1)
    assert recorder.timeline.time_label.cget("text").startswith("0:05 / ")
    recorder.seek(track.end_time - 1)
    clock.now += 1.0
    recorder.tick()                                                 # 4 s later: beyond the end of the flight
    assert not playback.running and playback.at_end and recorder.timeline.play_button.cget("text") == "▶ Abspielen"
    recorder.toggle()                                               # play at the end starts again from the start
    assert playback.running and playback.position == track.start_time
    recorder.stop()
    recorder.timeline.speed_scale.set(SPEEDS.index(1))
    root.update()


def _check_gauges(root, recorder):
    """The four gauges of the Viper-Jet logs are shown next to the horizon in the order of the user; pointers and
    numbers follow the row."""
    rects = recorder.layout.rects
    if recorder.layout.mode == MINIMAL:                              # the screen of a test machine may be small
        assert READOUTS in rects and len(recorder.readouts.numbers) == 6
        return
    assert all(recorder.gauges[name].visible for name in SIDE_GAUGES)
    assert rects[ALTITUDE].x < rects[VERTICAL_SPEED].x and rects[RPM_THROTTLE].x < rects[BATTERY].x
    assert rects[ALTITUDE].y < rects[RPM_THROTTLE].y and rects[VERTICAL_SPEED].y < rects[BATTERY].y
    canvas, track = recorder.canvas, recorder.track
    altitude, drive, battery = recorder.gauges[ALTITUDE], recorder.gauges[RPM_THROTTLE], recorder.gauges[BATTERY]
    assert canvas.itemcget(altitude.number, "text") in ("0 m", "1 m", "−1 m", NO_VALUE)   # starts at about 0 m
    pointer_at_start = canvas.coords(altitude.pointer)
    middle = track.start_time + (track.end_time - track.start_time) / 2
    recorder.seek(middle)
    root.update()
    row = recorder.shown_row
    assert canvas.coords(altitude.pointer) != pointer_at_start      # the pointer moved with the row
    assert canvas.itemcget(altitude.number, "text").endswith(" m")
    assert canvas.itemcget(altitude.number, "text") != NO_VALUE
    assert canvas.itemcget(drive.bar_number, "text").endswith(" %")
    assert " V" in canvas.itemcget(battery.bar_number, "text")
    recorder.press_key("<Right>")                                    # one row on: only moved, nothing created
    items = len(canvas.find_all())
    recorder.press_key("<Right>")
    assert len(canvas.find_all()) == items and recorder.shown_row == row + 2
    recorder.press_key("<Home>")
    root.update()


def _check_timeline_and_keys(root, recorder):
    """A click on the middle of the track jumps there; keys step rows and play/stop."""
    track, canvas = recorder.track, recorder.timeline.track
    left, right = recorder.timeline._ends
    canvas.event_generate("<ButtonPress-1>", x=int((left + right) / 2), y=5)
    canvas.event_generate("<ButtonRelease-1>", x=int((left + right) / 2), y=5)
    root.update()
    middle = track.start_time + (track.end_time - track.start_time) / 2
    assert recorder.playback.position == pytest.approx(middle, abs=(track.end_time - track.start_time) / 100)
    # the keys are bound to the canvas and the timeline; their actions are called directly, because a window in the
    # background of a test machine (Windows) may not get the keyboard focus that event_generate needs
    bound = set(recorder.canvas.bind_class(recorder.key_tag))
    assert len(bound) == len(KEY_SEQUENCES) and recorder.key_tag in recorder.canvas.bindtags()
    assert recorder.key_tag in recorder.timeline.track.bindtags()
    row = recorder.playback.row
    recorder.press_key("<Right>")
    root.update()
    assert recorder.playback.row == row + 1 and recorder.shown_row == row + 1
    recorder.press_key("<Left>")
    recorder.press_key("<Shift-Left>")
    root.update()
    assert recorder.playback.position == pytest.approx(track.time[row] - 10, abs=0.01)
    recorder.press_key("<space>")
    root.update()
    assert recorder.playback.running
    recorder.press_key("<space>")
    recorder.press_key("<Home>")
    root.update()
    assert not recorder.playback.running and recorder.playback.position == track.start_time
    recorder.press_key("<End>")
    assert recorder.playback.at_end
    recorder.press_key("<Shift-Right>")
    assert recorder.playback.at_end
    recorder.press_key("<Home>")


def _check_language_switch(root):
    """The tab, the position and the speed stay after a language switch."""
    h = root._akku
    h["select_page"]("flight")
    h["flight_page"].select_tab("recorder")
    root.update()
    recorder = h["recorder"]
    recorder.seek(42.0)
    recorder.timeline.speed_scale.set(SPEEDS.index(2))
    root.update()
    h["set_language"]("en")
    root.update()
    h = root._akku
    recorder = h["recorder"]
    assert h["flight_page"].current_tab() == "recorder" and recorder.active
    assert recorder.playback.position == pytest.approx(recorder.track.time[recorder.track.row_at(42.0)], abs=0.3)
    assert recorder.playback.speed == 2 and recorder.timeline.speed_label.cget("text") == "2×"
    assert h["flight_page"].tabs.tab(1, "text") == "Flight recorder"
    h["set_language"]("de")
    root.update()


def check_recorder_without_attitude(root):
    """A flight without attitude, RPM and battery columns (the glider of the opened copy): the recorder opens,
    the horizon, drive and battery are hidden, altitude and vertical speed take the space."""
    h = root._akku
    glider = next(flight for flight in h["flight_cache"].flights if flight.aircraft == "Glider")
    assert h["flight_area"].open_flight(glider.log_id)
    page, recorder, _clock = _open_recorder(root)
    assert recorder.key == glider.log_id and recorder.track is not None and not recorder.track.is_empty
    assert not recorder.horizon.visible and HORIZON not in recorder.layout.rects
    rects = recorder.layout.rects
    assert RPM_THROTTLE not in rects and BATTERY not in rects and not recorder.gauges[BATTERY].visible
    assert recorder.canvas.itemcget(recorder.gauges[BATTERY].pointer, "state") == "hidden"
    assert recorder.canvas.itemcget(recorder.note, "state") == "hidden"      # the gauges show, no note
    if recorder.layout.mode == MINIMAL:                              # the screen of a test machine may be small
        assert list(recorder.readouts.numbers) == ["altitude", "vertical_speed"]
    else:
        assert ALTITUDE in rects and VERTICAL_SPEED in rects and recorder.gauges[ALTITUDE].visible
        assert recorder.canvas.itemcget(recorder.gauges[ALTITUDE].number, "text").endswith(" m")
    recorder.toggle()                                               # the timeline works without instruments
    assert recorder.playback.running
    recorder.stop()
    page.select_tab("charts")
    h["select_page"]("logbook")
    root.update()


def check_recorder_font_fit(root, factor):
    """At the fonts of a display scaling (factor 1.0, 1.25, 1.5; the default font is already scaled by the
    caller), the timeline with its buttons fits into the height the layout gives it. Its controls fit into the
    width of a normal window at every scaling and of a small window (600 px) at 100 %; how wide the text is
    depends on the fonts of the test machine, so a small window at 150 % is not required to fit."""
    import tkinter as tk
    from tkinter import font as tkfont, ttk
    from ethosloganalyser.gui.recorder_page import RecorderPage
    from ethosloganalyser.recorder.layout import timeline_height

    style = ttk.Style(root)
    family = tkfont.nametofont("TkDefaultFont").actual("family")
    style.configure(".", font=(family, round(10 * factor)))           # the font of buttons and labels
    # a normal window as wide as the screen allows (Tk limits a window to the screen, the screen of a test machine
    # may be small) and a small window
    screen = (root.winfo_screenwidth(), root.winfo_screenheight())
    sizes = ((min(1280, screen[0] - 40), min(720, screen[1] - 80)), (600, 400))
    try:
        for width, height in sizes:
            window = tk.Toplevel(root)                                  # a new window per size (no window manager)
            window.geometry(f"{width}x{height}")
            try:
                page = RecorderPage(window, family)
                root.update()
                width = page.frame.winfo_width()                        # what the window really got
                assert page.timeline.frame.winfo_reqheight() <= timeline_height(page.line_height), (factor, width)
                assert page.layout.rects[TIMELINE].height == timeline_height(page.line_height)
                controls = page.timeline.controls
                if width >= 900 or factor == 1.0:
                    assert controls.winfo_reqwidth() <= width - 16, (factor, width, controls.winfo_reqwidth())
            finally:
                window.destroy()
    finally:
        style.configure(".", font=(family, 10))                         # as set by gui/style.py
