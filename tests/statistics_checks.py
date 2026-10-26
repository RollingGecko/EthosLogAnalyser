# -*- coding: utf-8 -*-
"""GUI checks of the statistics area (called from test_gui.py, which owns the one window of the test session).

The statistics show the flights of the database that pass the shared filter, one aircraft at a time, without any
folder analysis. These checks drive the filter bars of the statistics and of the logbook, the pages, the battery
settings per aircraft and the hint for several aircraft.
"""

import json
import time

from logbook_checks import choose, pick


def wait_for_statistics(root, state="ready"):
    """Waits until the statistics show the given state (the aircraft is prepared in the background)."""
    h = root._akku
    deadline = time.time() + 120
    while (h["statistics"].view is None or h["statistics"].view.state != state) and time.time() < deadline:
        root.update()
        time.sleep(0.02)
    root.update()
    assert h["statistics"].view.state == state, h["statistics"].view.state


def summary_lines(h, count):
    return h["summary"].get("1.0", f"{count + 1}.0").splitlines()


def check_statistics(root):
    """Statistics of the three example flights: shown without "Analyse", experimental notice first, battery hint
    on the first start, status line, pages drawn when chosen, filter shared with the logbook."""
    h = root._akku
    h["select_page"]("summary")
    wait_for_statistics(root)
    lines = summary_lines(h, 3)
    assert lines[0] == "Dieser Bereich ist noch experimentell: Werte und Auswertungen können sich ändern."
    # first start without any battery settings: the assumed LiPo is not a setting -> hint
    assert lines[1].startswith("Für das Modell Viper-Jet sind noch keine Akku-Einst")
    assert lines[2] == "ÜBERSICHT"
    assert h["battery_hint"].winfo_manager() == "grid"
    status = h["status"].get()
    assert status.startswith("Statistik  ·  3 von 3 Flügen der Datenbank  ·  Viper-Jet  ·  13.09.2026 – 18.10.2026")
    assert "Akku-Einstellungen für dieses Modell fehlen" in status
    assert h["statistics"].message.get() == ""
    _check_pages(root, h)
    _check_shared_filter(root, h)


def _check_pages(root, h):
    """Only the page that is shown is drawn; the others when they are chosen. The table lists the flights."""
    statistics = h["statistics"]
    assert "akku" in statistics.stale or h["tab_canvas"]("akku") is not None
    for key in ("akku", "belastung", "antrieb", "funk"):
        h["select_page"](key)
        root.update()
        canvas = h["tab_canvas"](key)
        assert canvas is not None and canvas.figure.axes and key not in statistics.stale
    h["select_page"]("table")
    root.update()
    assert len(h["table"].get_children()) == 3
    h["select_page"]("summary")
    root.update()


def _check_shared_filter(root, h):
    """The filter bar of the statistics and the one of the logbook show and change the same filter."""
    stats_filter, logbook_filter = h["stats_filter"], h["lb_filter"]
    assert [label for _value, label in stats_filter.year_box.options] == ["2026"]
    pick(root, stats_filter.month_box, 9)                   # September in the statistics ...
    assert logbook_filter.month_box.summary == "09"         # ... is the filter of the logbook too
    assert h["statistics"].view.n_flights == 2
    assert summary_lines(h, 4)[1] == "Filter: Monat 09"
    assert "2 von 3 Flügen" in h["status"].get() and "Filter: Monat 09" in h["status"].get()
    h["select_page"]("logbook")
    root.update()
    assert h["lb_scope"].get().startswith("2 von 3 Flügen der Datenbank")
    pick(root, logbook_filter.month_box, 10)                # October in the logbook ...
    assert stats_filter.month_box.summary == "10" and h["statistics"].view.n_flights == 1
    h["select_page"]("summary")
    root.update()
    assert "1 von 3 Flügen" in h["status"].get()
    pick(root, stats_filter.month_box, 1)                   # January: no flight
    assert h["statistics"].view.state == "no_match"
    assert h["statistics"].message.get() == "Kein Flug passt zum Filter."
    pick(root, stats_filter.month_box)                      # nothing chosen at all: 0 of 3 flights, no error
    assert h["statistics"].view.state == "no_match" and h["statistics"].view.n_flights == 0
    assert "0 von 3 Flügen" in h["status"].get() and "keine Monate" in h["status"].get()
    pick(root, stats_filter.month_box, 9, 10)               # two months: the flights of both
    assert h["statistics"].view.n_flights == 3 and summary_lines(h, 4)[1] == "Filter: Monate 09, 10"
    stats_filter.reset_button.invoke()
    root.update()
    assert logbook_filter.month_box.summary == "alle" and h["statistics"].view.n_flights == 3


