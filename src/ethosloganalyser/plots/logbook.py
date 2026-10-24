# -*- coding: utf-8 -*-
"""Chart of the logbook tab: flights and log duration per month (see analysis/logbook.py)."""

import numpy as np

from ..i18n import tr
from ..plots.common import _empty_fig, _new_fig, _note, hover_info, time_axis

MAX_TICKS = 12          # at most this many month labels on the x axis (every n-th month otherwise)


def month_label(year, month):
    return f"{month:02d}/{year}"


def figure_logbook(lb):
    """Bars per month (only months with flights): number of flights and summed log duration."""
    pm = lb.per_month
    if pm is None or pm.empty:
        return _empty_fig(tr("Keine Daten"))
    labels = [month_label(int(y), int(m)) for y, m in pm.index]
    x = np.arange(len(labels))
    fig, ax = _new_fig(1, 2, size=(11, 3.4))
    step = max(1, int(np.ceil(len(labels) / MAX_TICKS)))
    month_of = lambda v: labels[int(np.clip(round(v), 0, len(labels) - 1))]
    for a, col, color, title, note in [
            (ax[0][0], "Fluege", "tab:blue", tr("Flüge je Monat"), tr("Nur Monate mit Flügen.")),
            (ax[0][1], "dauer_s", "tab:green", tr("Log-Dauer je Monat [h:min:s]"),
             tr("Summe der Log-Dauer (Motor scharf bis gesperrt).")),
    ]:
        a.bar(x, pm[col].to_numpy(dtype=float), color=color, alpha=0.7, label=title.split(" [")[0])
        a.set_xticks(x[::step])
        a.set_xticklabels(labels[::step], rotation=45, ha="right", fontsize=7)
        a.set_title(title, loc="left")
        a.set_xlabel(tr("Monat"), fontsize=8)
        a.grid(axis="x", visible=False)
        hover_info(a, x=month_of)
        _note(a, note)
    ax[0][0].yaxis.get_major_locator().set_params(integer=True)
    hover_info(ax[0][0], y=lambda v: f"{v:.0f}")
    time_axis(ax[0][1], "y")
    return fig
