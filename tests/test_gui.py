# -*- coding: utf-8 -*-
"""GUI smoke test: build the window, analyse the example logs, draw every single-flight view.

Runs only where Tkinter and a display are available (in CI on Linux via xvfb).
"""

import os
import sys

import pytest

from helpers import EXAMPLES
from annotation_checks import check_annotations
from logbook_checks import check_empty_logbook, check_font_fit, check_import_report_fit, check_logbook
from recorder_checks import check_chart_position, check_chart_position_without_charts, check_recorder, check_recorder_without_attitude
from statistics_checks import check_statistics, check_two_aircraft

# In CI (environment variable REQUIRE_GUI_TEST) the test must run - skipping it there would be an error.
REQUIRED = bool(os.environ.get("REQUIRE_GUI_TEST"))
if REQUIRED:
    import tkinter as tk  # noqa: F401
else:
    tk = pytest.importorskip("tkinter")


def _display_available():
    if sys.platform.startswith("win") or sys.platform == "darwin":
        return True
    return bool(os.environ.get("DISPLAY"))


@pytest.mark.skipif(not REQUIRED and not _display_available(), reason="no display (DISPLAY) available")
def test_gui_analyses_example_logs(monkeypatch, tmp_path):
    import matplotlib
    matplotlib.use("TkAgg", force=True)
    from ethosloganalyser import config
    from ethosloganalyser.gui import app
    from ethosloganalyser.plots.flight import FLIGHT_VIEWS

    # do not store settings in the real home folder, start in German, capture message boxes
    settings = tmp_path / "settings.json"
    # a settings file of an older version: log folder and period are ignored without an error
    settings.write_text('{"language": "de", "folder": "/no/such/log/folder", "date_from": "20.09.2026", '
                        '"date_to": "kein Datum", "reserve_pct": "20"}', encoding="utf-8")
    monkeypatch.setattr(config, "SETTINGS_FILE", str(settings))
    monkeypatch.setattr(config, "DEFAULT_DATABASE_FILE", str(tmp_path / "db" / "flugbuch.db"))
    errors = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **k: errors.append(a))
    monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *a, **k: errors.append(a))

    root = app.run_gui()
    try:
        from ethosloganalyser import __version__
        from ethosloganalyser.buildinfo import window_title
        assert root.title() == window_title() and __version__ in root.title()     # version (and test marker)
        h = root._akku
        assert h["nb"].index("current") == h["nb"].index(h["tabs"]["logbook"])     # start page: logbook
        _check_empty_flight_page(root)
        check_empty_logbook(root)
        h["db_panel"].run_import([str(EXAMPLES)])            # logbook and single flight come from the database
        _wait_for_database(root)
        check_import_report_fit(root, h["db_panel"].report["tree"])      # nothing cut off in the report
        h["db_panel"].report["window"].destroy()
        _wait_for_flight(root)
        check_logbook(root, monkeypatch)                        # filled without any folder analysis
        check_annotations(root)                                 # notes and anomalies
        _wait_for_flight(root)
        check_statistics(root)                                  # statistics from the database, shared filter
        check_font_fit(root)                                    # tables at display scaling 100/125/150 %
        assert not errors, errors
        assert len(h["fbox"]["values"]) == 3
        for view in FLIGHT_VIEWS:
            h["view_var"].set(view)
            h["redraw"]()
            root.update()
        h["set_xlim"](10, 70)
        root.update()
        _check_single_flight_from_database(root)
        check_recorder(root)                                    # flight recorder tab of the single flight
        check_chart_position(root)                              # its position as a line in the charts (TW-059)
        _check_fullscreen(root)
        _check_whole_page_double_click(root)
        _check_language_switch(root, settings)
        _check_database(root, errors, settings, tmp_path, monkeypatch)
        check_two_aircraft(root, settings)                      # Viper-Jet and Glider in the opened copy
        check_recorder_without_attitude(root)                   # the glider has no attitude sensor
        check_chart_position_without_charts(root)               # ... and no charts: no line, no error
    finally:
        root.destroy()


