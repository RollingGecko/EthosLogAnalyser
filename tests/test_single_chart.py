# -*- coding: utf-8 -*-
"""Enlarging one chart of a page on its own (plots/single.py)."""

import numpy as np
import pandas as pd
import pytest

import helpers
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure

from ethosloganalyser.config import Params
from ethosloganalyser.i18n import get_language, set_language
from ethosloganalyser.plots.common import _bottom_labels_only, _new_fig, _plot_trend
from ethosloganalyser.plots.flight import FLIGHT_VIEWS, figure_flight
from ethosloganalyser.plots.overview import figure_akku, figure_antrieb, figure_belastung, figure_funk
from ethosloganalyser.plots.single import chart_group, chart_index, chart_title, single_chart

PAGES = {"akku": figure_akku, "belastung": figure_belastung, "antrieb": figure_antrieb, "funk": figure_funk}


@pytest.fixture(autouse=True)
def german():
    old = get_language()
    set_language("de")
    yield
    set_language(old)


def artists(ax):
    """What a chart is made of: number of each kind of artist plus the texts that matter."""
    leg = ax.get_legend()
    return dict(lines=len(ax.lines), collections=len(ax.collections), patches=len(ax.patches),
                texts=sorted(t.get_text() for t in ax.texts), containers=len(ax.containers),
                legend=None if leg is None else [t.get_text() for t in leg.get_texts()],
                title=ax.get_title(loc="left"), ylabel=ax.get_ylabel(),
                xlim=tuple(np.round(ax.get_xlim(), 6)), ylim=tuple(np.round(ax.get_ylim(), 6)))


def check_page(builder):
    """Every chart of the page enlarged on its own keeps all its artists and fills the figure."""
    page = builder()
    FigureCanvasAgg(page).draw()
    n = len(page.axes)
    assert n >= 1
    for i, ax in enumerate(page.axes):
        group = chart_group(page, ax)
        if group[0] is not ax:
            continue                                  # twin axes: enlarged together with their main axes
        before = [artists(a) for a in group]
        fig = builder()                                # the page is drawn again, as in the GUI
        kept = single_chart(fig, i)
        assert len(fig.axes) == len(kept) == len(group), (i, chart_title(ax))
        after = [artists(a) for a in kept]
        for b, a in zip(before, after):
            assert a == b, (i, chart_title(ax))
        FigureCanvasAgg(fig).draw()
        for a in kept:                                 # the chart fills the figure
            assert a.get_position().width > 0.7 and a.get_position().height > 0.6, chart_title(ax)
        assert kept[0].get_xlabel(), chart_title(ax)   # x label also for charts of the upper rows
        assert any(t.get_visible() and t.get_text() for t in kept[0].get_xticklabels()), chart_title(ax)


@pytest.mark.parametrize("page", sorted(PAGES))
def test_every_overview_chart_alone(page):
    res = helpers.example_result(9000.0)
    p = Params(nominal_mah=9000.0)
    check_page(lambda: PAGES[page](res, p))


@pytest.mark.parametrize("view", FLIGHT_VIEWS)
def test_every_single_flight_chart_alone(view):
    res = helpers.example_result(9000.0)
    p = Params(nominal_mah=9000.0)
    for path in res.df["pfad"]:
        check_page(lambda: figure_flight(res, p, path, view))


def test_peak_c_rate_chart_alone():
    """The example from the user: tab Load, "Peak C rate per flight [C]" with its note."""
    res = helpers.example_result(9000.0)
    p = Params(nominal_mah=9000.0)
    page = figure_belastung(res, p)
    ax = next(a for a in page.axes if chart_title(a) == "Spitzen-C-Rate je Flug [C]")
    i = chart_index(page, ax)
    fig = figure_belastung(res, p)
    (kept,) = single_chart(fig, i)
    assert chart_title(kept) == "Spitzen-C-Rate je Flug [C]"
    assert any(t.get_text().startswith("Höchster Strom geteilt durch Kapazität") for t in kept.texts)
    assert kept.get_xlabel() == "Flug Nr."
    assert kept._hover["x"](1).startswith("Flug 1")          # tooltip format stays with the chart


def _page_with_twin():
    fig, ax = _new_fig(2, 2)
    x = np.arange(1, 11, dtype=float)
    for a in ax.flat:
        a.plot(x, x ** 2, "o", label="main")
        a.set_title("Chart", loc="left")
        a.set_xlabel("Flight")
    main = ax[0][1]
    main.set_title("Voltage and current", loc="left")
    twin = main.twinx()
    twin.plot(x, 10 - x, "-", color="tab:red", label="current")
    twin.set_ylabel("Current [A]")
    main.axhline(50, color="grey", ls="--")
    _bottom_labels_only(ax)
    return fig


def test_twin_axes_are_enlarged_with_their_chart():
    page = _page_with_twin()
    twin = page.axes[-1]
    assert chart_index(page, twin) == 1                # clicking on the twin axes finds the chart
    group = chart_group(page, twin)
    assert [page.axes.index(a) for a in group] == [1, 4]
    fig = _page_with_twin()
    kept = single_chart(fig, 1)
    assert len(fig.axes) == 2 and kept[0].get_title(loc="left") == "Voltage and current"
    assert kept[1].get_ylabel() == "Current [A]" and len(kept[1].lines) == 1
    assert kept[0].get_xlabel() == "Flight"            # label of the bottom row taken over
    FigureCanvasAgg(fig).draw()
    assert np.allclose(kept[0].get_position().bounds, kept[1].get_position().bounds)
    assert kept[0].get_position().width > 0.7


def test_scatter_with_markers_alone():
    """Scatter chart with red circles (flagged flights), trend line, helper line and its label."""
    df = pd.DataFrame({"Flug": np.arange(1, 13), "datum": pd.date_range("2026-04-01", periods=12, freq="D"),
                       "v": np.linspace(10, 12, 12) + np.sin(np.arange(12))})

    def page():
        fig, ax = _new_fig(2, 2)
        for a in ax.flat:
            _plot_trend(a, df, "v", "tab:blue", "Other", trend=False)
        _plot_trend(ax[1][1], df, "v", "tab:green", "Capacity [mAh]", {"capacity": {3, 7}}, "capacity",
                    hlines=[(11, "80 %", "tab:red")], note="Falling trend = ageing.")
        ax[1][1].scatter(df["Flug"], df["v"] + 1, s=12, color="tab:purple", label="scatter")
        return fig

    p = page()
    before = artists(p.axes[3])
    assert before["lines"] == 5                        # 2 value series, trend, red circles, helper line
    fig = page()
    (kept,) = single_chart(fig, 3)
    assert artists(kept) == before
    assert any(isinstance(c, PathCollection) for c in kept.collections)
    circles = [ln for ln in kept.lines if ln.get_markeredgecolor() == "red"]
    assert len(circles) == 1 and list(circles[0].get_xdata()) == [3, 7]
    assert {"80 %", "Falling trend = ageing."} <= {t.get_text() for t in kept.texts}


def test_single_chart_rejects_unknown_index():
    fig = Figure()
    fig.subplots(1, 2)
    with pytest.raises(IndexError):
        single_chart(fig, 5)
