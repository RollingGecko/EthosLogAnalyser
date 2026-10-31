# -*- coding: utf-8 -*-
"""The position of the flight recorder as a line in the time charts of the single flight (TW-059).

Pure functions and the line itself on figures without a window; the clicks and the tabs are checked in
``recorder_checks.py``.
"""

import tempfile
import time

import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from helpers import ROOT, ela
from ethosloganalyser.db import FlightDatabase, import_paths
from ethosloganalyser.gui.database_flights import aircraft_result, complete_flight
from ethosloganalyser.plots.flight import FLIGHT_VIEWS, draw_flight, fit_y
from ethosloganalyser.plots.hover import Hover, series_points
from ethosloganalyser.plots.position import POSITION_GID, PositionMarker
from ethosloganalyser.recorder.chart_position import (CLICK_TOLERANCE_PX, is_click, marker_time, position_from_click,
                                                      time_axes)
from ethosloganalyser.recorder.flight_track import load_track

LOGS_2026 = ROOT / "examples" / "logs_2026"


# ---------------- pure functions ----------------
def test_the_line_is_limited_to_the_axis_of_the_charts():
    """The axis ends up to 0.25 s before the end of the recorder: a position behind it is drawn at its end."""
    assert marker_time(0.0, 0.0, 178.75) == 0.0                 # start
    assert marker_time(95.5, 0.0, 178.75) == 95.5               # inside
    assert marker_time(179.0, 0.0, 178.75) == 178.75            # recorder end behind the end of the axis
    assert marker_time(-3.0, 0.0, 178.75) == 0.0                # outside


def test_a_click_gives_a_position_inside_the_flight_of_the_recorder():
    assert position_from_click(12.3, 0.0, 179.0) == 12.3
    assert position_from_click(-4.0, 0.0, 179.0) == 0.0
    assert position_from_click(500.0, 0.0, 179.0) == 179.0


def test_a_click_stays_within_a_few_pixels_a_drag_does_not():
    assert is_click((100, 50), (100, 50))
    assert is_click((100, 50), (100 + CLICK_TOLERANCE_PX, 50 - CLICK_TOLERANCE_PX))
    assert not is_click((100, 50), (100 + CLICK_TOLERANCE_PX + 1, 50))
    assert not is_click((100, 50), (100, 50 + CLICK_TOLERANCE_PX + 1))


def test_only_the_charts_with_the_flight_time_get_a_line():
    """Other figures (statistics: flights, dates, no time) and the twin axes of a stick get none."""
    figure = Figure()
    axes = figure.subplots(2, 1)
    assert time_axes(figure) == []                              # an ordinary figure
    figure._t = np.arange(10.0)
    assert time_axes(figure) == []                              # time but no list of time axes
    figure._time_axes = list(axes)
    assert time_axes(figure) == list(axes)
    twin = axes[0].twinx()
    assert twin not in time_axes(figure)
    axes[1].remove()
    assert time_axes(figure) == [axes[0]]                       # an axes that is gone does not count


# ---------------- on the real charts ----------------
@pytest.fixture(scope="module")
def flights():
    """[(log id, analysis row, series, track)] of all example flights that have charts."""
    database = FlightDatabase(tempfile.mkdtemp() + "/position.db")
    import_paths(database, [str(LOGS_2026)], ela.Params())
    try:
        found = []
        for (log_id,) in database.connection.execute(
                "SELECT log_id FROM flight WHERE is_flight = 1 AND metrics IS NOT NULL ORDER BY log_id").fetchall():
            row, series = complete_flight(database.connection, log_id)
            found.append((log_id, row, series, load_track(database.connection, log_id)))
    finally:
        database.close()
    return found


def _figure_of(row, series, view):
    figure = Figure(figsize=(12, 7), dpi=100)
    result = aircraft_result({row["pfad"]: (row, series)}, ela.Params(), "test")      # adds the columns the charts use
    draw_flight(figure, result, ela.Params(), row["pfad"], view)
    return figure


def _marker_of(figure, position):
    canvas = FigureCanvasAgg(figure)
    hover = Hover(canvas, crosshair=True)
    marker = PositionMarker(canvas, hover)
    marker.attach(figure, position)
    return canvas, hover, marker


