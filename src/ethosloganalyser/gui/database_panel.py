# -*- coding: utf-8 -*-
"""Section "Database" on the page Data & settings: new, open, save as, empty, import with report.

DatabaseController owns the open flight database and runs imports in the background; it lives as long as
the window. DatabasePanel draws the section and is created again when the window content is rebuilt
(language switch). The single-flight area reads its flights from the database (flight_cache.py).
"""

import os
import queue
import threading

from ..config import Params, default_database_path
from ..db import DatabaseError, FlightDatabase, import_paths
from ..db import importer
from ..db.reanalysis import outdated_log_ids, reanalyse_outdated
from ..i18n import N_, tr

POLL_MS = 100

OUTCOME_LABELS = {
    importer.NEW: N_("neu"),
    importer.DUPLICATE: N_("doppelt"),
    importer.SUSPICIOUS: N_("mögliches Duplikat"),
    importer.UNREADABLE: N_("nicht lesbar"),
}

# order of the import report: what needs attention first
OUTCOME_ORDER = (importer.UNREADABLE, importer.SUSPICIOUS, importer.DUPLICATE, importer.NEW)


def format_size(size_bytes):
    """File size for the user: kB below one megabyte, otherwise MB with one decimal."""
    if size_bytes < 1024 * 1024:
        return tr("{size} kB", size=f"{size_bytes / 1024:.0f}")
    return tr("{size} MB", size=f"{size_bytes / (1024 * 1024):.1f}")


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


class BackgroundTask:
    """Runs work(database, progress, should_cancel) in a thread with its own database connection.

    The thread only puts messages into a queue; the main thread polls it (Tkinter must only be used there).
    """

    def __init__(self, root, database_path, work, on_progress, on_done):
        self.root = root
        self.database_path = database_path
        self.work = work
        self.on_progress = on_progress
        self.on_done = on_done
        self.messages = queue.Queue()
        self.cancel_requested = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        self.root.after(POLL_MS, self._poll)

    def cancel_and_wait(self, timeout_s=10.0):
        self.cancel_requested.set()
        self.thread.join(timeout_s)

    def _run(self):
        try:
            database = FlightDatabase(self.database_path)
        except Exception as error:
            self.messages.put(("error", error))
            return
        try:
            result = self.work(database, lambda *state: self.messages.put(("progress", state)),
                               self.cancel_requested.is_set)
            self.messages.put(("done", result))
        except Exception as error:                   # report it in the window instead of losing it
            self.messages.put(("error", error))
        finally:
            database.close()

    def _poll(self):
        finished = False
        while True:
            try:
                kind, value = self.messages.get_nowait()
            except queue.Empty:
                break
            if kind == "progress":
                self.on_progress(*value)
            else:
                finished = True
                self.on_done(kind, value)
        if not finished:
            try:
                self.root.after(POLL_MS, self._poll)
            except Exception:                       # window already closed
                pass