def _check_language_switch(root, settings):
    """Switching the language rebuilds the window in the new language and keeps the result and selection."""
    import json
    from ethosloganalyser.i18n import get_language

    h = root._akku
    flight, view = h["flight_page"].current_key(), h["view_var"].get()
    h["select_page"]("flight")
    for code, database_status, scope, status_text, heading in [
            ("en", "Flight database  ·  3 flights, 1 aircraft", "3 of 3 flights of the database",
             "Statistics  ·  3 of 3 flights", "OVERVIEW"),
            ("es", "Base de datos de vuelos  ·  3 vuelos, 1 aeronaves", "3 de 3 vuelos de la base de datos",
             "Estadística  ·  3 de 3 vuelos", "VISTA GENERAL"),
            ("de", "Flug-Datenbank  ·  3 Flüge, 1 Flugzeuge", "3 von 3 Flügen der Datenbank",
             "Statistik  ·  3 von 3 Flügen", "ÜBERSICHT")]:
        h["set_language"](code)
        root.update()
        h = root._akku                                    # widgets were rebuilt
        assert get_language() == code
        assert h["status"].get().startswith(database_status)                    # single-flight area: the database
        assert h["lb_scope"].get() == scope                                     # the logbook is filled at once
        assert heading in h["summary"].get("1.0", "4.0").splitlines()[:3]   # after the notice and battery hint
        assert h["flight_page"].current_key() == flight                       # same flight selected
        assert h["view_var"].get() == view
        assert h["is_flight_open"]() and h["nb"].index("current") == h["nb"].index(h["tabs"]["logbook"])   # stays open
        assert json.loads(settings.read_text(encoding="utf-8"))["language"] == code    # remembered
        h["nb"].select(h["tabs"]["statistics"])                                 # statistics: flights of the filter
        root.update()
        assert status_text in h["status"].get()
        h["select_page"]("flight")
        root.update()


def _check_fullscreen(root):
    """Whole page and single charts open in a full-screen window with tooltip and toolbar; Esc closes it."""
    h = root._akku
    for builder, title in ((h["tab_builder"]("akku"), "Akku"), (h["flight_builder"], "Einzelflug")):
        win = h["open_fullscreen"](builder, title)
        root.update()
        assert len(win._fig.axes) > 1                       # the whole page
        _close(root, win)

    # double-click on "Peak C rate per flight" in the tab Load: exactly this chart, alone
    h["select_page"]("belastung")
    root.update()
    canvas = h["tab_canvas"]("belastung")
    ax = next(a for a in canvas.figure.axes if a.get_title(loc="left") == "Spitzen-C-Rate je Flug [C]")
    win = _double_click(root, canvas, ax)
    assert len(win._fig.axes) == 1
    (big,) = win._fig.axes
    assert big.get_title(loc="left") == "Spitzen-C-Rate je Flug [C]"
    assert big.get_xlabel() == "Flug Nr."
    assert any("Höchster Strom geteilt durch Kapazität" in t.get_text() for t in big.texts)
    assert "Spitzen-C-Rate je Flug [C]" in win.title()
    assert win._fig.canvas._hover is not None               # tooltip in the window
    _close(root, win)

    # right-click: context menu "Enlarge this chart" / "Enlarge whole page"
    import tkinter as tk_
    menus = []
    popup = tk_.Menu.tk_popup
    tk_.Menu.tk_popup = lambda self, *a: menus.append(self)
    try:
        from matplotlib.backend_bases import MouseEvent
        ax = canvas.figure.axes[0]
        x, y = ax.bbox.x0 + ax.bbox.width / 2, ax.bbox.y0 + ax.bbox.height / 2
        canvas.callbacks.process("button_press_event", MouseEvent("button_press_event", canvas, x, y, button=3))
    finally:
        tk_.Menu.tk_popup = popup
    assert len(menus) == 1
    menu = menus[0]
    assert [menu.entrycget(i, "label") for i in range(menu.index("end") + 1)] == [
        "Dieses Diagramm vergrößern", "Ganze Seite vergrößern"]
    menu.invoke(0)
    root.update()
    win = h["fullscreen"][-1]
    assert len(win._fig.axes) == 1 and win._fig.axes[0].get_title(loc="left") == ax.get_title(loc="left")
    _close(root, win)

    # single flight: double-click on the second chart opens only that chart, with the zoom of the tab
    # (attitude view: pitch angle with the elevator stick on a twin axis)
    from ethosloganalyser.plots.single import chart_group
    h["view_var"].set("attitude")
    h["redraw"]()
    canvas = h["flight_canvas"]
    canvas.draw()
    root.update()
    ax = canvas.figure.axes[1]
    xlim = canvas.figure.axes[0].get_xlim()
    n_axes = len(chart_group(canvas.figure, ax))
    win = _double_click(root, canvas, ax)
    assert len(win._fig.axes) == n_axes == 2
    big, stick = win._fig.axes
    assert stick.get_ylabel() == "%" and stick.get_ylim() == (-105, 105)
    assert big.get_title(loc="left") == ax.get_title(loc="left")
    assert big.get_xlim() == pytest.approx(xlim)
    assert big.get_xlabel() == "Zeit seit Motorstart [min:s]"
    buttons = [w for w in _widgets(win) if w.winfo_class() == "TButton"]
    whole = [b for b in buttons if b.cget("text") == "Ganzer Flug"]
    assert whole, "no button 'Ganzer Flug' in the single-flight window"
    whole[0].invoke()
    root.update()
    t = win._fig._t
    assert big.get_xlim() == pytest.approx((t[0], t[-1]))
    _close(root, win)


