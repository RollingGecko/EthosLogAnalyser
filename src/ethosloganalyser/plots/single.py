# -*- coding: utf-8 -*-
"""One chart of a page on its own: the basis of the single-chart full-screen window.

A page (figure) holds several charts (axes). To enlarge one of them, the page is drawn again with its normal
plot function (so every artist - title, note, legend, helper lines, red circles, trend lines, twin axes - is
exactly the same as on the page) and every other chart is removed. The remaining chart (with its twin axes)
then fills the whole figure. This needs no special code in the plot functions: any chart that is shown with a
builder gets it.
"""

import numpy as np


def _cell(ax):
    """Grid cell of an axes as (gridspec, rows, columns), or None for axes placed by hand."""
    spec = ax.get_subplotspec() if hasattr(ax, "get_subplotspec") else None
    if spec is None:
        return None
    return spec.get_gridspec(), spec.rowspan, spec.colspan


def chart_group(fig, ax):
    """Axes that form one chart with ax: ax itself and its twin axes (same grid cell or same position)."""
    cell = _cell(ax)
    pos = ax.get_position().bounds
    group = []
    for a in fig.axes:
        if a is ax:
            group.append(a)
            continue
        c = _cell(a)
        same = (c is not None and cell is not None and c[0] is cell[0] and c[1] == cell[1] and c[2] == cell[2]) or \
            np.allclose(a.get_position().bounds, pos)
        if same:
            group.append(a)
    # the main axes first (the one created first: it carries the x axis)
    return sorted(group, key=fig.axes.index)


def chart_index(fig, ax):
    """Position of the chart of ax in fig.axes (index of its main axes) - stable when the page is redrawn."""
    return fig.axes.index(chart_group(fig, ax)[0])


def chart_title(ax):
    """Title of a chart (the left title the plot functions use, else the centre title)."""
    return ax.get_title(loc="left") or ax.get_title() or ""


def _column_xlabel(fig, ax):
    """x label of the chart below ax that shares its x axis (pages with a shared time axis label only the
    bottom chart)."""
    cell = _cell(ax)
    if cell is None:
        return None
    best = None
    for a in fig.axes:
        c = _cell(a)
        if c is None or c[0] is not cell[0] or c[2] != cell[2] or not a.get_xlabel():
            continue
        if not ax.get_shared_x_axes().joined(ax, a):
            continue
        if best is None or c[1].stop > _cell(best)[1].stop:
            best = a
    return best.xaxis.label if best is not None else None


def single_chart(fig, index):
    """Reduces fig to the chart whose main axes is fig.axes[index]; returns its axes (main axes first).

    The chart keeps all its artists and fills the figure. The page title (suptitle) stays as context.
    """
    axes = list(fig.axes)
    if not 0 <= index < len(axes):
        raise IndexError(f"chart {index} not on this page ({len(axes)} axes)")
    group = chart_group(fig, axes[index])
    main = group[0]
    if not main.get_xlabel():
        hidden = getattr(main, "_hidden_xlabel", None)     # removed by plots.common._bottom_labels_only
        lbl = _column_xlabel(fig, main)
        if hidden is not None:
            main.set_xlabel(hidden[0], fontsize=hidden[1])
        elif lbl is not None:
            main.set_xlabel(lbl.get_text(), fontsize=lbl.get_fontsize())
    for a in axes:
        if a not in group:
            a.remove()
    if all(_cell(a) is not None for a in group):
        gs = fig.add_gridspec(1, 1)
        for a in group:
            a.set_subplotspec(gs[0])
    else:                                              # axes placed by hand
        for a in group:
            a.set_position([0.08, 0.1, 0.84, 0.78])
    # pages with shared x axes hide the tick labels of the upper charts
    main.xaxis.set_tick_params(which="both", labelbottom=True)
    return group
