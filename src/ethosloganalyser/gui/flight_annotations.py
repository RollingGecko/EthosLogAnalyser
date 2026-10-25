# -*- coding: utf-8 -*-
"""Section "Note and anomalies" of the single flight, next to the details below the charts.

The note is a free text per flight; it is saved with the button, when the text box loses the focus and when
another flight is chosen. The anomalies of the flight are listed most severe first; the selected one can be
acknowledged (or opened again), and the user can add and delete entries of their own. Automatic anomalies are
found by the rules (analysis/anomalies.py) and cannot be deleted, only acknowledged.
"""

from ..db import annotations
from ..i18n import N_, tr

SEVERITY_LABELS = {annotations.INFO: N_("Info"), annotations.WARNING: N_("Warnung"),
                   annotations.CRITICAL: N_("Kritisch")}
ORIGIN_LABELS = {annotations.AUTO: N_("automatisch"), annotations.MANUAL: N_("eigener Eintrag")}

# text column width in characters; the other columns are as wide as their longest text
TEXT_COLUMN_CHARACTERS = 60


def status_label(anomaly):
    return tr("quittiert") if anomaly.acknowledged else tr("offen")


def anomaly_row(anomaly):
    """Shown texts of one anomaly: severity, status, origin, text."""
    return (tr(SEVERITY_LABELS[anomaly.severity]), status_label(anomaly), tr(ORIGIN_LABELS[anomaly.origin]),
            anomaly.text)


def _text_width(font, texts, padding=16):
    """Width in pixels that shows the longest of texts in font without cutting it off."""
    return max(font.measure(text) for text in texts) + padding