def _check_whole_page_double_click(root):
    """In the window "Enlarge whole page" a double-click (or right-click) on a chart enlarges that chart alone,
    for the overview tabs and the single-flight page; a zoomed time window of the page is kept."""
    import tkinter as tk_
    from matplotlib.backend_bases import MouseEvent
    h = root._akku
    title = "Spitzen-C-Rate je Flug [C]"
    page = h["open_fullscreen"](h["tab_builder"]("belastung"), "Belastung")
    root.update()
    canvas = page._fig.canvas
    buttons = [w.cget("text") for w in _widgets(page) if w.winfo_class() == "TButton"]
    assert "Ganze Seite vergrößern" not in buttons             # already the whole page
    ax = next(a for a in page._fig.axes if a.get_title(loc="left") == title)
    win = _double_click(root, canvas, ax)
    assert len(win._fig.axes) == 1 and win._fig.axes[0].get_title(loc="left") == title
    assert title in win.title()
    _close_last(root, win)

    # right-click: only "Enlarge this chart" (the page is already enlarged)
    menus = []
    popup = tk_.Menu.tk_popup
    tk_.Menu.tk_popup = lambda self, *a: menus.append(self)
    try:
        canvas.callbacks.process("button_press_event", MouseEvent(
            "button_press_event", canvas, ax.bbox.x0 + ax.bbox.width / 2, ax.bbox.y0 + ax.bbox.height / 2, button=3))
    finally:
        tk_.Menu.tk_popup = popup
    menu = menus[-1]
    assert [menu.entrycget(i, "label") for i in range(menu.index("end") + 1)] == ["Dieses Diagramm vergrößern"]
    menu.invoke(0)
    root.update()
    win = h["fullscreen"][-1]
    assert win is not page and win._fig.axes[0].get_title(loc="left") == title
    _close_last(root, win)
    _close(root, page)

    # single flight: zoom the time window in the page window, then double-click the second chart
    page = h["open_fullscreen"](h["flight_builder"], "Einzelflug", flight=True)
    root.update()
    page._fig.axes[0].set_xlim(20, 50)
    ax = page._fig.axes[1]
    win = _double_click(root, page._fig.canvas, ax)
    assert win._fig.axes[0].get_title(loc="left") == ax.get_title(loc="left")
    assert win._fig.axes[0].get_xlim() == pytest.approx((20, 50))
    assert any(w.winfo_class() == "TButton" and w.cget("text") == "Ganzer Flug" for w in _widgets(win))
    _close_last(root, win)
    _close(root, page)


