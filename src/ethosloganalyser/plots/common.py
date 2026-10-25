# -*- coding: utf-8 -*-
"""Shared chart styling and helper functions."""

import numpy as np

from ..i18n import fmt_datetime, tr
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
        # fixed offset in points (not a fraction of the axes height): the note keeps its place below the title
        # also when the chart is enlarged on its own (plots/single.py)
        ax.annotate("\n".join(lines), xy=(0, 1), xycoords="axes fraction", xytext=(0, 2.5), textcoords="offset points",
                    fontsize=7.5, color="#555555", va="bottom", ha="left")
        ax.set_title(ax.get_title(loc="left"), loc="left", pad=14 + 10 * (len(lines) - 1))


def _bottom_labels_only(ax):
    """x label only in the bottom row - otherwise it overlaps the title below.

    The label is kept in ax._hidden_xlabel, so a chart enlarged on its own shows it again (plots/single.py).
    """
    for row in ax[:-1]:
        for a in row:
            lbl = a.xaxis.label
            if lbl.get_text():
                a._hidden_xlabel = (lbl.get_text(), lbl.get_fontsize())
            a.set_xlabel("")


def _plot_trend(ax, df, col, color, title, flags=None, flag_label=None, hlines=(), label=None, trend=True, marker="o",
                note=None, model=None):
    """Values of one column per flight with optional trend line.

    title, label, note and hline texts must already be translated; flag_label is a flag code
    (see analysis.evaluate.FLAG_LABELS) whose flights are circled in red. model is an ageing model
    (analysis.ageing.ageing_model): its shown line is drawn instead of a plain least-squares trend - solid if
    the trend is significant and plausible, otherwise the dashed mean level.
    """
    x = df["Flug"].to_numpy(dtype=float)
    y = df[col].to_numpy(dtype=float)
    good = np.isfinite(y)
    flight_hover(ax, df)
    if not good.any():
        ax.text(0.5, 0.5, tr("keine Daten"), transform=ax.transAxes, ha="center", va="center", color="grey")
    else:
        ax.plot(x[good], y[good], marker, ms=5, color=color, label=label, ls="none")
        if trend and model is not None and model.get("status") == "ok":
            xs = np.array([model["first"], model["last"]])
            ys = np.array([model["start"], model["current"]])
            ax.plot(xs, ys, "-" if model.get("reliable") else "--", color=color, alpha=0.6, lw=1.8)
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
    return tr(" Linie gestrichelt: kein gesicherter Trend (Mittelwert).")


# ---------------------------------------------------------------- time axes and hover metadata

TIME_STEPS = (1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600, 7200, 18000, 36000)


def time_ticks(lo, hi, max_ticks=11):
    """Tick positions [s] on round time steps (1 s ... 10 h) with at most max_ticks ticks in [lo, hi]."""
    if not (np.isfinite(lo) and np.isfinite(hi)) or hi <= lo:
        return np.array([])
    span = hi - lo
    step = next((st for st in TIME_STEPS if span / st <= max_ticks - 1), TIME_STEPS[-1] * np.ceil(span / TIME_STEPS[-1] / 8))
    first = np.ceil(lo / step) * step
    return np.arange(first, hi + step * 1e-9, step)


def time_axis(ax, which="x"):
    """Formats an axis that holds seconds as min:s / h:min:s with ticks on round times (see utils.fmt_duration)."""
    from matplotlib.ticker import FuncFormatter, Locator
    from ..utils import fmt_duration

    class TimeLocator(Locator):
        def __call__(self):
            lo, hi = self.axis.get_view_interval()
            return self.tick_values(lo, hi)

        def tick_values(self, vmin, vmax):
            return time_ticks(min(vmin, vmax), max(vmin, vmax))

    axis = ax.xaxis if which == "x" else ax.yaxis
    axis.set_major_locator(TimeLocator())
    axis.set_major_formatter(FuncFormatter(lambda v, _pos: fmt_duration(v)))
    if which == "x":
        hover_info(ax, x=lambda v: "t = " + fmt_duration(v))
    else:
        hover_info(ax, y=lambda v: fmt_duration(v, unit=True))


def hover_info(ax, x=None, y=None, name=None):
    """Tells the mouse-over tooltip (plots/hover.py) how to show the values of this chart.

    x, y: functions value -> text (e.g. flight number -> "Flight 12 – 19/04/2026", seconds -> "8:58");
    name: series name if the artists have no label. Unset parts are shown with the axis unit.
    """
    info = getattr(ax, "_hover", {})
    info.update({k: v for k, v in (("x", x), ("y", y), ("name", name)) if v is not None})
    ax._hover = info


def flight_hover(ax, df):
    """Tooltip x value of charts over the flight number: "Flight 12 – 19/04/2026 12:05"."""
    if df is None or "Flug" not in df or "datum" not in df:
        return
    dates = dict(zip(df["Flug"].astype(int), df["datum"]))

    def fmt(v):
        no = int(round(v))
        if no in dates:
            return tr("Flug {no} – {date}", no=no, date=fmt_datetime(dates[no]))
        return tr("Flug {no}", no=no)
    hover_info(ax, x=fmt)
