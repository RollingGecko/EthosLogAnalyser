# -*- coding: utf-8 -*-
"""Chart basics shared by all charts: time format, time axes, mouse-over tooltip."""

import time

import numpy as np
import pandas as pd
import pytest

import helpers  # noqa: F401  (src on the path, Agg backend)
from matplotlib.backend_bases import MouseEvent
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from ethosloganalyser.i18n import get_language, set_language
from ethosloganalyser.plots.common import flight_hover, hover_info, time_axis, time_ticks
from ethosloganalyser.plots.hover import Hover, nearest, point_text, series_points
from ethosloganalyser.utils import _mmss, fmt_duration


@pytest.fixture(autouse=True)
def german():
    old = get_language()
    set_language("de")
    yield
    set_language(old)


# ---------------------------------------------------------------- time format

@pytest.mark.parametrize("s, text", [
    (0, "0:00"), (0.4, "0:00"), (59.4, "0:59"), (59.9, "1:00"), (60, "1:00"), (75, "1:15"), (538, "8:58"),
    (3599, "59:59"), (3599.6, "1:00:00"), (3600, "1:00:00"), (3725, "1:02:05"), (36000, "10:00:00"),
    (-75, "-1:15"), (-0.3, "0:00")])
def test_duration_format(s, text):
    assert fmt_duration(s) == text


@pytest.mark.parametrize("missing", [None, np.nan, float("inf"), "abc", pd.NA])
def test_missing_duration_is_a_dash(missing):
    assert fmt_duration(missing) == "–"
    assert fmt_duration(missing, na="") == ""


def test_duration_with_unit():
    assert fmt_duration(538, unit=True) == _mmss(538) == "8:58 min"
    assert fmt_duration(3725, unit=True) == "1:02:05 h"


def test_time_ticks_fall_on_round_times():
    assert list(time_ticks(0, 540)) == [0, 60, 120, 180, 240, 300, 360, 420, 480, 540]
    assert list(time_ticks(10, 50)) == [10, 15, 20, 25, 30, 35, 40, 45, 50]
    assert len(time_ticks(0, 20000)) <= 11
    assert len(time_ticks(5, 5)) == 0


def test_time_axis_labels_in_min_s():
    fig = Figure()
    ax = fig.subplots()
    ax.plot([0, 300, 600], [1, 2, 3])
    time_axis(ax, "x")
    FigureCanvasAgg(fig).draw()
    labels = [t.get_text() for t in ax.get_xticklabels() if t.get_text()]
    assert labels[0] == "0:00" and "10:00" in labels
    assert ax._hover["x"](75) == "t = 1:15"


# ---------------------------------------------------------------- nearest point

def test_nearest_point_in_screen_coordinates():
    pts = [np.array([[0, 0], [10, 10], [np.nan, np.nan]]), np.array([[100, 100]])]
    assert nearest(pts, 11, 9) == (0, 1, pytest.approx(np.sqrt(2)))
    assert nearest(pts, 96, 97)[:2] == (1, 0)
    assert nearest(pts, 50, 50, max_dist=25) is None
    assert nearest([None, np.empty((0, 2))], 1, 1) is None


def test_helper_lines_are_not_data():
    fig = Figure()
    ax = fig.subplots()
    ax.plot([1, 2, 3], [4, 5, 6], label="Daten")
    ax.plot([1, 3], [4, 6], "--")                    # 2-point trend line
    ax.plot([2], [5], "o", label="Punkt")           # single marker: data
    ax.axhline(5)
    ax.axvline(2)
    names = [s[0] for s in series_points(ax)]
    assert names == ["Daten", "Punkt"]


def test_stacked_bars_show_the_segment_value():
    fig = Figure()
    ax = fig.subplots()
    ax.bar([1, 2], [3, 4], label="unten")
    ax.bar([1, 2], [10, 20], bottom=[3, 4], label="oben")
    pts = {s[0]: s for s in series_points(ax)}
    _, x, y, v = pts["oben"]
    assert list(y) == [13, 24] and list(v) == [10, 20]


# ---------------------------------------------------------------- tooltip

def _hover_at(fig, ax, x, y):
    canvas = FigureCanvasAgg(fig)
    h = Hover(canvas)
    canvas.draw()
    px, py = ax.transData.transform((x, y))
    canvas.callbacks.process("motion_notify_event", MouseEvent("motion_notify_event", canvas, px + 2, py - 2))
    return h