def _close_last(root, win):
    """Closes a window opened from another full-screen window; the other one stays open."""
    h = root._akku
    n = len(h["fullscreen"])
    win.event_generate("<Escape>", when="tail")
    root.update()
    assert len(h["fullscreen"]) == n - 1 and win not in h["fullscreen"]


def _widgets(w):
    for c in w.winfo_children():
        yield c
        yield from _widgets(c)


def _double_click(root, canvas, ax):
    """Double-click into the middle of ax (as matplotlib reports it) and return the full-screen window."""
    from matplotlib.backend_bases import MouseEvent
    h = root._akku
    canvas.draw()
    x, y = ax.bbox.x0 + ax.bbox.width / 2, ax.bbox.y0 + ax.bbox.height / 2
    n = len(h["fullscreen"])
    ev = MouseEvent("button_press_event", canvas, x, y, button=1, dblclick=True)
    canvas.callbacks.process("button_press_event", ev)
    root.update()
    assert len(h["fullscreen"]) == n + 1, "double-click did not open a window"
    win = h["fullscreen"][-1]
    assert win.winfo_exists()
    assert [w for w in win.winfo_children() if w.winfo_class() == "Canvas"], "no chart in the full-screen window"
    return win


def _close(root, win):
    h = root._akku
    win.event_generate("<Escape>", when="tail")
    root.update()
    assert h["fullscreen"] == []


def _wait_for_database(root):
    import time
    deadline = time.time() + 120
    while root._akku["database"].busy and time.time() < deadline:
        root.update()
        time.sleep(0.02)
    root.update()
    assert not root._akku["database"].busy


def _wait_for_flight(root):
    """Waits until the single-flight page shows a flight (its aircraft is prepared in the background)."""
    import time
    deadline = time.time() + 120
    while not root._akku["flight_page"].axes and time.time() < deadline:
        root.update()
        time.sleep(0.02)
    assert root._akku["flight_page"].axes


def _check_empty_flight_page(root):
    """Without flights in the database the single-flight page explains how to import logs."""
    h = root._akku
    assert not h["fbox"]["values"]
    texts = [t.get_text() for t in h["flight_canvas"].figure.texts]
    assert any("Noch keine Flüge in der Datenbank" in t for t in texts)


def _check_single_flight_from_database(root):
    """Single flight: flights of the database with date and aircraft, views, back to the logbook, prev/next."""
    from ethosloganalyser.plots.flight import FLIGHT_VIEWS
    h = root._akku
    page = h["flight_page"]
    labels = list(h["fbox"]["values"])
    assert len(labels) == 3 and all(" | Viper-Jet | " in text for text in labels)
    assert h["flight_var"].get() == labels[-1]                     # newest flight
    assert [view for view, button in page.view_buttons.items() if button.winfo_manager()] == FLIGHT_VIEWS
    page.step_flight(-1)
    root.update()
    assert h["flight_var"].get() == labels[-2] and page.axes
    page.step_flight(1)
    h["select_page"]("flight")
    back = next(w for w in _widgets(page.selection_bar) if w.winfo_class() == "TButton")
    assert back.cget("text") == "‹ Logbuch"
    back.invoke()
    root.update()
    assert h["nb"].index("current") == h["nb"].index(h["tabs"]["logbook"])


