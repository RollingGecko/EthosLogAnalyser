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
