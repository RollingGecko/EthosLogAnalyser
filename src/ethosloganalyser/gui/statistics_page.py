# -*- coding: utf-8 -*-
"""Area Statistics: the shared filter on top and the pages summary, battery, load, drive, radio and table.

The pages show the flights of the database that pass the filter (``StatisticsModel``), always for one aircraft.
Only the page that is shown is drawn; the others are drawn when they are chosen, so changing the filter stays
quick. While nothing can be shown (no flights, several aircraft, flights being prepared) every page shows why.
"""

from ..i18n import tr
from ..plots.common import _empty_fig
from ..plots.overview import figure_akku, figure_antrieb, figure_belastung, figure_funk
from ..report.text import summary_lines
from .common import TABLE_COLS, fill_text, fmt_cell, make_text
from .flight_filter import FilterBar
from .statistics_model import EXPERIMENTAL_NOTICE, READY
from .table_fit import TableFonts

# chart pages: key -> function drawing the page from (result, params)
CHART_PAGES = {"akku": figure_akku, "belastung": figure_belastung, "antrieb": figure_antrieb, "funk": figure_funk}

# all statistics pages in their order
PAGE_KEYS = ("summary", "akku", "belastung", "antrieb", "funk", "table")


def page_title(key):
    """Title of a statistics page in the current language."""
    return {"summary": tr("Zusammenfassung"), "akku": tr("Akku"), "belastung": tr("Belastung & Flugprofil"),
            "antrieb": tr("Antrieb"), "funk": tr("Funk & Bordnetz"), "table": tr("Tabelle")}[key]


def report_lines(view, battery_hint=None, filter_text=""):
    """The summary of a statistics view as report lines [(tag, text)]: the notice that the area is experimental
    first, then the filter (if one is set besides the aircraft), the battery hint (if the battery settings are
    missing) and the summary of the analysis."""
    lines = [("notice", tr(EXPERIMENTAL_NOTICE))]
    if filter_text:
        lines.append(("info", tr("Filter: {filter}", filter=filter_text)))
    if view.state != READY:
        return lines + [("info", view.message)]
    if battery_hint:
        lines.append(("bad", battery_hint))
    return lines + summary_lines(view.result, view.params)


class StatisticsPages:
    """The filter bar and the statistics pages inside the frames given as {key: frame} (keys of PAGE_KEYS).

    header: frame above the pages (filter bar, message); notebook: the notebook holding the page frames.
    """

    def __init__(self, header, notebook, frames, charts, family, filter_state):
        import tkinter as tk
        from tkinter import ttk
        self.notebook = notebook
        self.frames = frames
        self.charts = charts
        self.view = None
        self.lines = []
        self.stale = set()                        # pages that still show an older state
        self.filter_bar = FilterBar(header, filter_state)
        self.filter_bar.frame.pack(side="top", anchor="w")
        self.message = tk.StringVar()
        self.message_label = ttk.Label(header, textvariable=self.message, foreground="#b00020",
                                       font=(family, 10, "bold"))
        # shown only while there is a message (no empty line above the pages otherwise)
        summary_frame = frames["summary"]
        self.summary = make_text(summary_frame, family)
        self.summary.tag_configure("notice", font=(family, 11, "bold"), foreground="#7a4a00",
                                   background="#fff1cc", spacing1=4, spacing3=6)
        scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", command=self.summary.yview)
        self.summary.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.summary.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        self._build_table(frames["table"])
        notebook.bind("<<NotebookTabChanged>>", lambda _event: self.draw_visible())

    def _build_table(self, parent):
        from tkinter import ttk
        self.columns = [c[0] for c in TABLE_COLS]
        self.table = ttk.Treeview(parent, columns=self.columns, show="headings")
        for key, head in TABLE_COLS:
            self.table.heading(key, text=tr(head))
            self.table.column(key, anchor="center", stretch=False)
        self._fit_columns([])
        vertical = ttk.Scrollbar(parent, orient="vertical", command=self.table.yview)
        horizontal = ttk.Scrollbar(parent, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        vertical.pack(side="right", fill="y")
        horizontal.pack(side="bottom", fill="x")
        self.table.pack(fill="both", expand=True)

    # ---------------- showing ----------------
    def show(self, view, lines):
        """Shows a StatisticsView: the message (if any) at once, the pages when they are seen."""
        self.view, self.lines = view, lines
        self.message.set(view.message)
        if view.message:
            self.message_label.pack(side="top", anchor="w", pady=(4, 0))
        else:
            self.message_label.pack_forget()
        self.stale = set(PAGE_KEYS)
        self.draw_visible()

    def visible_key(self):
        """Key of the statistics page that is selected."""
        return PAGE_KEYS[self.notebook.index("current")]

    def draw_visible(self):
        """Draws the selected page if it still shows an older state."""
        if self.view is not None and self.visible_key() in self.stale:
            self.draw(self.visible_key())

    def draw(self, key):
        """Draws one page for the current view."""
        self.stale.discard(key)
        if key == "summary":
            fill_text(self.summary, self.lines)
        elif key == "table":
            self._fill_table()
        else:
            self._draw_chart(key)

    def _fit_columns(self, rows):
        """Column widths from the font: the heading and the longest text of the column (digits as wide as the
        widest digit), so neither is cut off at any screen scaling."""
        fonts = TableFonts(self.table)
        for index, (key, head) in enumerate(TABLE_COLS):
            longest = max((row[index] for row in rows), key=len, default="")
            self.table.column(key, width=fonts.width(tr(head), [fonts.shaped(longest)]), stretch=False)

    def _fill_table(self):
        self.table.delete(*self.table.get_children())
        if self.view.state != READY:
            self._fit_columns([])
            return
        rows = [[fmt_cell(k, row[k]) for k in self.columns] for _, row in self.view.result.df.iterrows()]
        self._fit_columns(rows)
        for row in rows:
            self.table.insert("", "end", values=row)

    def figure(self, key):
        """The figure of a chart page for the current view (a message when there is nothing to show)."""
        if self.view is None or self.view.state != READY:
            return _empty_fig(self.view.message if self.view is not None else "")
        return CHART_PAGES[key](self.view.result, self.view.params)

    def _draw_chart(self, key):
        frame = self.frames[key]
        figure = self.figure(key)
        if not self.charts.replace_fig(frame, figure):                 # the first time: create the canvas
            self.charts.show_fig(frame, figure, builder=lambda: self.figure(key), title=page_title(key))

    def chart_canvas(self, key):
        """Canvas of the chart page key (for tests)."""
        return self.charts.page_canvases.get(str(self.frames[key]))
