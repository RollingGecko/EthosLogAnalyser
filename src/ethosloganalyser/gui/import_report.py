# -*- coding: utf-8 -*-
"""The import report: one line about an import and a window with every file and what happened to it."""

from ..db import importer
from ..i18n import N_, tr

OUTCOME_LABELS = {
    importer.NEW: N_("neu"),
    importer.DUPLICATE: N_("doppelt"),
    importer.SUSPICIOUS: N_("mögliches Duplikat"),
    importer.UNREADABLE: N_("nicht lesbar"),
}

# order of the import report: what needs attention first
OUTCOME_ORDER = (importer.UNREADABLE, importer.SUSPICIOUS, importer.DUPLICATE, importer.NEW)


def report_summary(report):
    """One line about an import: new (thereof flights), duplicates, possible duplicates, unreadable."""
    text = tr("{new} neu (davon {flights} Flüge), {duplicate} doppelt, {suspicious} mögliche Duplikate, "
              "{unreadable} nicht lesbar",
              new=report.count(importer.NEW) + report.count(importer.SUSPICIOUS), flights=report.flight_count,
              duplicate=report.count(importer.DUPLICATE), suspicious=report.count(importer.SUSPICIOUS),
              unreadable=report.count(importer.UNREADABLE))
    if report.cancelled:
        text += " – " + tr("abgebrochen")
    return text


def entry_detail(entry):
    """What the import report says about one file."""
    if entry.outcome == importer.DUPLICATE:
        return tr("gleicher Inhalt wie {file} (übersprungen)", file=entry.other_file)
    if entry.outcome == importer.SUSPICIOUS:
        return tr("gleiches Modell und gleiche Startzeit wie {file} (importiert, markiert)", file=entry.other_file)
    if entry.outcome == importer.UNREADABLE:
        return str(entry.reason)
    return tr("Flug") if entry.is_flight else tr("kein Flug")


def report_rows(report):
    """(file name, outcome label, detail) of every file, problems first."""
    rows = []
    for outcome in OUTCOME_ORDER:
        for entry in report.with_outcome(outcome):
            rows.append((entry.file_name, tr(OUTCOME_LABELS[outcome]), entry_detail(entry)))
    return rows


def show_import_report(root, report):
    """Window with the import report: summary and every file with its outcome."""
    import tkinter as tk
    from tkinter import font as tkfont, ttk

    window = tk.Toplevel(root)
    window.title(tr("Import-Bericht"))
    window.geometry("900x480")
    window.transient(root)
    frame = ttk.Frame(window, padding=10)
    frame.pack(fill="both", expand=True)
    family = tkfont.nametofont("TkDefaultFont").actual("family")
    ttk.Label(frame, text=report_summary(report), font=(family, 10, "bold")).pack(anchor="w", pady=(0, 8))
    table = ttk.Frame(frame)
    table.pack(fill="both", expand=True)
    tree = ttk.Treeview(table, columns=("file", "outcome", "detail"), show="headings")
    for column, title, width in (("file", tr("Datei"), 300), ("outcome", tr("Ergebnis"), 140),
                                 ("detail", tr("Hinweis"), 420)):
        tree.heading(column, text=title)
        tree.column(column, width=width, stretch=column == "detail")
    for row in report_rows(report):
        tree.insert("", "end", values=row)
    scrollbar = ttk.Scrollbar(table, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(side="left", fill="both", expand=True)
    ttk.Button(frame, text=tr("Schließen"), command=window.destroy).pack(anchor="e", pady=(8, 0))
    return dict(window=window, tree=tree)
