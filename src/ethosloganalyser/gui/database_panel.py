# -*- coding: utf-8 -*-
"""Section "Database" on the page Data & settings: new, open, save as, empty, import with report
(gui/import_report.py).

DatabaseController owns the open flight database and runs imports in the background; it lives as long as
the window. DatabasePanel draws the section and is created again when the window content is rebuilt
(language switch). The single-flight area reads its flights from the database (flight_cache.py).
"""

import os
import queue
import threading

from ..config import Params, default_database_path
from ..db import DatabaseError, FlightDatabase, import_paths
from ..db.reanalysis import outdated_log_ids, reanalyse_outdated
from ..i18n import tr
from .import_report import report_summary, show_import_report

POLL_MS = 100


def format_size(size_bytes):
    """File size for the user: kB below one megabyte, otherwise MB with one decimal."""
    if size_bytes < 1024 * 1024:
        return tr("{size} kB", size=f"{size_bytes / 1024:.0f}")
    return tr("{size} MB", size=f"{size_bytes / (1024 * 1024):.1f}")


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
        self.task_changes_flights = False            # False: the running task changes only notes or anomalies
        self.progress = None                         # (done, total, text) while a background task runs
        self.last_report = None
        self.listeners = []
        # raised whenever the content may have changed (other database, import, recalculation, emptied), so
        # views built from the database know when to read it again
        self.generation = 0
        # raised when only notes or anomalies changed: the logbook updates its symbols, the prepared single flights
        # stay valid (they depend on generation only)
        self.annotations_generation = 0
        # called after the flights themselves may have changed (opened, emptied, imported, recalculated, switched
        # between flight and no flight) - e.g. to judge the anomalies again
        self.content_hooks = []

    # ---------------- state ----------------
    @property
    def path(self):
        return self.database.path if self.database is not None else ""

    @property
    def busy(self):
        """True from the start of a background task until its result has been taken over."""
        return self.task is not None

    @property
    def busy_with_flights(self):
        """True while an import or recalculation of flights runs. A recalculation of the anomalies does not count:
        it is stopped when the user starts something else (and done again afterwards)."""
        return self.task is not None and self.task_changes_flights

    def _stop_annotation_task(self):
        """Stops a running recalculation of the anomalies, so the user can import, open or empty at once. It is
        requested again (content hooks) and runs after the new work."""
        if self.task is None or self.task_changes_flights:
            return
        self.task.cancel_and_wait()
        self.task = None
        self.progress = None
        self._content_changed()

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

    def _content_changed(self):
        for hook in list(self.content_hooks):
            hook()

    # ---------------- open, new, save as, empty ----------------
    def _use(self, database):
        self._stop_annotation_task()
        if self.database is not None:
            self.database.close()
        self.database = database
        self.generation += 1
        self._changed()
        self._reanalyse_if_needed()
        self._content_changed()

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
        self._stop_annotation_task()
        self.database.clear()
        self.generation += 1
        self.annotations_generation += 1
        self.last_report = None
        self._changed()
        self._content_changed()

    def flights_changed(self):
        """Tells the views that flights were changed in place (e.g. a log switched between flight and no flight)."""
        self.generation += 1
        self._changed()
        self._content_changed()

    def annotations_changed(self):
        """Tells the views that notes or anomalies changed (the flights themselves did not)."""
        self.annotations_generation += 1
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
    def _run_in_background(self, work, on_finished, changes_flights=True):
        """Runs work in a background task. changes_flights=False: the work changes only notes or anomalies."""
        def on_progress(done, total, text=""):
            self.progress = (done, total, text)
            self._changed()

        def on_done(kind, value):
            if self.task is not task:
                return                              # a stopped recalculation of the anomalies; nothing to take over
            self.task = None
            self.progress = None
            if kind == "error":
                self.messagebox.showerror(tr("Datenbank"), tr("Fehler bei der Verarbeitung:\n{error}", error=value))
            else:
                on_finished(value)
            if changes_flights:
                self.generation += 1
            self.annotations_generation += 1
            self._changed()
            if changes_flights:
                self._content_changed()

        task = BackgroundTask(self.root, self.path, work, on_progress, on_done)
        self.task, self.task_changes_flights = task, changes_flights
        self.progress = (0, 0, "") if changes_flights else None     # a quick recalculation shows no bar
        task.start()
        self._changed()

    def start_import(self, paths, params, on_report=None):
        """Imports files and folders in the background; on_report(report) is called when it is finished."""
        if self.busy_with_flights or self.database is None or not paths:
            return False
        self._stop_annotation_task()

        def work(database, progress, should_cancel):
            return import_paths(database, paths, params, progress=progress, should_cancel=should_cancel)

        def finished(report):
            self.last_report = report
            if on_report is not None:
                on_report(report)

        self._run_in_background(work, finished)
        return True

    def run_annotation_task(self, work, on_finished=None):
        """Runs work(database, progress, should_cancel) in the background; it may change only notes and anomalies.
        Returns False if another task is running or no database is open."""
        if self.busy or self.database is None:
            return False
        self._run_in_background(work, on_finished or (lambda _result: None), changes_flights=False)
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
        busy = controller.busy_with_flights
        state = "disabled" if busy or controller.database is None else "normal"
        for key, button in self.actions.items():
            button.configure(state="normal" if key in ("new", "open") and not busy else state)
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