def test_tooltip_shows_series_flight_and_unit():
    df = pd.DataFrame({"Flug": [1, 2, 3], "datum": pd.to_datetime(["2026-04-19 12:05", "2026-04-19 13:25",
                                                                 "2026-05-04 12:23"])})
    fig = Figure()
    ax = fig.subplots()
    ax.plot(df["Flug"], [8611, 8642, 8980], "o", label="Kapazität")
    ax.set_title("Geschätzte Gesamtkapazität [mAh]", loc="left")
    flight_hover(ax, df)
    h = _hover_at(fig, ax, 2, 8642)
    txt = h._text()
    assert txt.get_visible()
    assert txt.get_text() == "Kapazität\nFlug 2 – 19.04.2026 13:25\n8642 mAh"


def test_tooltip_finds_points_on_twin_axes_and_scatter():
    fig = Figure()
    ax = fig.subplots()
    ax.plot([0, 60, 120], [10, 20, 30], label="Strom")
    ax.set_ylabel("Strom [A]")
    time_axis(ax, "x")
    ax2 = ax.twinx()
    ax2.scatter([90], [500], label="Höhe")
    ax2.set_ylabel("Höhe [m]")
    h = _hover_at(fig, ax2, 90, 500)
    assert h._text().get_text() == "Höhe\nx = 90\n500 m"
    h = _hover_at(fig, ax, 60, 20)
    assert h._text().get_text() == "Strom\nt = 1:00\n20 A"


def test_point_text_uses_the_axis_unit_and_names():
    fig = Figure()
    ax = fig.subplots()
    ax.set_title("Spitzenleistung je Flug [W]", loc="left")
    assert point_text(ax, "_child0", 3, 5442.4) == "Spitzenleistung je Flug [W]\nx = 3\n5442 W"
    hover_info(ax, y=lambda v: f"{v:.1f} V")
    assert point_text(ax, "Spannung", 3, 3.95).endswith("4.0 V")


def test_tooltip_is_fast_with_many_points():
    # a long log (about 8000 rows, several series) must not make the mouse lag
    n = 12000
    t = np.linspace(0, 2000, n)
    fig = Figure(figsize=(12, 8))
    axes = fig.subplots(4, 1, sharex=True)
    for k, a in enumerate(axes):
        a.plot(t, np.sin(t / (10 + k)) * 10 + k)
        a.plot(t, np.cos(t / (7 + k)) * 5 + k)
    canvas = FigureCanvasAgg(fig)
    h = Hover(canvas, crosshair=True)
    canvas.draw()
    bb = axes[1].bbox
    xs = np.linspace(bb.x0 + 5, bb.x1 - 5, 200)
    start = time.perf_counter()
    for x in xs:
        canvas.callbacks.process("motion_notify_event", MouseEvent("motion_notify_event", canvas, x, bb.y0 + 0.5 * bb.height))
    per_event = (time.perf_counter() - start) / len(xs)
    assert per_event < 0.05, per_event          # well below a frame at 20 Hz, also on slow CI runners
    assert h._series and sum(len(s[2]) for s in h._series) == 8 * n


def test_tooltip_survives_a_cleared_figure():
    fig = Figure()
    canvas = FigureCanvasAgg(fig)
    h = Hover(canvas)
    ax = fig.subplots()
    ax.plot([1, 2, 3], [1, 2, 3], "o")
    canvas.draw()
    h._show(h.find(*ax.transData.transform((2, 2))), 2, (10, 10))
    fig.clear()                                  # e.g. another view of the single flight
    ax = fig.subplots()
    ax.plot([1, 2, 3], [3, 2, 1], "o", label="neu")
    canvas.draw()
    px, py = ax.transData.transform((3, 1))
    canvas.callbacks.process("motion_notify_event", MouseEvent("motion_notify_event", canvas, px, py))
    assert h._text().get_text().startswith("neu") and h._text().figure is fig


# ---------------------------------------------------------------- table and CSV export

def test_csv_export_keeps_seconds_and_adds_min_s_columns():
    from ethosloganalyser.gui.common import export_table, fmt_cell
    df = pd.DataFrame({"Flug": [1, 2], "dauer_s": [482.6, np.nan], "Timer_s": [538.0, 3725.0], "pfad": ["a", "b"]})
    out = export_table(df)
    assert list(out.columns) == ["Flug", "dauer_s", "dauer_mmss", "Timer_s", "Timer_mmss"]
    assert out["dauer_s"].tolist()[0] == 482.6                     # seconds unchanged for existing evaluations
    assert out["dauer_mmss"].tolist() == ["8:03", ""]
    assert out["Timer_mmss"].tolist() == ["8:58", "1:02:05"]
    assert fmt_cell("dauer_s", 482.6) == "8:03" and fmt_cell("Timer_s", np.nan) == "–"
