# -*- coding: utf-8 -*-
"""The position of the flight recorder in the time charts of the single flight (no Tkinter).

The recorder and the charts count the same seconds: time 0 is the start of the motor (``flight_window_times``).
The recorder plays up to the duration of the flight; the time axis of the charts ends up to one grid step
(0.25 s) earlier, so a position beyond it is drawn at the end of the axis. A click in a chart gives a position
that is limited to the flight of the recorder.
"""

# a mouse press and release that moved less than this many pixels is a click, else it was a drag (panning)
CLICK_TOLERANCE_PX = 4


def marker_time(position, chart_start, chart_end):
    """Where the position line is drawn: the recorder position limited to the time axis of the charts."""
    return min(max(float(position), float(chart_start)), float(chart_end))


def position_from_click(chart_time, recorder_start, recorder_end):
    """The recorder position for a click at chart_time [s]: limited to the flight of the recorder."""
    return min(max(float(chart_time), float(recorder_start)), float(recorder_end))


def is_click(press_xy, release_xy, tolerance=CLICK_TOLERANCE_PX):
    """True if the mouse (screen pixels) stayed within the tolerance between press and release."""
    return abs(release_xy[0] - press_xy[0]) <= tolerance and abs(release_xy[1] - press_xy[1]) <= tolerance


def time_axes(figure):
    """The axes of a figure that have the flight time as x axis (the main axes of the single-flight charts, not
    their twin axes); empty for every other figure, e.g. the statistics, and for axes no longer on the figure."""
    if getattr(figure, "_t", None) is None:
        return []
    return [axes for axes in getattr(figure, "_time_axes", []) if axes in figure.axes]
