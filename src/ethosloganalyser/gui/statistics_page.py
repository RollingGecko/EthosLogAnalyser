# -*- coding: utf-8 -*-
"""Statistics pages over all flights of the analysed model: summary, battery, load, drive, radio, table.

Filled from the folder analysis (analysis/fleet.py); the switch to the database and the filter follow in WP-19.
"""

from ..i18n import tr
from ..plots.overview import figure_akku, figure_antrieb, figure_belastung, figure_funk
from .common import TABLE_COLS, fill_text, fmt_cell, make_text

# chart pages: key -> function drawing the page from (result, params)
CHART_PAGES = {"akku": figure_akku, "belastung": figure_belastung, "antrieb": figure_antrieb, "funk": figure_funk}

# all statistics pages in their order
PAGE_KEYS = ("summary", "akku", "belastung", "antrieb", "funk", "table")


def page_title(key):
    """Title of a statistics page in the current language."""
    return {"summary": tr("Zusammenfassung"), "akku": tr("Akku"), "belastung": tr("Belastung & Flugprofil"),
            "antrieb": tr("Antrieb"), "funk": tr("Funk & Bordnetz"), "table": tr("Tabelle")}[key]


class StatisticsPages:
    """The statistics pages inside the frames given as {key: frame} (keys of PAGE_KEYS)."""

    def __init__(self, frames, charts, family):
        from tkinter import ttk
        self.frames = frames
        self.charts = charts
        self.figures = {}
        summary_frame = frames["summary"]
        self.summary = make_text(summary_frame, family)
        scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary.yview)
        self.summary.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.summary.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        self._build_table(frames["table"])

    def _build_table(self, parent):
        from tkinter import ttk
        self.columns = [c[0] for c in TABLE_COLS]
        self.table = ttk.Treeview(parent, columns=self.columns, show="headings")
        for key, head, width in TABLE_COLS:
            self.table.heading(key, text=tr(head))
            self.table.column(key, width=width, anchor="center", stretch=False)
        vertical = ttk.Scrollbar(parent, orient="vertical", command=self.table.yview)
        horizontal = ttk.Scrollbar(parent, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        vertical.pack(side="right", fill="y")
        horizontal.pack(side="bottom", fill="x")
        self.table.pack(fill="both", expand=True)

    def show_summary(self, lines):
        fill_text(self.summary, lines)

    def show(self, result, params, get_current):
        """Fills table and chart pages. get_current() returns the (result, params) to draw again later."""
        df = result.df
        self.table.delete(*self.table.get_children())
        for _, row in df.iterrows():
            self.table.insert("", "end", values=[fmt_cell(k, row[k]) for k in self.columns])
        self.figures = {}
        if df.empty:
            return
        for key, draw in CHART_PAGES.items():
            fig = draw(result, params)
            self.figures[key] = fig
            self.charts.show_fig(self.frames[key], fig, builder=lambda draw=draw: draw(*get_current()),
                                 title=page_title(key))

    def chart_canvas(self, key):
        """Canvas of the chart page key (for tests)."""
        return self.charts.page_canvases.get(str(self.frames[key]))