class FlightAnnotationsPanel:
    """Note and anomalies of the flight shown on the single-flight page."""

    def __init__(self, parent, database):
        import tkinter as tk
        from tkinter import font as tkfont, ttk

        self.database = database              # DatabaseController (main-thread connection)
        self.log_id = None
        self._annotations_generation = None
        self._saved_note = ""
        self.frame = ttk.LabelFrame(parent, text=tr("Notiz und Auffälligkeiten"), padding=(8, 4))
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(1, weight=1)
        font = tkfont.nametofont("TkDefaultFont")
        line_height = font.metrics("linespace")

        ttk.Label(self.frame, text=tr("Notiz:")).grid(row=0, column=0, sticky="nw", padx=(0, 6))
        self.note = tk.Text(self.frame, height=3, wrap="word", font=font, relief="solid", borderwidth=1,
                            undo=True)
        self.note.grid(row=0, column=1, sticky="nsew")
        self.note.bind("<FocusOut>", lambda _event: self.save_note())
        self.save_button = ttk.Button(self.frame, text=tr("Notiz speichern"), command=self.save_note)
        self.save_button.grid(row=0, column=2, sticky="nw", padx=(6, 0))

        style = ttk.Style(self.frame)
        style.configure("Annotations.Treeview", rowheight=line_height + 6)   # row height follows the font
        columns = ("severity", "status", "origin", "text")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings", height=4, selectmode="browse",
                                 style="Annotations.Treeview")
        headings = {"severity": tr("Stufe"), "status": tr("Status"), "origin": tr("Herkunft"), "text": tr("Hinweis")}
        widths = {"severity": [headings["severity"]] + [tr(text) for text in SEVERITY_LABELS.values()],
                  "status": [headings["status"], tr("quittiert"), tr("offen")],
                  "origin": [headings["origin"]] + [tr(text) for text in ORIGIN_LABELS.values()]}
        for column in columns:
            self.tree.heading(column, text=headings[column], anchor="w")
            if column == "text":
                self.tree.column(column, width=font.measure("n" * TEXT_COLUMN_CHARACTERS), stretch=True)
            else:
                self.tree.column(column, width=_text_width(font, widths[column]), stretch=False)
        for severity, color in ((annotations.CRITICAL, "#b00020"), (annotations.WARNING, "#b36b00")):
            self.tree.tag_configure(severity, foreground=color)
        self.tree.tag_configure("acknowledged", foreground="#888888")
        self.tree.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=(6, 0))
        self.tree.bind("<<TreeviewSelect>>", lambda _event: self._show_selected())

        # the full text of the selected anomaly (the text column can be narrower than the text)
        self.selected_text = tk.StringVar()
        self.selected_label = ttk.Label(self.frame, textvariable=self.selected_text, justify="left",
                                        foreground="#333")
        self.selected_label.grid(row=2, column=0, columnspan=3, sticky="we", pady=(4, 0))
        self.frame.bind("<Configure>", lambda event: self.selected_label.configure(
            wraplength=max(200, event.width - 30)))
        self._build_buttons(ttk)
        database.add_listener(self._on_database_changed)
        self.frame.bind("<Destroy>", lambda event: database.remove_listener(self._on_database_changed)
                        if event.widget is self.frame else None)
        self.show_flight(None)

    def _build_buttons(self, ttk):
        bar = ttk.Frame(self.frame)
        bar.grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))
        self.acknowledge_button = ttk.Button(bar, text=tr("Quittieren / wieder öffnen"),
                                             command=self.toggle_acknowledged)
        self.acknowledge_button.pack(side="left", padx=(0, 6))
        self.add_button = ttk.Button(bar, text=tr("Eigener Eintrag …"), command=self.ask_entry)
        self.add_button.pack(side="left", padx=(0, 6))
        self.delete_button = ttk.Button(bar, text=tr("Eintrag löschen"), command=self.delete_selected)
        self.delete_button.pack(side="left")

    # ---------------- database ----------------
    def _connection(self):
        database = self.database.database
        return database.connection if database is not None else None

    def _changed(self):
        self.database.annotations_changed()

    def _on_database_changed(self):
        """New anomalies after a recalculation: list them again (the note being typed stays as it is)."""
        if self.database.annotations_generation != self._annotations_generation:
            self.show_anomalies()

    # ---------------- showing ----------------
    def show_flight(self, log_id):
        """Shows the note and the anomalies of a log (None: no flight). The note of the previous flight is saved."""
        self.save_note()
        self.log_id = log_id if self._connection() is not None else None
        self._saved_note = annotations.note_of(self._connection(), log_id) if self.log_id is not None else ""
        self.note.configure(state="normal")
        self.note.delete("1.0", "end")
        self.note.insert("1.0", self._saved_note)
        self.note.edit_reset()
        self.note.configure(state="normal" if self.log_id is not None else "disabled")
        for button in (self.save_button, self.add_button):
            button.state(["!disabled"] if self.log_id is not None else ["disabled"])
        self.show_anomalies()

    def anomalies(self):
        """The anomalies of the shown flight."""
        connection = self._connection()
        if self.log_id is None or connection is None:
            return []
        return annotations.anomalies_of(connection, self.log_id)

    def show_anomalies(self):
        self._annotations_generation = self.database.annotations_generation
        selected = self.selected_id()
        self.tree.delete(*self.tree.get_children())
        for anomaly in self.anomalies():
            tags = ("acknowledged",) if anomaly.acknowledged else (anomaly.severity,)
            self.tree.insert("", "end", iid=str(anomaly.anomaly_id), values=anomaly_row(anomaly), tags=tags)
        if selected is not None and self.tree.exists(str(selected)):
            self.tree.selection_set(str(selected))
        self._show_selected()

    def selected_id(self):
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def _selected(self):
        anomaly_id = self.selected_id()
        return next((anomaly for anomaly in self.anomalies() if anomaly.anomaly_id == anomaly_id), None)

    def _show_selected(self):
        anomaly = self._selected()
        self.selected_text.set(anomaly.text if anomaly is not None else
                               (tr("Keine Auffälligkeiten für diesen Flug.") if self.log_id is not None and
                                not self.tree.get_children() else ""))
        self.acknowledge_button.state(["!disabled"] if anomaly is not None else ["disabled"])
        self.delete_button.state(["!disabled"] if anomaly is not None and anomaly.origin == annotations.MANUAL
                                 else ["disabled"])

    # ---------------- changing ----------------
    def note_text(self):
        return self.note.get("1.0", "end").strip()

    def save_note(self):
        """Stores the note if it was changed."""
        if self.log_id is None or self._connection() is None or self.note_text() == self._saved_note.strip():
            return
        annotations.set_note(self._connection(), self.log_id, self.note_text())
        self._saved_note = self.note_text()
        self._changed()

    def toggle_acknowledged(self):
        anomaly = self._selected()
        if anomaly is None:
            return
        annotations.set_acknowledged(self._connection(), anomaly.anomaly_id, not anomaly.acknowledged)
        self._changed()
        self.show_anomalies()

    def add_entry(self, text, severity):
        """Adds an entry of the user to the shown flight (what the dialog of "Own entry" does)."""
        if self.log_id is None or not text.strip():
            return None
        anomaly_id = annotations.add_manual_anomaly(self._connection(), self.log_id, text, severity)
        self._changed()
        self.show_anomalies()
        self.tree.selection_set(str(anomaly_id))
        return anomaly_id

    def delete_selected(self):
        anomaly = self._selected()
        if anomaly is None or anomaly.origin != annotations.MANUAL:
            return
        annotations.delete_manual_anomaly(self._connection(), anomaly.anomaly_id)
        self._changed()
        self.show_anomalies()

    def ask_entry(self):
        """Dialog for an entry of the user: text and severity."""
        if self.log_id is None:
            return
        EntryDialog(self.frame.winfo_toplevel(), self.add_entry)


class EntryDialog:
    """Small window: text and severity of an own entry; OK adds it with on_ok(text, severity)."""

    def __init__(self, root, on_ok):
        import tkinter as tk
        from tkinter import ttk

        self.on_ok = on_ok
        self.window = tk.Toplevel(root)
        self.window.title(tr("Eigener Eintrag"))
        self.window.transient(root)
        frame = ttk.Frame(self.window, padding=10)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text=tr("Hinweis:")).grid(row=0, column=0, sticky="w")
        self.text = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=self.text, width=60)
        entry.grid(row=0, column=1, sticky="we", padx=(6, 0))
        ttk.Label(frame, text=tr("Stufe:")).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.severities = list(annotations.SEVERITIES)
        self.severity = ttk.Combobox(frame, values=[tr(SEVERITY_LABELS[s]) for s in self.severities],
                                     state="readonly", width=14)
        self.severity.current(self.severities.index(annotations.WARNING))
        self.severity.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(6, 0))
        buttons = ttk.Frame(frame)
        buttons.grid(row=2, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(buttons, text=tr("OK"), command=self.ok).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text=tr("Abbrechen"), command=self.window.destroy).pack(side="left")
        entry.focus_set()
        self.window.bind("<Return>", lambda _event: self.ok())
        self.window.bind("<Escape>", lambda _event: self.window.destroy())

    def ok(self):
        if self.text.get().strip():
            self.on_ok(self.text.get(), self.severities[self.severity.current()])
        self.window.destroy()