class DatabaseController:
    """The open flight database of the window and the background work on it."""

    def __init__(self, root, messagebox):
        self.root = root
        self.messagebox = messagebox
        self.database = None
        self.task = None
        self.progress = None                         # (done, total, text) while a background task runs
        self.last_report = None
        self.listeners = []
        # raised whenever the content may have changed (other database, import, recalculation, emptied), so
        # views built from the database know when to read it again
        self.generation = 0

    # ---------------- state ----------------
    @property
    def path(self):
        return self.database.path if self.database is not None else ""

    @property
    def busy(self):
        """True from the start of a background task until its result has been taken over."""
        return self.task is not None

    def stats(self):
        return self.database.stats() if self.database is not None else None

    def add_listener(self, listener):
        """listener() is called whenever path, contents or progress change."""
        self.listeners.append(listener)

    def remove_listener(self, listener):
        if listener in self.listeners:
            self.listeners.remove(listener)

    def _changed(self):
        for listener in list(self.listeners):
            listener()

    # ---------------- open, new, save as, empty ----------------
    def _use(self, database):
        if self.database is not None:
            self.database.close()
        self.database = database
        self.generation += 1
        self._changed()
        self._reanalyse_if_needed()

    def open_path(self, path):
        """Opens (or creates) the database at path. Shows an error and returns False if that fails."""
        try:
            database = FlightDatabase(path)
        except (DatabaseError, OSError) as error:
            self.messagebox.showerror(tr("Datenbank"), tr("Die Datei kann nicht als Flug-Datenbank geöffnet "
                                                          "werden:\n{path}\n\n{error}", path=path, error=error))
            return False
        self._use(database)
        return True

    def create_new(self, path):
        """Creates a new, empty database at path (an existing file there is replaced) and opens it."""
        if self.database is not None and os.path.abspath(path) == self.path:
            self.database.close()
            self.database = None
        try:
            database = FlightDatabase.create_new(path)
        except (DatabaseError, OSError) as error:
            self.messagebox.showerror(tr("Datenbank"), tr("Die Datenbank kann nicht angelegt werden:\n{path}\n\n"
                                                          "{error}", path=path, error=error))
            return False
        self._use(database)
        return True

    def save_copy(self, path):
        """Writes a copy of the open database to path (the open database stays the same)."""
        try:
            self.database.save_as(path)
        except Exception as error:
            self.messagebox.showerror(tr("Datenbank"), tr("Die Kopie kann nicht gespeichert werden:\n{path}\n\n"
                                                          "{error}", path=path, error=error))
            return False
        return True

    def clear(self):
        """Deletes all logs and flights from the open database (the log files themselves stay untouched)."""
        self.database.clear()
        self.generation += 1
        self.last_report = None
        self._changed()

    def flights_changed(self):
        """Tells the views that flights were changed in place (e.g. a log switched between flight and no flight)."""
        self.generation += 1
        self._changed()

    def start(self, saved, offer_import):
        """At program start: opens the last database; without one the default database is created and
        offer_import(folder) is called with the last used log folder (if any) so it can be imported."""
        last_path = saved.get("database")
        if last_path:
            if os.path.exists(last_path) and self.open_path(last_path):
                return
            if not os.path.exists(last_path):
                self.messagebox.showwarning(tr("Datenbank"), tr("Die zuletzt geöffnete Datenbank wurde nicht "
                                                                "gefunden:\n{path}\n\nEs wird die Standard-"
                                                                "Datenbank verwendet.", path=last_path))
        default_path = default_database_path()
        is_new = not os.path.exists(default_path)
        if self.open_path(default_path) and is_new and not last_path:
            folder = saved.get("folder") or ""
            if folder and os.path.isdir(folder):
                offer_import(folder)

    # ---------------- background work ----------------
    def _run_in_background(self, work, on_finished):
        def on_progress(done, total, text=""):
            self.progress = (done, total, text)
            self._changed()

        def on_done(kind, value):
            self.task = None
            self.progress = None
            if kind == "error":
                self.messagebox.showerror(tr("Datenbank"), tr("Fehler bei der Verarbeitung:\n{error}", error=value))
            else:
                on_finished(value)
            self.generation += 1
            self._changed()

        self.task = BackgroundTask(self.root, self.path, work, on_progress, on_done)
        self.progress = (0, 0, "")
        self.task.start()
        self._changed()

    def start_import(self, paths, params, on_report=None):
        """Imports files and folders in the background; on_report(report) is called when it is finished."""
        if self.busy or self.database is None or not paths:
            return False

        def work(database, progress, should_cancel):
            return import_paths(database, paths, params, progress=progress, should_cancel=should_cancel)

        def finished(report):
            self.last_report = report
            if on_report is not None:
                on_report(report)

        self._run_in_background(work, finished)
        return True

    def _reanalyse_if_needed(self):
        """Flights stored with an older analysis version are calculated again in the background."""
        if self.busy or self.database is None or not outdated_log_ids(self.database.connection):
            return
        self._run_in_background(lambda database, progress, should_cancel: reanalyse_outdated(
            database, Params(), progress=lambda done, total: progress(done, total, tr("Neuberechnung")),
            should_cancel=should_cancel), lambda _count: None)

    def close(self):
        """At program end: stops a running import after the current file and closes the database."""
        if self.task is not None:
            self.task.cancel_and_wait()
        if self.database is not None:
            self.database.close()
            self.database = None


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


