# -*- coding: utf-8 -*-
"""Rauchtest der Oberfläche: Fenster aufbauen, Beispiel-Logs auswerten, alle Einzelflug-Ansichten zeichnen.

Läuft nur, wenn Tkinter und ein Bildschirm vorhanden sind (in der CI unter Linux per xvfb).
"""

import os
import sys

import pytest

from helpers import EXAMPLES

# In der CI (Umgebungsvariable REQUIRE_GUI_TEST) muss der Test laufen - dort wäre ein Überspringen ein Fehler.
REQUIRED = bool(os.environ.get("REQUIRE_GUI_TEST"))
if REQUIRED:
    import tkinter as tk  # noqa: F401
else:
    tk = pytest.importorskip("tkinter")


def _display_available():
    if sys.platform.startswith("win") or sys.platform == "darwin":
        return True
    return bool(os.environ.get("DISPLAY"))


@pytest.mark.skipif(not REQUIRED and not _display_available(), reason="kein Bildschirm (DISPLAY) vorhanden")
def test_oberflaeche_wertet_beispiel_logs_aus(monkeypatch, tmp_path):
    import matplotlib
    matplotlib.use("TkAgg", force=True)
    from ethosloganalyser import config
    from ethosloganalyser.gui import app
    from ethosloganalyser.plots.flight import FLIGHT_VIEWS

    # Einstellungen nicht im echten Benutzerordner speichern, Meldungsfenster abfangen
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
        assert "3 Flüge ausgewertet" in h["status"].get()
        assert len(h["fbox"]["values"]) == 3
        for view in FLIGHT_VIEWS:
            h["view_var"].set(view)
            h["redraw"]()
            root.update()
        h["set_xlim"](10, 70)
        root.update()
    finally:
        root.destroy()
