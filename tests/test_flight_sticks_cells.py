# -*- coding: utf-8 -*-
"""Single flight: stick positions in the attitude view and battery voltage per cell."""

import numpy as np
import pandas as pd
import pytest

import helpers
from matplotlib.backends.backend_agg import FigureCanvasAgg

from ethosloganalyser.analysis.fleet import Result
from ethosloganalyser.analysis.flight import analyse_file
from ethosloganalyser.config import CHEM, Params
from ethosloganalyser.i18n import get_language, set_language
from ethosloganalyser.plots.flight import battery_voltage, cell_count, figure_flight, fit_y
from ethosloganalyser.plots.single import chart_title, single_chart
from test_single_chart import check_page


@pytest.fixture(autouse=True)
def german():
    old = get_language()
    set_language("de")
    yield
    set_language(old)


# ---------------------------------------------------------------- voltage per cell

@pytest.mark.parametrize("value, cells", [(13, 13), (13.0, 13), (6.0, 6), (np.nan, None), (0, None), (None, None),
                                          ("x", None)])
def test_cell_count(value, cells):
    assert cell_count(pd.Series({"Zellen": value})) == cells


def test_cell_count_without_column():
    assert cell_count(pd.Series({"Flug": 1})) is None


def test_battery_voltage_per_cell():
    u = np.array([54.6, 48.1, 41.6])
    v, unit, per_cell = battery_voltage(u, 13)
    assert per_cell and unit == "V/Zelle"
    assert v == pytest.approx([4.2, 3.7, 3.2])


def test_battery_voltage_without_cell_count_is_total():
    u = np.array([54.6, 48.1])
    v, unit, per_cell = battery_voltage(u, None)
    assert not per_cell and unit == "V"
    assert v == pytest.approx(u)
    assert battery_voltage(None, 13) == (None, "V", False)


def test_battery_voltage_translated():
    set_language("en")
    assert battery_voltage(np.array([4.0]), 1)[1] == "V/cell"


# ---------------------------------------------------------------- synthetic flight with stick channels

def _flight_log(folder, sticks=("QR", "HR", "SR"), gas=True, attitude=True):
    """Log of a 4-minute flight with stick channels in Ethos units (-1024 ... +1024)."""
    t = np.arange(0, 260, 0.2)
    run = (t > 10) & (t < 250)
    i = np.where(run, 40 + 20 * np.sin(t / 7), 0.2)
    u = 54.0 - 0.003 * t - 0.012 * i
    extra = {}
    wave = lambda per, amp: np.round(amp * np.sin(2 * np.pi * t / per))
    if "QR" in sticks:
        extra["QR"] = np.clip(wave(9, 1100), -1024, 1024)            # beyond full deflection: clipped to 100 %
    if "HR" in sticks:
        extra["HR"] = wave(13, 512)                                   # half deflection
    if "SR" in sticks:
        extra["SR"] = wave(17, -256)
    if gas:
        extra["Gas"] = np.where(run, 1024, -1024)
    if attitude:
        extra["Roll(°)"] = np.round(60 * np.sin(2 * np.pi * t / 9), 1)
        extra["Pitch(°)"] = np.round(20 * np.sin(2 * np.pi * t / 13), 1)
    return helpers.write_ethos_csv(folder, "Model-2026-05-01-12-00-00.csv", t, u, i, extra)


def _result(path, cells=13):
    p = Params(cells=cells, chem="Li-Ion", nominal_mah=9000)
    row, msg = analyse_file(str(path), p)
    assert row is not None, msg
    series = {row["pfad"]: row.pop("_series")}
    df = pd.DataFrame([row])
    df.insert(0, "Flug", 1)
    df["Zellen"] = cells if cells else np.nan
    df["Ri_Zelle_mOhm"] = df["Ri_mOhm"] / (cells or 1)
    df["Timer_s"] = np.nan
    return Result(df, [], 1, series, {}), p, row["pfad"]


def test_stick_channels_are_scaled_to_percent():
    res, _, path = _result(_flight_log(helpers.tmpdir()))
    s = res.series[path]
    st = s["sticks"]
    assert set(st) == {"aileron", "elevator", "rudder"}
    assert st["aileron"].max() == pytest.approx(100, abs=0.5) and st["aileron"].min() == pytest.approx(-100, abs=0.5)
    assert np.abs(st["elevator"]).max() == pytest.approx(50, abs=1)
    assert np.abs(st["rudder"]).max() == pytest.approx(25, abs=1)
    assert s["gas"].max() == pytest.approx(100)                  # throttle: -1024 ... +1024 -> 0 ... 100 %


def _attitude(res, p, path):
    fig = figure_flight(res, p, path, "attitude")
    FigureCanvasAgg(fig).draw()
    return fig, {chart_title(a): a for a in fig.axes if a.get_title(loc="left")}