def _check_database(root, errors, settings, tmp_path, monkeypatch):
    """Section Database: default database at start, duplicates, a flight without battery data, language switch,
    save as, empty, open."""
    import json
    import shutil
    from helpers import write_glider_log

    h = root._akku
    database, panel = h["database"], h["db_panel"]
    assert database.path == str(tmp_path / "db" / "flugbuch.db")      # created at the first start
    assert json.loads(settings.read_text(encoding="utf-8"))["database"] == database.path
    assert panel.path.get() == database.path
    assert database.stats().flight_count == 3                          # imported at the start of the test
    assert panel.stats.get().startswith("3 Logs: 3 Flüge, 0 ohne Flug")

    # the same folder again, and a renamed copy: everything is a duplicate
    copy = tmp_path / "renamed"
    copy.mkdir()
    shutil.copy(next(EXAMPLES.glob("*.csv")), copy / "Copy-2030-01-01-10-00-00.csv")
    panel.run_import([str(EXAMPLES), str(copy)])
    assert database.busy                                               # runs in the background
    _wait_for_database(root)
    rows = [panel.report["tree"].item(item, "values")
            for item in panel.report["tree"].get_children()]
    assert [row[1] for row in rows] == ["doppelt"] * 4
    assert database.stats().log_count == 3
    panel.report["window"].destroy()

    # a glider without motor and battery sensors: listed, no views, a hint instead of the charts
    glider = tmp_path / "glider"
    glider.mkdir()
    write_glider_log(glider, "Glider-2030-02-01-12-00-00.csv", airborne_s=600, start="2030-02-01 12:00:00")
    panel.run_import([str(glider)])
    _wait_for_database(root)
    panel.report["window"].destroy()
    page = root._akku["flight_page"]
    labels = list(h["fbox"]["values"])
    assert len(labels) == 4 and " | Glider | " in labels[-1]
    h["flight_var"].set(labels[-1])
    h["select_flight"]()
    root.update()
    assert [view for view, button in page.view_buttons.items() if button.winfo_manager()] == []
    texts = [t.get_text() for t in h["flight_canvas"].figure.texts]
    assert any("keine Spannungs- und Stromdaten" in t for t in texts)
    h["flight_var"].set(labels[0])                                  # back to a Viper flight
    h["select_flight"]()
    _wait_for_flight(root)

    # the database stays open across a language switch, the flight stays selected
    selected = h["flight_var"].get()
    h["set_language"]("en")
    root.update()
    h = root._akku
    panel = h["db_panel"]
    assert panel.stats.get().startswith("4 logs: 4 flights")
    assert h["flight_var"].get().split(" | ")[1:] == selected.split(" | ")[1:]
    h["set_language"]("de")
    root.update()
    h = root._akku
    panel = h["db_panel"]

    # save as: a copy, the open database stays
    copy_path = tmp_path / "copy.db"
    monkeypatch.setattr("tkinter.filedialog.asksaveasfilename", lambda **k: str(copy_path))
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *a, **k: None)
    panel.actions["save_as"].invoke()
    assert copy_path.exists() and database.path == str(tmp_path / "db" / "flugbuch.db")

    # empty (after the question): the single-flight page explains the import again
    monkeypatch.setattr("tkinter.messagebox.askyesno", lambda *a, **k: True)
    panel.actions["clear"].invoke()
    root.update()
    assert database.stats().log_count == 0
    assert panel.stats.get().startswith("0 Logs")
    _check_empty_flight_page(root)
    check_empty_logbook(root)

    # open the copy: it still has the flights. Its prepared values for the statistics are missing (as after the
    # update from schema version 2): they are worked out once in the background, with progress
    import sqlite3
    from ethosloganalyser.db import flight_preparation
    copy_connection = sqlite3.connect(str(copy_path))
    copy_connection.execute("DELETE FROM flight_preparation")
    copy_connection.commit()
    copy_connection.close()
    progress_texts = []

    def record_progress():
        if database.progress is not None:
            progress_texts.append(database.progress[2])

    database.add_listener(record_progress)
    monkeypatch.setattr("tkinter.filedialog.askopenfilename", lambda **k: str(copy_path))
    panel.actions["open"].invoke()
    _wait_for_database(root)
    database.remove_listener(record_progress)
    assert "Auswertungswerte für die Statistik werden vorbereitet" in progress_texts
    assert flight_preparation.outdated_log_ids(database.database.connection) == []
    assert database.path == str(copy_path) and database.stats().flight_count == 4
    assert len(h["fbox"]["values"]) == 4
    assert h["lb_scope"].get() == "4 von 4 Flügen der Datenbank"       # the logbook shows the opened database
    assert not errors, errors
