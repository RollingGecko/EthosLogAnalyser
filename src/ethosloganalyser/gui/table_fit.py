# -*- coding: utf-8 -*-
"""Sizes of table columns and rows that follow the font, so no text is cut off at any screen scaling.

The process is DPI aware on Windows, so the fonts grow with the display scaling (100 %, 125 %, 150 % ...) while
fixed pixel sizes do not. Every size here is worked out from the font instead:

* a column is as wide as its heading (plus the ▲/▼ mark of a sortable table) and the widest value it can show,
  plus a margin for the cell padding;
* a row is as high as one line of the font plus a margin.

The calculations are plain functions that take a ``measure(text) -> pixels`` function, so they are tested without
a window. ``TableFonts`` binds them to the fonts of a Tk widget.
"""

SORT_MARK = " ▼"            # the widest mark ``common.sortable_tree`` adds to a heading
CELL_MARGIN = 20            # pixels added to the text width: cell padding on both sides plus some air
ROW_MARGIN = 6              # pixels added to the line height of the font
DIGITS = "0123456789"
REFERENCE_SCALING = 96 / 72  # Tk scaling at a Windows display scaling of 100 %: window sizes are meant for it


def widest_digits(measure, count):
    """The text of ``count`` digits that is widest in the font (digits are equally wide in most fonts, but not in
    all of them)."""
    digit = max(DIGITS, key=measure)
    return digit * count


def shaped(text, digit):
    """The text with every digit replaced by ``digit`` (the widest digit of the font): the widest text of a format
    such as a time or a date."""
    return "".join(digit if char.isdigit() else char for char in text)


def column_width(measure_heading, measure_cell, heading, samples=(), sortable=False, margin=CELL_MARGIN):
    """Pixels for a column: wide enough for the heading (with the sort mark if the table is sortable) and for
    every text of ``samples`` (the widest values the column can show)."""
    widths = [measure_heading(heading + (SORT_MARK if sortable else ""))]
    widths += [measure_cell(text) for text in samples]
    return max(widths) + margin


def row_height(line_height, margin=ROW_MARGIN):
    """Pixels for a table row: one line of the font plus a margin."""
    return line_height + margin


def scaled_window_size(scaling, base, screen, margin=(40, 80)):
    """(width, height) of a window in pixels: the size ``base`` meant for 100 % display scaling grows with the
    scaling (the fonts and so the tables do), but never beyond the screen minus ``margin`` (taskbar, title bar)."""
    factor = max(1.0, scaling / REFERENCE_SCALING)
    return (min(round(base[0] * factor), screen[0] - margin[0]), min(round(base[1] * factor), screen[1] - margin[1]))


def window_size(window, base):
    """``scaled_window_size`` for the Tk window with the current Tk scaling and its screen."""
    return scaled_window_size(float(window.tk.call("tk", "scaling")), base,
                              (window.winfo_screenwidth(), window.winfo_screenheight()))


def characters_for(measure, texts, minimum, maximum=None, margin_characters=2):
    """Width in characters (the unit of an entry or combobox) that shows the widest of ``texts``; at least
    ``minimum``, at most ``maximum``. A character is the width of the digit "0", as in Tk."""
    zero = max(measure("0"), 1)
    widest = max((measure(text) for text in texts), default=0)
    wanted = -(-widest // zero) + margin_characters            # rounded up
    wanted = max(minimum, wanted)
    return wanted if maximum is None else min(wanted, maximum)


class TableFonts:
    """The fonts a Treeview of this application uses (cell font, heading font) and what follows from them."""

    def __init__(self, widget):
        from tkinter import font as tkfont, ttk
        self.cell_font = tkfont.nametofont("TkDefaultFont")
        heading = ttk.Style(widget).lookup("Treeview.Heading", "font") or "TkHeadingFont"
        self.heading_font = tkfont.Font(root=widget, font=heading)

    @property
    def line_height(self):
        return self.cell_font.metrics("linespace")

    def width(self, heading, samples=(), sortable=False):
        return column_width(self.heading_font.measure, self.cell_font.measure, heading, samples, sortable)

    def digits(self, count):
        return widest_digits(self.cell_font.measure, count)

    def shaped(self, text):
        return shaped(text, self.digits(1))


def fit_tree_columns(tree, specs, sortable=False):
    """Sets the width of the columns of a Treeview to the font. specs: {column key: (heading, samples)}; columns
    without an entry keep their width."""
    fonts = TableFonts(tree)
    for key, (heading, samples) in specs.items():
        tree.column(key, width=fonts.width(heading, samples, sortable), stretch=False)
