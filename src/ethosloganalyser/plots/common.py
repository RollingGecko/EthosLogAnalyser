# -*- coding: utf-8 -*-
"""Shared chart styling and helper functions."""

import numpy as np

from ..i18n import tr
from ..utils import _trend


def _style_mpl():
    import matplotlib as mpl
    mpl.rcParams.update({
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "legend.fontsize": 8,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "lines.linewidth": 1.4,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3,
        "axes.titleweight": "bold", "axes.titlelocation": "left",
    })


def _new_fig(rows, cols, size=(11, 8)):
    from matplotlib.figure import Figure
    _style_mpl()
    fig = Figure(figsize=size, dpi=100, layout="constrained")
    fig.get_layout_engine().set(h_pad=0.08, hspace=0.06)
    axes = fig.subplots(rows, cols, squeeze=False)
    return fig, axes


def _empty_fig(text):
    from matplotlib.figure import Figure
    fig = Figure(figsize=(8, 5), dpi=100)
    fig.text(0.5, 0.5, text, ha="center", va="center", fontsize=12)
    return fig


NOTE_WIDTH = 95         # characters per line of a chart note (longer notes are wrapped)


def _note(ax, text):
    """Short explanation below the chart title: what is shown and what is good."""
    if text:
        import textwrap
        lines = textwrap.wrap(text.strip(), NOTE_WIDTH) or [""]
        ax.text(0, 1.012, "\n".join(lines), transform=ax.transAxes, fontsize=7.5, color="#555555", va="bottom",
                ha="left")
        ax.set_title(ax.get_title(loc="left"), loc="left", pad=14 + 10 * (len(lines) - 1))


def _bottom_labels_only(ax):
    """x label only in the bottom row - otherwise it overlaps the title below."""
    for row in ax[:-1]:
        for a in row:
            a.set_xlabel("")


def _legend(*axes, loc="best", ncol=1):
    """One shared legend for charts with a secondary y axis."""
    h, l = [], []
    for a in axes:
        hh, ll = a.get_legend_handles_labels()
        h += hh
        l += ll
    if h:
        axes[0].legend(h, l, fontsize=7, loc=loc, ncol=ncol, framealpha=0.85)


def _axis_color(a, color, label, side="left"):
    a.set_ylabel(label, color=color, fontsize=8)
    a.tick_params(axis="y", colors=color, labelsize=8)


def _plot_trend(ax, df, col, color, title, flags=None, flag_label=None, hlines=(), label=None, trend=True, marker="o",
                note=None, model=None):
    """Values of one column per flight with optional trend line.

    title, label, note and hline texts must already be translated; flag_label is a flag code
    (see analysis.evaluate.FLAG_LABELS) whose flights are circled in red. model is an ageing model
    (analysis.ageing.ageing_model): its line is drawn instead of a plain least-squares trend - solid if the
    trend is significant, dashed if not.
    """
    x = df["Flug"].to_numpy(dtype=float)
    y = df[col].to_numpy(dtype=float)
    good = np.isfinite(y)
    if not good.any():
        ax.text(0.5, 0.5, tr("keine Daten"), transform=ax.transAxes, ha="center", va="center", color="grey")
    else:
        ax.plot(x[good], y[good], marker, ms=5, color=color, label=label, ls="none")
        if trend and model is not None and model.get("status") == "ok":
            xs = np.array([model["first"], model["last"]])
            ys = model["current"] + model["slope"] * (xs - model["last"])
            ax.plot(xs, ys, "-" if model["trend"] != "none" else "--", color=color, alpha=0.6, lw=1.8)
        elif trend:
            trd = _trend(x, y)
            if trd:
                ax.plot(x, trd[0] * x + trd[1], "-", color=color, alpha=0.5, lw=1.5)
        if flags and flag_label in flags:
            sel = np.isin(x, list(flags[flag_label])) & good
            ax.plot(x[sel], y[sel], "o", ms=12, mfc="none", mec="red", mew=1.5)
    for val, txt, c in hlines:
        ax.axhline(val, color=c, ls="--", lw=1)
        ax.text(0.01, val, txt, transform=ax.get_yaxis_transform(), fontsize=8, color=c, va="bottom")
    if not ax.get_title(loc="left"):        # several series in one chart: keep the title and its note spacing
        ax.set_title(title, loc="left")
    ax.set_xlabel(tr("Flug Nr."), fontsize=8)
    _note(ax, note)


def flag_note():
    return tr(" Rot umkreist: auffälliger Flug.")


def trend_note():
    return tr(" Linie gestrichelt: kein gesicherter Trend.")
