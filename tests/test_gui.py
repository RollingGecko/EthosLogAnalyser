# -*- coding: utf-8 -*-
"""GUI smoke test: build the window, analyse the example logs, draw every single-flight view.

Runs only where Tkinter and a display are available (in CI on Linux via xvfb).
"""

import os
import sys

import pytest

from helpers import EXAMPLES

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
    settings.write_text('{"language": "de"}', encoding="utf-8")
    monkeypatch.setattr(config, "SETTINGS_FILE", str(settings))
    errors = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **k: errors.append(a))
    monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *a, **k: errors.append(a))

    root = app.run_gui()
    try:
        from ethosloganalyser import __version__
        from ethosloganalyser.buildinfo import window_title
        assert root.title() == window_title() and __version__ in root.title()     # version (and test marker)
        h = root._akku
        h["folder_var"].set(str(EXAMPLES))
        h["run"]()
        root.update()
        assert not errors, errors
        assert "3 Flüge ausgewertet" in h["status"].get()       # status bar text (German UI)
        # first start without any battery settings: the assumed LiPo is not a setting -> hint
        assert h["battery_hint"].winfo_manager() == "grid"
        assert "Akku-Einstellungen für dieses Modell fehlen" in h["status"].get()
        assert h["summary"].get("1.0", "2.0").startswith("Für das Modell Viper-Jet sind noch keine Akku-Einst")
        assert len(h["fbox"]["values"]) == 3
        for view in FLIGHT_VIEWS:
            h["view_var"].set(view)
            h["redraw"]()
            root.update()
        h["set_xlim"](10, 70)
        root.update()
        _check_fullscreen(root)
        _check_whole_page_double_click(root)
        _check_language_switch(root, settings)
        _check_period_filter(root, errors)
        _check_two_models(root, errors, settings, tmp_path)
    finally:
        root.destroy()


def _check_language_switch(root, settings):
    """Switching the language rebuilds the window in the new language and keeps the result and selection."""
    import json
    from ethosloganalyser.i18n import get_language

    h = root._akku
    flight, view = h["flight_var"].get(), h["view_var"].get()
    h["nb"].select(h["tabs"]["flight"])
    for code, status_text, heading in [("en", "3 flights analysed", "OVERVIEW"),
                                       ("es", "3 vuelos analizados", "VISTA GENERAL"),
                                       ("de", "3 Flüge ausgewertet", "ÜBERSICHT")]:
        h["set_language"](code)
        root.update()
        h = root._akku                                    # widgets were rebuilt
        assert get_language() == code
        assert status_text in h["status"].get()
        assert heading in h["summary"].get("1.0", "3.0").splitlines()[:2]   # after the battery hint, if any
        assert h["flight_var"].get().split("|")[0] == flight.split("|")[0]     # same flight selected
        assert h["view_var"].get() == view
        assert h["nb"].index("current") == h["nb"].index(h["tabs"]["flight"])
        assert json.loads(settings.read_text(encoding="utf-8"))["language"] == code    # remembered


def _check_period_filter(root, errors):
    """The period fields limit the analysis to the flights in that period; invalid input is rejected."""
    h = root._akku
    h["params"]["date_from"].set("20.09.2026")
    h["run"]()
    root.update()
    h = root._akku
    assert not errors, errors
    assert "2 Flüge ausgewertet" in h["status"].get()
    assert "Zeitraum-Filter: 20.09.2026 – …; 1 Dateien außerhalb nicht ausgewertet" in h["summary"].get("1.0", "end")
    h["params"]["date_from"].set("kein Datum")
    h["run"]()
    root.update()
    assert errors and "Datum" in errors[-1][1]
    errors.clear()
    h["params"]["date_from"].set("")


