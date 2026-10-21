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

    # do not store settings in the real home folder, capture message boxes
    monkeypatch.setattr(config, "SETTINGS_FILE", str(tmp_path / "settings.json"))
    errors = []
    monkeypatch.setattr("tkinter.messagebox.showerror", lambda *a, **k: errors.append(a))
    monkeypatch.setattr("tkinter.messagebox.showwarning", lambda *a, **k: errors.append(a))

    root = app.run_gui()
    try:
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
    finally:
        root.destroy()
