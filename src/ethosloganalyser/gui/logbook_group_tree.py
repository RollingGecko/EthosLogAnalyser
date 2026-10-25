# -*- coding: utf-8 -*-
"""The "Group by" tree of the logbook: flights and flight time per year, month and aircraft.

The user chooses the grouping (time: year -> month -> aircraft, or aircraft: aircraft -> year -> month).
A click on a row selects those flights for the flight list; the sum row at the end selects all flights again.
"""

from ..analysis.logbook_groups import AIRCRAFT, GROUP_BY_AIRCRAFT, GROUP_BY_TIME, MONTH, YEAR
from ..config import model_label
from ..i18n import tr
from ..plots.logbook import month_label
from ..utils import fmt_duration

TOTAL_ITEM = "total"


def node_text(node):
    """Text of a tree row: the year, "MM/YYYY" for a month, the aircraft name."""
    if node.level == YEAR:
        return str(node.value)
    if node.level == MONTH:
        return month_label(node.selector[YEAR], node.value)
    return model_label(node.value)


class GroupTree:
    """Radio buttons for the grouping and the tree below them."""

    def __init__(self, parent, group_by, on_group_by_changed, on_selected):
        import tkinter as tk
        from tkinter import ttk

        self.on_selected = on_selected              # on_selected(selector or None)
        self.selectors = {}                         # tree item -> selector of its flights
        self._silent = False                        # True while the tree is filled (no selection events)
        box = ttk.LabelFrame(parent, text=tr("Gruppieren nach"), padding=4)
        self.frame = box
        self.group_by = tk.StringVar(value=group_by)
        buttons = ttk.Frame(box)
        buttons.pack(fill="x")
        for value, text in ((GROUP_BY_TIME, tr("Zeit (Jahr, Monat, Flugzeug)")),
                            (GROUP_BY_AIRCRAFT, tr("Flugzeug (Jahr, Monat)"))):
            ttk.Radiobutton(buttons, text=text, value=value, variable=self.group_by,
                            command=lambda: on_group_by_changed(self.group_by.get())).pack(anchor="w")

        columns = [("flights", tr("Flüge"), 50), ("duration", tr("Log-Dauer"), 80)]
        self.tree = ttk.Treeview(box, columns=[key for key, _text, _width in columns], height=10)
        self.tree.heading("#0", text=tr("Gruppe"))
        self.tree.column("#0", width=150, stretch=True)
        for key, text, width in columns:
            self.tree.heading(key, text=text)
            self.tree.column(key, width=width, anchor="center", stretch=False)
        from tkinter import font as tkfont
        self.total_font = tkfont.nametofont("TkDefaultFont").copy()      # the sum row: the normal font, bold
        self.total_font.configure(weight="bold")
        self.tree.tag_configure(TOTAL_ITEM, font=self.total_font)
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, pady=(4, 0))
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def show(self, nodes, n_flights, duration_s, selected):
        """Fills the tree with the nodes and the sum row; the row with the selector `selected` stays selected."""
        self._silent = True
        try:
            self.tree.delete(*self.tree.get_children())
            self.selectors = {}
            self._insert(nodes, "", selected)
            self.tree.insert("", "end", iid=TOTAL_ITEM, text=tr("Summe"), values=(n_flights, fmt_duration(duration_s)),
                             tags=(TOTAL_ITEM,))
        finally:
            self._silent = False

    def _insert(self, nodes, parent, selected, depth=0):
        for node in nodes:
            item = self.tree.insert(parent, "end", text=node_text(node), open=depth == 0,
                                    values=(node.n_flights, fmt_duration(node.duration_s)))
            self.selectors[item] = node.selector
            if node.selector == selected:
                self.tree.selection_set(item)
                self._open_parents(item)
            self._insert(node.children, item, selected, depth + 1)

    def _open_parents(self, item):
        parent = self.tree.parent(item)
        while parent:
            self.tree.item(parent, open=True)
            parent = self.tree.parent(parent)

    def _on_tree_select(self, _event=None):
        if self._silent:
            return
        selection = self.tree.selection()
        self.on_selected(self.selectors.get(selection[0]) if selection else None)

    def select_item(self, item):
        """Selects a row (what a click does)."""
        self.tree.selection_set(item)