def test_time_zero_of_the_recorder_and_of_the_charts_is_the_same_place(flights):
    """x = 0 of the charts is the start of the motor, like time 0 of the recorder; the axis never ends later."""
    assert len(flights) >= 33
    for log_id, _row, series, track in flights:
        chart_time = series["t"]
        assert chart_time[0] == pytest.approx(0.0, abs=1e-9), log_id
        assert track.time[0] == 0.0, log_id
        assert 0 <= track.end_time - chart_time[-1] < 0.25 + 1e-6, log_id
        assert marker_time(track.end_time, chart_time[0], chart_time[-1]) == chart_time[-1]


def test_every_view_has_a_line_on_each_time_chart_and_not_on_the_twin_axes(flights):
    _log_id, row, series, _track = flights[-1]
    for view in FLIGHT_VIEWS:
        figure = _figure_of(row, series, view)
        if not figure.axes:
            assert time_axes(figure) == []                              # "no data in this view": no line, no error
            continue
        axes = time_axes(figure)
        assert axes and all(axes_.get_subplotspec() is not None for axes_ in axes)
        _canvas, _hover, marker = _marker_of(figure, 12.5)
        assert [line.get_xdata()[0] for line in marker.lines] == [12.5] * len(axes)
        if view == "attitude":
            assert len(figure.axes) > len(axes)                         # the sticks sit on twin axes: no extra line


def test_the_line_changes_neither_axes_nor_tooltip_nor_fit_y(flights):
    _log_id, row, series, _track = flights[-1]
    figure = _figure_of(row, series, FLIGHT_VIEWS[0])
    before_limits = [(a.get_xlim(), a.get_ylim()) for a in figure.axes]
    before_series = [len(series_points(a)) for a in figure.axes]
    canvas, _hover, marker = _marker_of(figure, 30.0)
    canvas.draw()
    marker.move(60.0)
    marker.move(1e6)                                                    # beyond the end: drawn at the end
    assert marker.lines[0].get_xdata()[0] == series["t"][-1]
    fit_y(time_axes(figure))
    assert [(a.get_xlim(), a.get_ylim()) for a in figure.axes] == before_limits
    assert [len(series_points(a)) for a in figure.axes] == before_series
    assert all(line.get_gid() == POSITION_GID and line.get_label().startswith("_") for line in marker.lines)
    assert all(list(line.get_ydata()) == [0.0, 1.0] for line in marker.lines)


def test_the_line_is_moved_not_created_and_can_be_hidden(flights):
    _log_id, row, series, _track = flights[-1]
    figure = _figure_of(row, series, FLIGHT_VIEWS[0])
    canvas, _hover, marker = _marker_of(figure, 0.0)
    canvas.draw()
    lines = list(marker.lines)
    count = sum(len(a.lines) for a in figure.axes)
    marker.move(40.0)
    marker.move(41.0)
    assert marker.lines == lines and sum(len(a.lines) for a in figure.axes) == count
    assert all(line.get_xdata()[0] == 41.0 and line.get_visible() for line in lines)
    marker.move(None)                                                   # a flight without a track: no line
    assert not any(line.get_visible() for line in lines)
    marker.move(2.0)
    assert all(line.get_visible() for line in lines)


def test_moving_the_line_is_much_faster_than_drawing_the_page(flights):
    """Moving by blitting (target: under 20 ms; the screen copy itself is left out on this canvas)."""
    _log_id, row, series, _track = flights[-1]
    figure = _figure_of(row, series, FLIGHT_VIEWS[0])
    canvas, _hover, marker = _marker_of(figure, 0.0)
    start = time.perf_counter()
    canvas.draw()
    draw_ms = (time.perf_counter() - start) * 1000
    canvas.blit = lambda *_: None
    start = time.perf_counter()
    for k in range(20):
        marker.move(float(k + 1))
    move_ms = (time.perf_counter() - start) * 1000 / 20
    print(f"draw {draw_ms:.1f} ms, move {move_ms:.2f} ms")
    assert move_ms < 20 and move_ms < draw_ms
