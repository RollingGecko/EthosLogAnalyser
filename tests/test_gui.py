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
        assert len(h["fbox"]["values"]) == 3
        for view in FLIGHT_VIEWS:
            h["view_var"].set(view)
            h["redraw"]()
            root.update()
        h["set_xlim"](10, 70)
        root.update()
        _check_fullscreen(root)
        _check_language_switch(root, settings)
        _check_period_filter(root, errors)
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
        assert h["summary"].get("1.0", "2.0").strip() == heading
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
