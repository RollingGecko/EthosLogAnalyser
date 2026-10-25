# -*- coding: utf-8 -*-
"""Main window of the app (Tkinter).

The window content is built by ``MainWindow.build()``. When the user switches the language, the content is
destroyed and built again in the new language; the analysis result, the settings, the selected flight, view,
zoom and tab are kept, so the logs do not have to be analysed again.

Four areas, as tabs at the top: Logbook (start page, from the flight database), Single flight (flights from the
flight database), Statistics (pages over all flights of the analysed folder) and Data & settings.

The pages are separate modules: settings_page (Data & settings), statistics_page, flight_page with flight_area
and flight_cache (single flight from the database), logbook_page with logbook_model, flight_filter,
logbook_group_tree and logbook_flight_list; charts (chart canvases, full screen), app_settings (input fields,
battery per model), database_panel.

The status line shows the state of the flight database on the logbook and the single-flight area and the
result of the last folder analysis everywhere else.
"""

import os

from ..analysis.fleet import analyse_folder, default_model, find_logs, models_in
from ..buildinfo import window_title
from ..config import MODEL_UNKNOWN_LABEL, load_settings, model_label
from ..gui.anomaly_controller import AnomalyController
from ..gui.app_settings import BATTERY_HINT, AppSettings
from ..gui.charts import ChartManager
from ..gui.common import export_table
from ..gui.database_panel import DatabaseController
from ..gui.flight_annotations import FlightAnnotationsPanel
from ..gui.flight_area import DatabaseFlightArea
from ..gui.flight_cache import FlightCache
from ..gui.flight_filter import FilterState
from ..gui.flight_page import FlightPage
from ..gui.logbook_model import LogbookModel
from ..gui.logbook_page import LogbookPage
from ..gui.settings_page import SettingsPage
from ..gui.statistics_model import READY, StatisticsModel, filter_description
from ..gui.statistics_page import CHART_PAGES, PAGE_KEYS, StatisticsPages, page_title, report_lines
from ..gui.style import BG, _setup_style
from ..i18n import LANGUAGES, Msg, detect_language, fmt_date, get_language, set_language, tr
from ..plots.flight import FLIGHT_VIEWS, figure_flight
from ..report.text import flight_detail_lines, summary_lines

# time after the program start before database flights are prepared in the background
START_DELAY_MS = 700

# areas of the window (tabs at the top) in their order; the statistics area holds the pages PAGE_KEYS
AREA_KEYS = ("logbook", "flight", "statistics", "settings")

# areas whose status line shows the state of the flight database
DATABASE_STATUS_AREAS = ("logbook", "flight")


def tab_title(key):
    """Title of an area or statistics page in the current language."""
    titles = {"logbook": tr("Logbuch"), "flight": tr("Einzelflug"), "statistics": tr("Statistik"),
              "settings": tr("Daten & Einstellungen")}
    return titles[key] if key in titles else page_title(key)


def _view_key(view, lines):
    """What a statistics view shows; the pages are drawn again only when it changed."""
    return (view.state, view.aircraft, view.n_flights, view.n_total, id(view.result), view.params,
            view.aircraft_names, tuple(lines))