def check_two_aircraft(root, settings):
    """The opened copy holds the Viper-Jet and a glider: the statistics ask for an aircraft; the glider has no
    battery data; battery settings are kept per aircraft with the hint for an aircraft without settings."""
    h = root._akku
    h["select_page"]("summary")
    root.update()
    wait_for_statistics(root, "several_aircraft")
    assert h["statistics"].message.get().startswith("Bitte im Filter ein Flugzeug wählen")
    assert "Bitte im Filter ein Flugzeug wählen" in h["summary"].get("1.0", "end")
    stats_filter = h["stats_filter"]
    assert [label for _value, label in stats_filter.aircraft_box.options] == ["Glider", "Viper-Jet"]
    pick(root, stats_filter.aircraft_box, "Glider")         # the glider: no battery data
    assert h["statistics"].view.state == "no_battery_data"
    assert "keine Spannungs- und Stromdaten" in h["statistics"].message.get()
    h["select_page"]("akku")
    root.update()
    assert any("keine Spannungs- und Stromdaten" in text.get_text() for text in h["tab_canvas"]("akku").figure.texts)
    pick(root, stats_filter.aircraft_box, "Viper-Jet")      # the Viper-Jet: its statistics as before
    wait_for_statistics(root)
    assert h["statistics"].view.n_flights == 3 and h["statistics"].message.get() == ""
    _check_battery_per_aircraft(root, h, settings)
    pick(root, stats_filter.aircraft_box, "Glider", "Viper-Jet")     # both ticked: the statistics ask for one again
    wait_for_statistics(root, "several_aircraft")
    assert h["statistics"].message.get().startswith("Bitte im Filter ein Flugzeug wählen")
    stats_filter.reset_button.invoke()
    h["select_page"]("summary")
    root.update()


def _check_battery_per_aircraft(root, h, settings):
    """Battery settings of Data & settings belong to the aircraft chosen there; one without settings shows the
    hint until the cell chemistry or a capacity is chosen."""
    box = h["model_box"]
    assert list(box["values"]) == ["Glider", "Viper-Jet"]
    h["params"]["chem"].set("Li-Ion")                       # Viper-Jet (chosen): cell chemistry and capacity
    h["chem_box"].event_generate("<<ComboboxSelected>>")
    h["params"]["nominal_mah"].set("9000")
    root.update()
    assert h["battery_hint"].winfo_manager() == ""
    choose(box, 0)                                          # the glider: no settings yet -> hint
    root.update()
    assert h["params"]["nominal_mah"].get() == "0" and h["battery_hint"].winfo_manager() == "grid"
    h["params"]["nominal_mah"].set("3000")
    root.update()
    assert h["battery_hint"].winfo_manager() == ""
    choose(box, 1)                                          # back: the Viper-Jet keeps its own settings
    root.update()
    assert h["params"]["nominal_mah"].get() == "9000" and h["params"]["chem"].get() == "Li-Ion"
    h["window"].store_settings()
    stored = json.loads(settings.read_text(encoding="utf-8"))
    assert stored["models"]["Glider"]["nominal_mah"] == "3000" and stored["model"] == "Viper-Jet"
    assert "folder" not in stored and "date_from" not in stored
    h["select_page"]("settings")                            # the user comes from Data & settings
    root.update()
    h["select_page"]("summary")
    root.update()
    assert not h["summary"].get("2.0", "3.0").startswith("Für das Modell")     # set up: no battery hint
    text = h["summary"].get("1.0", "end")
    assert "Akku: 13S Li-Ion" in text and "Nennkapazität 9000 mAh" in text