class DatabasePanel:
    """The section "Database" on Data & settings, drawn into parent.

    read_params() gives the analysis settings (config.Params) or None after showing an input error.
    Attributes used by tests: path, stats, progress (Tk variables), actions (buttons), report (last report
    window: dict(window, tree)), run_import(paths).
    """

    def __init__(self, parent, controller, read_params, filedialog, messagebox):
        import tkinter as tk
        from tkinter import ttk

        self.controller = controller
        self.read_params = read_params
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.report = None
        self.frame = ttk.LabelFrame(parent, text=tr("Datenbank"), padding=10)
        self.frame.columnconfigure(1, weight=1)
        ttk.Label(self.frame, text=tr("Datei:")).grid(row=0, column=0, sticky="w")
        self.path, self.stats, self.progress = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(self.frame, textvariable=self.path).grid(row=0, column=1, columnspan=2, sticky="w", padx=(6, 0))
        ttk.Label(self.frame, textvariable=self.stats, foreground="#666").grid(row=1, column=1, columnspan=2,
                                                                               sticky="w", padx=(6, 0))
        self._build_buttons()
        self.progress_bar = ttk.Progressbar(self.frame, mode="determinate")
        self.progress_bar.grid(row=3, column=0, columnspan=3, sticky="we", pady=(8, 0))
        ttk.Label(self.frame, textvariable=self.progress, foreground="#666").grid(row=4, column=0, columnspan=3,
                                                                                  sticky="w", pady=(4, 0))
        controller.add_listener(self.refresh)
        self.frame.bind("<Destroy>", lambda event: controller.remove_listener(self.refresh)
                        if event.widget is self.frame else None)
        self.refresh()

    def _build_buttons(self):
        from tkinter import ttk
        buttons = ttk.Frame(self.frame)
        buttons.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.actions = {}
        for key, text, command in (("new", tr("Neu …"), self.new_database), ("open", tr("Öffnen …"), self.open_database),
                                   ("save_as", tr("Speichern unter …"), self.save_as),
                                   ("clear", tr("Leeren …"), self.clear_database),
                                   ("import_files", tr("Dateien importieren …"), self.import_files),
                                   ("import_folder", tr("Ordner importieren …"), self.import_folder)):
            self.actions[key] = ttk.Button(buttons, text=text, command=command)
            self.actions[key].pack(side="left", padx=(0, 6) if key != "clear" else (0, 24))

    # ---------------- actions ----------------
    @staticmethod
    def _file_types():
        return [(tr("Flug-Datenbank"), "*.db"), (tr("Alle Dateien"), "*.*")]

    def _start_folder(self):
        return os.path.dirname(self.controller.path) or None

    def new_database(self):
        path = self.filedialog.asksaveasfilename(title=tr("Neue Datenbank anlegen"), defaultextension=".db",
                                                 filetypes=self._file_types(), initialdir=self._start_folder())
        if path:
            self.controller.create_new(path)

    def open_database(self):
        path = self.filedialog.askopenfilename(title=tr("Datenbank öffnen"), filetypes=self._file_types(),
                                               initialdir=self._start_folder())
        if path:
            self.controller.open_path(path)

    def save_as(self):
        path = self.filedialog.asksaveasfilename(title=tr("Datenbank speichern unter"), defaultextension=".db",
                                                 filetypes=self._file_types(), initialdir=self._start_folder())
        if path and self.controller.save_copy(path):
            self.messagebox.showinfo(tr("Datenbank"), tr("Eine Kopie der Datenbank wurde gespeichert:\n{path}\n\n"
                                                         "Geöffnet bleibt weiterhin:\n{current}",
                                                         path=path, current=self.controller.path))

    def clear_database(self):
        if self.messagebox.askyesno(tr("Datenbank leeren"), tr("Alle importierten Logs und Flüge aus der Datenbank "
                                                               "löschen?\n\nDie Logdateien selbst bleiben "
                                                               "unverändert.")):
            self.controller.clear()

    def run_import(self, paths):
        params = self.read_params()
        if params is not None:
            self.controller.start_import(paths, params, on_report=self.show_report)

    def import_files(self):
        paths = self.filedialog.askopenfilenames(title=tr("Logdateien importieren"),
                                                 filetypes=[(tr("Ethos-Logs"), "*.csv"), (tr("Alle Dateien"), "*.*")])
        if paths:
            self.run_import(list(paths))

    def import_folder(self):
        folder = self.filedialog.askdirectory(title=tr("Ordner importieren (mit Unterordnern)"))
        if folder:
            self.run_import([folder])

    def show_report(self, report):
        self.report = show_import_report(self.frame.winfo_toplevel(), report)

    # ---------------- display ----------------
    def refresh(self):
        """Shows path, contents, progress and the last import of the database."""
        controller = self.controller
        self.path.set(controller.path or tr("keine Datenbank geöffnet"))
        stats = controller.stats()
        self.stats.set("" if stats is None else tr(
            "{logs} Logs: {flights} Flüge, {other} ohne Flug · Flugzeuge: {aircraft} · {size}",
            logs=stats.log_count, flights=stats.flight_count, other=stats.non_flight_count,
            aircraft=stats.aircraft_count, size=format_size(stats.size_bytes)))
        state = "disabled" if controller.busy or controller.database is None else "normal"
        for key, button in self.actions.items():
            button.configure(state="normal" if key in ("new", "open") and not controller.busy else state)
        if controller.progress is not None:
            done, total, text = controller.progress
            self.progress_bar.grid()
            self.progress_bar.configure(maximum=max(total, 1), value=done)
            self.progress.set(tr("{done} von {total}: {file}", done=done, total=total, file=text) if total else
                              tr("wird vorbereitet …"))
        else:
            self.progress_bar.grid_remove()
            self.progress.set(tr("Letzter Import: {summary}", summary=report_summary(controller.last_report))
                              if controller.last_report else "")