def test_attitude_view_shows_sticks_with_angles():
    res, p, path = _result(_flight_log(helpers.tmpdir()))
    fig, charts = _attitude(res, p, path)
    # (no acceleration in the synthetic log: no g-load chart)
    assert list(charts) == ["Rollwinkel und Querruder", "Nickwinkel und Höhenruder", "Gas und Seitenruder", "Drehrate"]
    roll = charts["Rollwinkel und Querruder"]
    twins = [a for a in fig.axes if a is not roll and a.get_subplotspec() == roll.get_subplotspec()]
    assert len(twins) == 1
    tw = twins[0]
    assert [ln.get_label() for ln in tw.lines] == ["Querruder (Knüppel)"]
    assert tw.get_ylim() == (-105, 105) and tw.get_ylabel() == "%"
    lo, hi = roll.get_ylim()
    assert lo == pytest.approx(-hi)                                # angle centred on 0, like the stick axis
    assert tw.get_shared_x_axes().joined(tw, roll)
    assert tw._hover["y"](12.34) == "12.34 %" and tw._hover["x"](75).startswith("t = 1:15")
    labels = [t.get_text() for t in (tw.get_legend() or roll.get_legend()).get_texts()]
    assert labels == ["Roll", "Querruder (Knüppel)"]               # one legend for both axes
    names = [r[0] for r in fig._readout]
    assert {"Querruder (Knüppel)", "Höhenruder (Knüppel)", "Seitenruder (Knüppel)", "Gas"} <= set(names)
    # zoom: the stick axis keeps its range, the angle stays symmetric
    roll.set_xlim(20, 40)
    fit_y([roll])
    assert tw.get_ylim() == (-105, 105)
    lo, hi = roll.get_ylim()
    assert lo == pytest.approx(-hi)


def test_attitude_charts_can_be_enlarged_alone():
    res, p, path = _result(_flight_log(helpers.tmpdir()))
    check_page(lambda: figure_flight(res, p, path, "attitude"))
    fig = figure_flight(res, p, path, "attitude")
    kept = single_chart(fig, 0)
    assert len(kept) == 2 and kept[1].get_ylabel() == "%"


def test_missing_stick_channels_are_left_out_with_a_hint():
    res, p, path = _result(_flight_log(helpers.tmpdir(), sticks=("QR",)))
    fig, charts = _attitude(res, p, path)
    assert "Nickwinkel und Höhenruder" in charts                   # pitch angle still shown, without stick
    pitch = charts["Nickwinkel und Höhenruder"]
    assert not [a for a in fig.axes if a is not pitch and a.get_subplotspec() == pitch.get_subplotspec()]
    texts = [t.get_text() for a in fig.axes for t in a.texts]
    assert any("Nicht im Log oder nicht bewegt: HR, SR." in t for t in texts)
    assert [ln.get_label() for ln in charts["Gas und Seitenruder"].lines if ln.get_gid() == "data"] == ["Gas"]


def test_no_sticks_and_no_throttle():
    res, p, path = _result(_flight_log(helpers.tmpdir(), sticks=(), gas=False))
    fig, charts = _attitude(res, p, path)
    assert "Gas und Seitenruder" not in charts
    assert any("Nicht im Log oder nicht bewegt: QR, HR, SR, Gas." in t.get_text() for a in fig.axes for t in a.texts)


def test_stick_without_attitude_is_shown_alone():
    res, p, path = _result(_flight_log(helpers.tmpdir(), attitude=False))
    fig, charts = _attitude(res, p, path)
    roll = charts["Rollwinkel und Querruder"]
    assert roll.get_ylabel() == "%" and [ln.get_label() for ln in roll.lines if ln.get_gid() == "data"] == [
        "Querruder (Knüppel)"]


# ---------------------------------------------------------------- battery view per cell

def _battery(res, p, path):
    fig = figure_flight(res, p, path, "battery")
    FigureCanvasAgg(fig).draw()
    return fig, fig.axes[0]


def test_battery_view_per_cell():
    res, p, path = _result(_flight_log(helpers.tmpdir()), cells=13)
    fig, ax = _battery(res, p, path)
    assert chart_title(ax) == "Akkuspannung je Zelle" and ax.get_ylabel() == "V/Zelle"
    data = [ln for ln in ax.lines if ln.get_gid() == "data"]
    assert data[0].get_ydata() == pytest.approx(res.series[path]["u"] / 13)
    limits = {round(float(ln.get_ydata()[0]), 2) for ln in ax.lines if ln.get_gid() == "limit"}
    assert limits == {CHEM["Li-Ion"]["load_min"], CHEM["Li-Ion"]["rest_min"]}
    assert ax._hover["y"](3.712) == "3.712 V/Zelle"
    assert ("Spannung", "V/Zelle") in [(r[0], r[1]) for r in fig._readout]
    assert any("13 Zellen" in t.get_text() for t in ax.texts)
    lo, _ = ax.get_ylim()
    assert lo < CHEM["Li-Ion"]["load_min"]                         # limit lines stay visible


def test_battery_view_without_cell_count_shows_total_voltage():
    res, p, path = _result(_flight_log(helpers.tmpdir()), cells=0)
    fig, ax = _battery(res, p, path)
    assert chart_title(ax) == "Akkuspannung (gesamt)" and ax.get_ylabel() == "V"
    data = [ln for ln in ax.lines if ln.get_gid() == "data"]
    assert data[0].get_ydata() == pytest.approx(res.series[path]["u"])
    assert not [ln for ln in ax.lines if ln.get_gid() == "limit"]
    assert any("Zellenzahl unbekannt" in t.get_text() for t in ax.texts)


def test_receiver_voltage_unchanged():
    res, p, path = _result(_flight_log(helpers.tmpdir()), cells=13)
    res.series[path]["rxu"] = np.full(len(res.series[path]["t"]), 7.4)
    fig = figure_flight(res, p, path, "rx_current")
    ax = next(a for a in fig.axes if chart_title(a) == "Empfängerspannung")
    assert ax.get_ylabel() == "V" and ax.lines[0].get_ydata()[0] == pytest.approx(7.4)
