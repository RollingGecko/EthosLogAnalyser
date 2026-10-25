# -*- coding: utf-8 -*-
"""GUI checks of notes and anomalies (called from test_gui.py, which owns the one window of the test session).

Uses the three example flights of the logbook check: writes a note, adds, acknowledges and deletes an own entry
on the single-flight page, checks the symbol and the filter in the logbook, and makes a rule stricter on
Data & settings so that the automatic anomalies are recalculated in the background.
"""

import time

from logbook_checks import _select_newest_flight


def _wait_until_recalculated(root):
    """Waits for the debounced recalculation of the anomalies and the background task."""
    h = root._akku
    deadline = time.time() + 60
    while (h["anomalies"].pending or h["database"].busy) and time.time() < deadline:
        root.update()
        time.sleep(0.02)
    root.update()
    assert not h["anomalies"].pending and not h["database"].busy


def _open_flight(root, h, number):
    lst = h["lb_list"]
    h["select_page"]("logbook")
    root.update()
    item = next(i for i in lst.get_children() if lst.item(i)["values"][0] == number)
    h["lb_open_row"](item)
    root.update()
    return h["lb_flights"].log_id_of(item)


def _row_of(h, log_id):
    lst, flights = h["lb_list"], h["lb_flights"]
    return next(i for i in lst.get_children() if flights.log_id_of(i) == log_id)


def check_annotations(root):
    h = root._akku
    _wait_until_recalculated(root)
    panel = h["annotations_panel"]
    log_id = _open_flight(root, h, 2)
    assert panel.log_id == log_id and panel.note_text() == ""
    assert panel.anomalies() == []                       # three flights: too few for the median rules
    assert panel.selected_text.get() == "Keine Auffälligkeiten für diesen Flug."
    _check_note(root, h, panel, log_id)
    _check_own_entry(root, h, panel, log_id)
    _check_rule_settings(root, h, panel)
    _select_newest_flight(root, h)


def _check_note(root, h, panel, log_id):
    panel.note.insert("1.0", "Querruder schwergängig?")
    h["select_page"]("logbook")                           # leaving the page saves the note
    root.update()
    lst = h["lb_list"]
    assert lst.set(_row_of(h, log_id), "note") == "✎"
    assert h["lb_flights"].hint_text(_row_of(h, log_id)) == [("note", "✎ Querruder schwergängig?")]
    h["lb_only_annotated"].set(True)                      # the checkbox "only with note or anomaly"
    h["lb_annotated_toggled"]()
    root.update()
    assert h["lb_flights"].log_ids() == [log_id]
    h["lb_only_annotated"].set(False)
    h["lb_annotated_toggled"]()
    root.update()
    assert len(lst.get_children()) == 3


def _check_own_entry(root, h, panel, log_id):
    _open_flight(root, h, 2)
    assert panel.note_text() == "Querruder schwergängig?"
    entry = panel.add_entry("Servo getauscht", "critical")
    assert [row for row in panel.tree.item(str(entry))["values"]] == ["Kritisch", "offen", "eigener Eintrag",
                                                                        "Servo getauscht"]
    root.update()
    assert h["lb_list"].set(_row_of(h, log_id), "note") == "✎ ‼"
    panel.toggle_acknowledged()                           # acknowledged: no open anomaly any more
    root.update()
    assert panel.tree.item(str(entry))["values"][1] == "quittiert"
    assert h["lb_list"].set(_row_of(h, log_id), "note") == "✎"
    panel.delete_selected()
    panel.note.delete("1.0", "end")
    panel.save_note()
    root.update()
    assert panel.anomalies() == [] and h["lb_list"].set(_row_of(h, log_id), "note") == ""


def _check_rule_settings(root, h, panel):
    """A stricter threshold finds receiver voltage dips in all three flights; the standard value finds none."""
    settings_panel = h["anomaly_settings"]
    settings_panel.thresholds["rx_voltage_dip"].set("0,1")         # decimal comma as typed by the user
    assert h["settings"].anomaly_rules.threshold("rx_voltage_dip") == 0.1
    _wait_until_recalculated(root)
    assert h["anomalies"].last_count == 3
    assert settings_panel.status.get() == "Zuletzt gefunden: 3 automatische Hinweise."
    assert [h["lb_list"].set(item, "note") for item in h["lb_list"].get_children()] == ["⚠"] * 3
    assert [anomaly.rule for anomaly in panel.anomalies()] == ["rx_voltage_dip"]
    settings_panel.enabled["rx_voltage_dip"].set(False)            # switched off: gone
    settings_panel._changed()
    _wait_until_recalculated(root)
    assert h["anomalies"].last_count == 0 and panel.anomalies() == []
    settings_panel.enabled["rx_voltage_dip"].set(True)
    settings_panel.thresholds["rx_voltage_dip"].set("10")
    _wait_until_recalculated(root)
    assert h["anomalies"].last_count == 0