class MainWindow:
    """The window: settings, database and analysis result survive a rebuild; the pages are built anew."""

    def __init__(self):
        import tkinter as tk
        from tkinter import filedialog, messagebox

        try:                                         # sharp rendering on Windows
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self.filedialog, self.messagebox = filedialog, messagebox
        self.root = tk.Tk()
        self.root.geometry("1400x950")
        self.root.configure(background=BG)
        self.family = _setup_style(self.root)

        self.saved = load_settings()
        set_language(self.saved.get("language") or detect_language())
        self.settings = AppSettings(self.root, self.saved)
        self.settings.on_battery_confirmed = self.show_battery_hint
        self.database = DatabaseController(self.root, messagebox)     # flight database (section "Database")
        self.anomalies = AnomalyController(self.root, self.database, self.settings)   # keeps anomalies up to date
        self.flight_cache = FlightCache(self.root, self.database, self.settings.params_for_model)
        self.flight_area = None
        self.filter_state = FilterState()                  # the flight filter, shared by the pages that use it
        self.logbook_model = LogbookModel(self.database, self.settings.params_for_model)
        self.logbook_page = None
        # statistics: the database flights that pass the shared filter, one aircraft at a time
        self.statistics_model = StatisticsModel(self.flight_cache, self.filter_state, self.settings.params_for_model)
        self.statistics = None
        self.database.add_listener(self._on_database_changed)
        self.flight_cache.add_listener(self.refresh_statistics)
        self.filter_state.add_listener(self.refresh_statistics)
        # result of the folder analysis
        self.res, self.params, self.folder = None, None, ""
        self.models = {}                                   # {model: number of logs} of the last analysed folder
        self.status_msg = Msg("Noch nicht ausgewertet – Ordner und Akku im Reiter „Daten & Einstellungen“ "
                              "festlegen.")
        self.status_main = self.status_shown = None
        self.content = None

    # ---------------- building ----------------
    def build(self, snap=None):
        """Builds the complete window content in the current language."""
        import tkinter as tk
        from tkinter import ttk

        if self.content is not None:
            self.content.destroy()
        self.root.title(window_title())
        self.content = ttk.Frame(self.root)
        self.content.pack(fill="both", expand=True)
        self.status = tk.StringVar(value=str(self.status_msg))
        ttk.Label(self.content, textvariable=self.status, style="Status.TLabel").pack(fill="x")
        self.notebook = ttk.Notebook(self.content)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=(4, 6))
        self.tabs = self._add_tabs(self.notebook, AREA_KEYS)
        statistics_header = ttk.Frame(self.tabs["statistics"], padding=(10, 8, 10, 0))
        statistics_header.pack(fill="x")
        self.statistics_notebook = ttk.Notebook(self.tabs["statistics"], style="Pages.TNotebook")
        self.statistics_notebook.pack(fill="both", expand=True, pady=(4, 0))
        self.tabs.update(self._add_tabs(self.statistics_notebook, PAGE_KEYS))

        self.charts = ChartManager(self.root)
        self.settings_page = SettingsPage(self.tabs["settings"], self, {
            "run": self.run_analysis, "choose_folder": self.choose_folder, "model_chosen": self.choose_model,
            "language": self.change_language, "export_csv": self.export_csv, "export_all": self.export_all})
        self.settings_page.update_model_box(self.models, self.settings.model)
        self.statistics = StatisticsPages(statistics_header, self.statistics_notebook,
                                          {key: self.tabs[key] for key in PAGE_KEYS}, self.charts, self.family,
                                          self.filter_state)
        self.flight_page = FlightPage(self.tabs["flight"], self.charts, self.family, self.filedialog,
                                      back=lambda: self.select_page("logbook"))
        self.flight_annotations = FlightAnnotationsPanel(self.flight_page.side_frame, self.database)
        self.flight_annotations.frame.pack(fill="both", expand=True)
        self.flight_area = DatabaseFlightArea(self.flight_page, self.flight_cache, self.flight_annotations)
        self.flight_area.reload(force=True)
        self.logbook_page = LogbookPage(self.tabs["logbook"], self.charts, self.family, tab_title("logbook"),
                                        self.logbook_model, self.filter_state)
        self.logbook_page.on_open_flight = self.open_logbook_flight
        self.logbook_page.on_switch_flight = self.switch_logbook_flight
        if self.database.database is not None:       # at program start the database is opened right after this
            self.logbook_page.refresh()
            self.logbook_page.show()

        self.show_battery_hint()
        if snap is not None:
            self.flight_page.restore(snap["flight_page"])
            self.notebook.select(snap["tab"])
            self.statistics_notebook.select(snap["statistics_tab"])
        else:
            self.select_page("logbook")
        self.root._akku = self.test_handles()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_area_changed)
        self.refresh_statistics()
        self._show_status()

    @staticmethod
    def _add_tabs(notebook, keys):
        from tkinter import ttk
        frames = {}
        for key in keys:
            frames[key] = ttk.Frame(notebook)
            notebook.add(frames[key], text=tab_title(key))
        return frames

    def select_page(self, key):
        """Shows an area, or a statistics page inside the statistics area."""
        if key in PAGE_KEYS:
            self.notebook.select(self.tabs["statistics"])
            self.statistics_notebook.select(self.tabs[key])
        else:
            self.notebook.select(self.tabs[key])

    def read_params(self):
        return self.settings.read_params(self.messagebox)

    def set_status(self, msg):
        """Stores the status of the folder analysis; it is shown on the areas that do not show the database."""
        self.status_msg = msg
        self._show_status()

    def current_area(self):
        """Key of the area (tab at the top) that is shown."""
        return AREA_KEYS[self.notebook.index("current")]

    def _show_status(self):
        """Status line: the state of the flight database on the logbook and single-flight areas, otherwise the
        result of the last folder analysis."""
        if self.current_area() == "statistics" and self.statistics is not None:
            self.status.set(self.statistics_status_text())
        elif self.current_area() in DATABASE_STATUS_AREAS:
            self.status.set(self.database_status_text())
        else:
            self.status.set(str(self.status_msg))

    def database_status_text(self):
        """Flights, aircraft and period of the flight database in the current language."""
        summary = self.logbook_model.summary()
        if not summary.n_flights:
            return tr("Die Flug-Datenbank enthält noch keine Flüge – Logs unter „Daten & Einstellungen“ → "
                      "„Datenbank“ importieren.")
        text = tr("Flug-Datenbank  ·  {flights} Flüge, {aircraft} Flugzeuge  ·  {first} – {last}",
                  flights=summary.n_flights, aircraft=summary.n_aircraft, first=fmt_date(summary.first),
                  last=fmt_date(summary.last))
        if summary.n_non_flights:
            text += tr("  ·  {n} Logs ohne Flug", n=summary.n_non_flights)
        return text

    def _on_area_changed(self, _event=None):
        """Another area was chosen: the logbook picks up changed battery settings, the status line follows; changed
        battery settings also judge the anomalies again. A note being typed is saved when the area is left."""
        self.flight_annotations.save_note()
        if self.current_area() == "logbook":
            self.logbook_page.refresh()
        self.anomalies.check_settings()
        self.refresh_statistics()                  # battery settings may have changed; prepares the aircraft
        self._show_status()

    # ---------------- folder analysis ----------------
    def choose_folder(self):
        folder = self.filedialog.askdirectory(title=tr("Ordner mit Ethos-Logfiles wählen"),
                                              initialdir=self.settings.folder.get() or None)
        if folder:
            self.settings.folder.set(folder)

    def choose_model(self, model):
        if model != self.settings.model:
            self.root.after_idle(lambda: (self.settings.use_model(model), self.run_analysis()))

    def run_analysis(self):
        """Analyses the log folder for the selected model and shows the result on all pages."""
        folder = self.settings.folder.get()
        if not folder or not os.path.isdir(folder):
            self.messagebox.showwarning(tr("Ordner"), tr("Bitte zuerst einen gültigen Ordner wählen."))
            return
        groups = models_in(find_logs(folder))
        model = self.settings.model if self.settings.model in groups else default_model(groups)
        self.settings.use_model(model)                     # battery settings of that model
        self.show_battery_hint()
        params = self.read_params()
        if params is None:
            return
        self.store_settings()
        self.set_status(Msg("Werte aus …"))
        run_button = self.settings_page.run_button
        run_button.state(["disabled"])
        self.root.update_idletasks()

        def progress(done, total):
            self.settings_page.set_progress(done, total)
            self.root.update_idletasks()

        try:
            res = analyse_folder(folder, params, progress, model=model)
        except Exception as error:                        # unexpected error: report it understandably
            self.messagebox.showerror(tr("Fehler bei der Auswertung"), f"{type(error).__name__}: {error}")
            self.set_status(Msg("Fehler bei der Auswertung."))
            return
        finally:
            run_button.state(["!disabled"])
        self.res, self.params, self.folder = res, params, folder
        self.models = res.meta.get("models", {})
        self.settings_page.update_model_box(self.models, self.settings.model)
        self._set_status_after_analysis(folder, model, res, params)
        self.show_results()
        self.select_page("summary")

    def _set_status_after_analysis(self, folder, model, res, params):
        cells = res.meta.get("cells", params.cells)
        capacity = f", {params.nominal_mah:.0f} mAh" if params.nominal_mah > 0 else Msg(", Kapazität unbekannt")
        status_args = dict(folder=os.path.basename(os.path.normpath(folder)), n=len(res.df),
                           skipped=len(res.skipped), total=res.total, cells=cells, chem=params.chem, cap=capacity)
        if len(self.models) > 1:
            self.set_main_status(Msg("{folder}  ·  Modell {model}  ·  {n} Flüge ausgewertet, {skipped} von {total} "
                                     "Dateien übersprungen  ·  Akku {cells}S {chem}{cap}",
                                     model=model if model else Msg(MODEL_UNKNOWN_LABEL), **status_args))
        else:
            self.set_main_status(Msg("{folder}  ·  {n} Flüge ausgewertet, {skipped} von {total} Dateien "
                                     "übersprungen  ·  Akku {cells}S {chem}{cap}", **status_args))

    def set_main_status(self, msg):
        """Status line after an analysis; while the battery of the model is not set up it names that."""
        self.status_main = msg
        shown = Msg("{status}  ·  {hint}", status=msg, hint=Msg("Akku-Einstellungen für dieses Modell fehlen")) \
            if self.settings.battery_unset else msg
        self.status_shown = shown
        self.set_status(shown)

    # ---------------- statistics ----------------
    def statistics_lines(self, view):
        """Summary of the statistics: experimental notice, battery hint for the aircraft if its battery settings
        are missing, the summary of the analysis."""
        hint = None
        if view.state == READY and not self.settings.battery_chosen(view.aircraft):
            hint = tr(BATTERY_HINT, model=model_label(view.aircraft))
        return report_lines(view, hint)

    def refresh_statistics(self):
        """Shows the statistics for the current filter (only what changed is drawn again)."""
        if self.statistics is None or not self.statistics.frames["summary"].winfo_exists():
            return
        view = self.statistics_model.view(prepare=self.current_area() == "statistics")
        lines = self.statistics_lines(view)
        if self.statistics.view is None or _view_key(view, lines) != _view_key(self.statistics.view,
                                                                                self.statistics.lines):
            self.statistics.show(view, lines)
        if self.current_area() == "statistics":
            self._show_status()

    def statistics_status_text(self):
        """Status line on the statistics: flights of the filter, aircraft and period."""
        view = self.statistics.view
        if view is None or not view.n_total:
            return self.database_status_text()
        text = tr("Statistik  ·  {n} von {total} Flügen der Datenbank", n=view.n_flights, total=view.n_total)
        if view.aircraft is not None:
            text += "  ·  " + model_label(view.aircraft)
        if view.first is not None:
            text += f"  ·  {fmt_date(view.first)} – {fmt_date(view.last)}"
        described = filter_description(self.filter_state.value)
        if described:
            text += "  ·  " + tr("Filter: {filter}", filter=described)
        if view.state == READY and not self.settings.battery_chosen(view.aircraft):
            text += "  ·  " + tr("Akku-Einstellungen für dieses Modell fehlen")
        return text

    def show_battery_hint(self):
        """Shows or hides the battery hint next to the battery fields, in the status line and the summary."""
        if getattr(self, "settings_page", None) is None:
            return
        self.settings_page.show_battery_hint(self.settings.battery_unset)
        if self.status_shown is not None and self.status_msg is self.status_shown:
            self.set_main_status(self.status_main)          # still the status of the last analysis
        self.refresh_statistics()

    def show_results(self):
        """Shows the skipped files of the folder analysis."""
        self.settings_page.show_skipped(self.res.skipped)

    # ---------------- single flight from the database ----------------
    def _on_database_changed(self):
        if self.flight_area is not None:
            self.flight_area.reload()
        if self.logbook_page is not None:
            self.logbook_page.refresh()
        self.refresh_statistics()
        self._show_status()

    def open_logbook_flight(self, log_id):
        """Double-click in the logbook: shows that flight from the database on the single-flight page."""
        if not self.flight_area.open_flight(log_id):
            self.messagebox.showinfo(tr("Einzelflug"), tr("Dieser Log ist nicht als Flug gezählt. Zum Ansehen im "
                                                          "Logbuch in der Spalte „Flug“ auf ☑ umschalten."))
            return
        self.select_page("flight")

    def switch_logbook_flight(self, log_id):
        """Switch in the flight list: decides by hand whether a log is a flight; every page reads it again."""
        if self.logbook_model.switch_flight(log_id):
            self.database.flights_changed()

    # ---------------- export ----------------
    def _exportable_view(self):
        """The statistics view to export, or None after telling the user why there is nothing to export."""
        view = self.statistics_model.view(prepare=False)
        if view.state != READY or view.result.df.empty:
            self.messagebox.showinfo(tr("Export"), tr("Die Statistik zeigt gerade keine Flüge:\n{reason}",
                                                      reason=view.message or tr("Kein Flug passt zum Filter.")))
            return None
        return view

    def export_csv(self):
        """The table of the statistics (filtered flights of one aircraft) as CSV."""
        view = self._exportable_view()
        if view is None:
            return
        path = self.filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            export_table(view.result.df).to_csv(path, index=False, sep=";", decimal=",", encoding="utf-8-sig")

    def export_all(self):
        """Summary, all statistics charts, the table and the selected single flight into a folder."""
        view = self._exportable_view()
        if view is None:
            return
        folder = self.filedialog.askdirectory(title=tr("Zielordner für Bericht und Diagramme"))
        if not folder:
            return
        with open(os.path.join(folder, tr("zusammenfassung.txt")), "w", encoding="utf-8") as handle:
            for _, line in self.statistics_lines(view):
                handle.write(line + "\n")
        for name, draw in CHART_PAGES.items():
            draw(view.result, view.params).savefig(os.path.join(folder, f"{name}.png"), dpi=150)
        self._export_flight(folder)
        export_table(view.result.df).to_csv(os.path.join(folder, tr("fluege.csv")), index=False, sep=";",
                                            decimal=",", encoding="utf-8-sig")
        self.messagebox.showinfo(tr("Gespeichert"), tr("Bericht, Tabelle und Diagramme wurden in\n{folder}\n"
                                                       "gespeichert.", folder=folder))

    def _export_flight(self, folder):
        """Details and all views of the flight selected on the single-flight page."""
        selected = self.flight_page.current()
        if selected is None:
            return
        result, params, path = selected
        number = int(result.df.loc[result.df["pfad"] == path, "Flug"].iloc[0])
        with open(os.path.join(folder, tr("flug{no}_details.txt", no=number)), "w", encoding="utf-8") as handle:
            for _, line in flight_detail_lines(result, params, path):
                handle.write(line + "\n")
        for k, view in enumerate(FLIGHT_VIEWS):
            figure_flight(result, params, path, view).savefig(
                os.path.join(folder, tr("flug{no}_{view}.png", no=number, view=k + 1)), dpi=130)

    # ---------------- language, settings, closing ----------------
    def snapshot(self):
        """What the user is looking at - restored after a language switch."""
        return {"tab": self.notebook.index("current"), "statistics_tab": self.statistics_notebook.index("current"),
                "flight_page": self.flight_page.snapshot()}

    def change_language(self, code):
        """Switches the language and builds the window content again (the analysis result is kept)."""
        if code == get_language() or code not in LANGUAGES:
            return
        snap = self.snapshot()
        set_language(code)
        self.store_settings()
        self.build(snap)

    def store_settings(self):
        self.settings.store(self.database.path)

    def close(self):
        self.flight_annotations.save_note()
        self.store_settings()
        self.flight_cache.close()
        self.database.close()
        self.root.destroy()

    def offer_folder_import(self, folder):
        """First start with the database: offer to import the log folder used so far."""
        if self.messagebox.askyesno(tr("Datenbank"), tr("Es wurde eine neue Flug-Datenbank angelegt:\n{path}\n\n"
                                                        "Sollen die Logs aus dem bisher genutzten Ordner importiert "
                                                        "werden?\n{folder}", path=self.database.path,
                                                        folder=folder)):
            self.settings_page.db_panel.run_import([folder])

    def start(self):
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.flight_cache.paused = True
        self.build()
        self.database.start(self.saved, self.offer_folder_import)
        self.store_settings()
        # prepare the flights of the database only once the window is shown (keeps the start quick)
        self.root.after(START_DELAY_MS, self.flight_cache.resume)

    # ---------------- tests ----------------
    def test_handles(self):
        """Widgets and functions that the GUI test drives (root._akku)."""
        settings_page, flight_page, logbook_page = self.settings_page, self.flight_page, self.logbook_page
        return dict(
            window=self, database=self.database, flight_cache=self.flight_cache, flight_area=self.flight_area,
            select_page=self.select_page, statistics_nb=self.statistics_notebook, flight_page=flight_page, db_panel=settings_page.db_panel, run=self.run_analysis,
            model_box=settings_page.model_box, model_bar=settings_page.model_bar, use_model=self.settings.use_model,
            folder_var=self.settings.folder, battery_hint=settings_page.battery_hint,
            chem_box=settings_page.chem_box, settings=self.settings, params=self.settings.fields,
            status=self.status, nb=self.notebook, tabs=self.tabs, lang_var=settings_page.lang_var,
            set_language=self.change_language, summary=self.statistics.summary, table=self.statistics.table,
            fbox=flight_page.flight_box, flight_var=flight_page.flight_var, view_var=flight_page.view_var,
            select_flight=flight_page.select_flight, redraw=flight_page.redraw, set_xlim=flight_page.set_xlim,
            goto_spike=flight_page.goto_spike, spike_var=flight_page.spike_var, details=flight_page.details,
            flight_builder=flight_page.builder, flight_canvas=flight_page.canvas,
            lb_page=logbook_page, lb_model=self.logbook_model, filter_state=self.filter_state,
            lb_filter=logbook_page.filter_bar, lb_groups=logbook_page.group_tree, lb_flights=logbook_page.flight_list,
            lb_totals=logbook_page.totals, lb_scope=logbook_page.scope, lb_missing=logbook_page.missing,
            lb_year=logbook_page.year_tree, lb_month=logbook_page.month_tree, lb_list=logbook_page.flight_list.tree,
            lb_sort=logbook_page.sorter, lb_state=logbook_page.state, lb_canvas=logbook_page.chart_canvas,
            lb_open_row=logbook_page.open_row, lb_only_annotated=logbook_page.only_annotated,
            lb_annotated_toggled=logbook_page._annotated_toggled, annotations_panel=self.flight_annotations,
            anomalies=self.anomalies, anomaly_settings=settings_page.anomaly_panel,
            fullscreen=self.charts.fullscreen, open_fullscreen=self.charts.open_fullscreen,
            open_chart=self.charts.open_chart, tab_canvas=self.statistics.chart_canvas,
            tab_builder=lambda key: (lambda: self.statistics.figure(key)), statistics=self.statistics,
            statistics_model=self.statistics_model, stats_filter=self.statistics.filter_bar)


def run_gui():
    """Creates the window (without starting the Tk main loop) and returns its Tk root."""
    window = MainWindow()
    window.start()
    return window.root


def main():
    """Starts the user interface."""
    run_gui().mainloop()