def _check_two_models(root, errors, settings, tmp_path):
    """A folder with two models: selector visible, status names the model, battery settings kept per model."""
    import json
    import shutil
    h = root._akku
    assert h["model_bar"].winfo_manager() == ""                       # one model so far: no selector
    d = tmp_path / "two"
    d.mkdir()
    files = sorted(EXAMPLES.glob("*.csv"))
    for f in files:
        shutil.copy(f, d / f.name)
    for f, stamp in zip(files[:2], ("2025-06-01-10-00-00", "2025-06-01-11-00-00")):
        shutil.copy(f, d / f"Edge-540-{stamp}.csv")
    h["params"]["nominal_mah"].set("9000")                          # settings before models existed ...
    h["folder_var"].set(str(d))
    h["run"]()
    root.update()
    h = root._akku
    assert not errors, errors
    assert h["model_bar"].winfo_manager() == "grid"
    assert h["model_box"].get() == "Viper-Jet (3 Logs)"                   # newest model by default
    assert "Modell Viper-Jet" in h["status"].get() and "3 Flüge ausgewertet" in h["status"].get()
    assert "Modell: Viper-Jet – weitere Modelle im Ordner (getrennt ausgewertet): Edge-540" in \
        h["summary"].get("1.0", "end")
    assert h["params"]["nominal_mah"].get() == "9000"               # ... stay with the first model

    h["model_box"].set("Edge-540 (2 Logs)")                               # switch the model
    h["model_box"].event_generate("<<ComboboxSelected>>")
    for _ in range(5):
        root.update()
    h = root._akku
    assert "Modell Edge-540" in h["status"].get() and "2 Flüge ausgewertet" in h["status"].get()
    assert h["params"]["nominal_mah"].get() == "0"                  # new model: default battery settings
    _check_battery_hint(root, settings)
    h["params"]["nominal_mah"].set("2200")
    h["params"]["chem"].set("LiPo")
    h["run"]()
    root.update()
    stored = json.loads(settings.read_text(encoding="utf-8"))
    assert stored["models"]["Edge-540"]["nominal_mah"] == "2200"
    assert "unset" not in stored["models"]["Edge-540"]
    assert stored["models"]["Viper-Jet"]["nominal_mah"] == "9000"
    assert stored["model"] == "Edge-540"

    h["use_model"]("Viper-Jet")                                      # back: its own settings again
    assert h["params"]["nominal_mah"].get() == "9000"
    assert not h["state"]["battery_unset"]                           # set-up model: no hint
    h["folder_var"].set(str(EXAMPLES))
    h["run"]()
    root.update()
    h = root._akku
    assert h["model_bar"].winfo_manager() == ""
    assert "Modell" not in h["status"].get()                         # one model: status as before


def _check_battery_hint(root, settings):
    """A model without stored battery settings shows a hint (settings tab, status line, summary) until the user
    chooses the cell chemistry or enters a capacity; the hint is remembered until then."""
    import json
    h = root._akku
    hint = "Für das Modell Edge-540 sind noch keine Akku-Einstellungen gespeichert"
    assert h["battery_hint"].winfo_manager() == "grid"
    assert "Akku-Einstellungen für dieses Modell fehlen" in h["status"].get()
    assert h["summary"].get("1.0", "2.0").startswith(hint)
    stored = json.loads(settings.read_text(encoding="utf-8"))
    assert stored["models"]["Edge-540"]["unset"] is True              # kept across a restart
    assert "unset" not in stored["models"]["Viper-Jet"]

    h["chem_box"].event_generate("<<ComboboxSelected>>")            # cell chemistry chosen (even if LiPo)
    root.update()
    assert h["battery_hint"].winfo_manager() == ""
    assert "Akku-Einstellungen" not in h["status"].get() and "Modell Edge-540" in h["status"].get()
    assert hint not in h["summary"].get("1.0", "end")

    h["state"]["battery_unset"] = True                               # again, now with the capacity
    h["battery_hint"].grid()
    h["params"]["nominal_mah"].set("abc")                            # no number: hint stays
    assert h["state"]["battery_unset"]
    h["params"]["nominal_mah"].set("0")
    assert h["state"]["battery_unset"]


def test_gui_battery_hint_not_for_old_settings(monkeypatch, tmp_path):
    """Battery settings from before models existed belong to the first model: no hint."""
    if not REQUIRED and not _display_available():
        pytest.skip("no display (DISPLAY) available")
    import matplotlib
    matplotlib.use("TkAgg", force=True)
    from ethosloganalyser import config
    from ethosloganalyser.gui import app

    settings = tmp_path / "settings.json"
    settings.write_text('{"language": "de", "chem": "Li-Ion", "cells": "13", "nominal_mah": "9000", "folder": "%s"}'
                        % str(EXAMPLES).replace("\\", "/"), encoding="utf-8")
    monkeypatch.setattr(config, "SETTINGS_FILE", str(settings))
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **k: None)
    root = app.run_gui()
    try:
        h = root._akku
        h["run"]()
        root.update()
        assert "3 Flüge ausgewertet" in h["status"].get()
        assert h["battery_hint"].winfo_manager() == ""
        assert "Akku-Einstellungen" not in h["status"].get()
        assert not h["summary"].get("1.0", "2.0").startswith("Für das Modell")
    finally:
        root.destroy()


def _check_fullscreen(root):
    """Whole page and single charts open in a full-screen window with tooltip and toolbar; Esc closes it."""
    h = root._akku
    for builder, title in ((h["tab_builder"]("akku"), "Akku"), (h["flight_builder"], "Einzelflug")):
        win = h["open_fullscreen"](builder, title)
        root.update()
        assert len(win._fig.axes) > 1                       # the whole page
        _close(root, win)

    # double-click on "Peak C rate per flight" in the tab Load: exactly this chart, alone
    h["nb"].select(h["tabs"]["belastung"])
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
