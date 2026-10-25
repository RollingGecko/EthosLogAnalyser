# -*- coding: utf-8 -*-
"""GUI checks of the logbook page (called from test_gui.py, which owns the one window of the test session).

Everything here drives the widgets the way the user does: choosing in the combo boxes, clicking in the tree and
on the flight switch, double-clicking a row.
"""


def widgets(parent):
    """All widgets below parent."""
    found = []
    for child in parent.winfo_children():
        found.append(child)
        found.extend(widgets(child))
    return found


def choose(box, index):
    """Chooses an entry of a combo box like the user does."""
    box.current(index)
    box.event_generate("<<ComboboxSelected>>")


def enter_date(root, entry, variable, text):
    """Types a date into a date field and leaves the field."""
    variable.set(text)
    entry.event_generate("<FocusOut>")
    root.update()


def list_column(tree, column):
    """The texts of one column of a Treeview, in the order shown."""
    return [tree.set(item, column) for item in tree.get_children()]


def check_empty_logbook(root):
    """Without flights in the database the logbook explains how to import logs."""
    h = root._akku
    root.update()
    assert h["lb_scope"].get().startswith("Noch keine Flüge in der Datenbank")
    assert h["lb_totals"]["flights"].get() == "0"
    assert not h["lb_list"].get_children()


def check_logbook(root, monkeypatch):
    """Logbook from the database (three Viper-Jet flights): scope, totals, tables, flight list, sorting, chart,
    status line, the tree with both groupings, the filter, double-click, the flight switch."""
    h = root._akku
    nb, tabs = h["nb"], h["tabs"]
    assert nb.index(tabs["logbook"]) == 0                               # first area (start page)
    nb.select(tabs["logbook"])
    root.update()
    assert h["lb_scope"].get() == "3 von 3 Flügen der Datenbank"       # no folder analysis needed
    assert h["lb_totals"]["flights"].get().startswith("3  (")
    assert h["lb_missing"].get() == ""
    assert h["status"].get() == "Flug-Datenbank  ·  3 Flüge, 1 Flugzeuge  ·  13.09.2026 – 18.10.2026"
    years = [h["lb_year"].item(i)["values"] for i in h["lb_year"].get_children()]
    assert len(years) == 1 and years[0][1] == 3
    _check_flight_list(root, h)
    _check_tree(root, h)
    _check_filter(root, h)
    _check_open_flight(root, h)
    _check_flight_switch(root, h, monkeypatch)
    _select_newest_flight(root, h)


def _select_newest_flight(root, h):
    """Leaves the single-flight page on the newest flight again, as after the import."""
    lst = h["lb_list"]
    newest = next(i for i in lst.get_children() if lst.item(i)["values"][0] == 3)
    h["lb_open_row"](newest)
    root.update()
    h["nb"].select(h["tabs"]["logbook"])
    root.update()


def _check_flight_list(root, h):
    lst = h["lb_list"]
    first_col = lambda: [lst.item(i)["values"][0] for i in lst.get_children()]
    assert first_col() == [1, 2, 3]
    assert set(list_column(lst, "aircraft")) == {"Viper-Jet"} and set(list_column(lst, "is_flight")) == {"☑"}
    book = h["lb_state"]["book"]
    h["lb_sort"]["sort"]("dauer_s")                                   # shortest first
    durations = [book.flights.set_index("Flug").loc[no, "dauer_s"] for no in first_col()]
    assert durations == sorted(durations)
    h["lb_sort"]["sort"]("dauer_s")                                   # second click: longest first
    assert first_col()[0] == book.longest["Flug"]
    assert lst.heading("dauer_s")["text"].endswith("▼")
    canvas = h["lb_canvas"]()
    assert canvas is not None and len(canvas.figure.axes) == 2
    h["lb_sort"]["sort"]("number")                                    # by number, ascending
    assert first_col() == [1, 2, 3]


def _check_tree(root, h):
    """Both groupings, and a click on a row filters the flight list but not the totals."""
    tree, lst = h["lb_groups"].tree, h["lb_list"]
    top = tree.get_children()
    assert [tree.item(i, "text") for i in top] == ["2026", "Summe"]
    months = tree.get_children(top[0])
    assert [tree.item(i, "text") for i in months] == ["09/2026", "10/2026"]
    assert [int(tree.set(i, "#1")) for i in months] == [2, 1] and int(tree.set(top[1], "#1")) == 3
    h["lb_groups"].select_item(months[1])                             # a click on October
    root.update()
    assert len(lst.get_children()) == 1 and h["lb_totals"]["flights"].get().startswith("3  (")
    h["lb_groups"].select_item(top[1])                                # the sum row: everything again
    root.update()
    assert len(lst.get_children()) == 3

    by_aircraft = next(w for w in widgets(h["lb_groups"].frame) if w.winfo_class() == "TRadiobutton"
                       and w.cget("text").startswith("Flugzeug"))
    by_aircraft.invoke()
    root.update()
    top = tree.get_children()
    assert [tree.item(i, "text") for i in top] == ["Viper-Jet", "Summe"]
    assert [tree.item(i, "text") for i in tree.get_children(top[0])] == ["2026"]
    assert h["lb_model"].group_by == "aircraft"
    next(w for w in widgets(h["lb_groups"].frame) if w.winfo_class() == "TRadiobutton"
         and w.cget("text").startswith("Zeit")).invoke()
    root.update()
    assert [tree.item(i, "text") for i in tree.get_children()] == ["2026", "Summe"]


def _check_filter(root, h):
    """Aircraft, year, month and date fields change what the page shows; a second bar follows the first one."""
    from tkinter import ttk
    from ethosloganalyser.gui.flight_filter import FilterBar

    bar, state = h["lb_filter"], h["filter_state"]
    assert list(bar.aircraft_box["values"]) == ["alle", "Viper-Jet"] and list(bar.year_box["values"]) == ["alle", "2026"]
    second = FilterBar(ttk.Frame(root), state)                       # e.g. the filter on the statistics page
    choose(bar.month_box, 9)                                          # September
    root.update()
    assert h["lb_scope"].get() == "2 von 3 Flügen der Datenbank  ·  Filter aktiv"
    assert h["lb_totals"]["flights"].get().startswith("2  (") and len(h["lb_list"].get_children()) == 2
    assert second.month_var.get() == "09" and state.value.month == 9      # one setting for every bar
    choose(second.year_box, 1)                                        # changed in the other bar
    root.update()
    assert bar.year_var.get() == "2026" and state.value.year == 2026
    bar.reset_button.invoke()
    root.update()
    assert bar.month_var.get() == bar.year_var.get() == "alle" and second.month_var.get() == "alle"
    assert h["lb_scope"].get() == "3 von 3 Flügen der Datenbank"

    choose(bar.aircraft_box, 1)
    root.update()
    assert state.value.aircraft == "Viper-Jet" and h["lb_totals"]["flights"].get().startswith("3  (")
    bar.reset_button.invoke()
    enter_date(root, bar.from_entry, bar.from_var, "20.09.2026")      # flights of 27.09. and 18.10.
    assert h["lb_totals"]["flights"].get().startswith("2  (") and len(h["lb_list"].get_children()) == 2
    enter_date(root, bar.to_entry, bar.to_var, "27.09.2026")           # the end day counts as well
    assert h["lb_totals"]["flights"].get().startswith("1  (") and len(h["lb_list"].get_children()) == 1
    enter_date(root, bar.to_entry, bar.to_var, "kein Datum")           # not a date: marked, filter unchanged
    assert str(bar.to_entry.cget("foreground")) == "#b00020" and state.value.date_to.isoformat() == "2026-09-27"
    enter_date(root, bar.to_entry, bar.to_var, "")                      # empty: no limit
    assert state.value.date_to is None and h["lb_totals"]["flights"].get().startswith("2  (")
    bar.reset_button.invoke()
    root.update()
    assert bar.from_var.get() == "" and h["lb_scope"].get() == "3 von 3 Flügen der Datenbank"

    second.frame.master.destroy()                                      # a bar that is gone is not told any more
    state.set(year=2026)
    state.set(year=None)
    root.update()


def _check_open_flight(root, h):
    """Double-click on a flight: that flight on the single-flight page."""
    nb, tabs, lst = h["nb"], h["tabs"], h["lb_list"]
    nb.select(tabs["logbook"])
    item = next(i for i in lst.get_children() if lst.item(i)["values"][0] == 2)
    h["lb_open_row"](item)                                           # what a double-click on the row does
    root.update()
    assert nb.index("current") == nb.index(tabs["flight"])
    row = h["lb_model"].table.set_index("Flug").loc[2]
    assert h["flight_var"].get().startswith(f"{row['datum']:%d.%m.%Y %H:%M} | Viper-Jet")
    assert h["details"].get("1.0", "2.0").startswith("Flug 2 – ")
    assert h["status"].get().startswith("Flug-Datenbank  ·  3 Flüge")     # the database state on both areas
    nb.select(tabs["logbook"])
    root.update()


def _check_flight_switch(root, h, monkeypatch):
    """The ☑/☐ switch: a log is no flight any more (totals, single-flight list, status), is shown with the
    non-flights switch, and the same switch gives it back."""
    shown = []
    monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *a, **k: shown.append(a))
    lst, flights = h["lb_list"], h["lb_flights"]
    root.update()
    item = lst.get_children()[0]
    log_id = flights.log_id_of(item)

    flights.switch_row(item, event_time=1000)                          # a click on the ☑ of the first flight
    root.update()
    assert h["lb_scope"].get() == "2 von 2 Flügen der Datenbank"
    assert h["lb_totals"]["flights"].get().startswith("2  (") and len(lst.get_children()) == 2
    assert log_id not in flights.log_ids()
    assert len(h["fbox"]["values"]) == 2                               # the single-flight list follows
    assert h["status"].get() == "Flug-Datenbank  ·  2 Flüge, 1 Flugzeuge  ·  27.09.2026 – 18.10.2026  ·  1 Logs ohne Flug"

    h["lb_page"].non_flights_button.invoke()                            # show the non-flights
    root.update()
    assert len(lst.get_children()) == 3 and h["lb_totals"]["flights"].get().startswith("2  (")
    non_flight = next(i for i in lst.get_children() if flights.log_id_of(i) == log_id)
    assert lst.set(non_flight, "is_flight") == "☐" and lst.set(non_flight, "number") == "–"
    h["lb_open_row"](non_flight)                                        # no single flight for a non-flight: a hint
    assert shown and "nicht als Flug gezählt" in shown[-1][1] and h["nb"].index("current") == 0

    flights.switch_row(non_flight, event_time=2000)                    # switch it back ...
    root.update()
    assert h["lb_totals"]["flights"].get().startswith("3  (") and len(h["fbox"]["values"]) == 3
    again = next(i for i in lst.get_children() if flights.log_id_of(i) == log_id)
    assert lst.set(again, "is_flight") == "☑"
    flights.switch_row(again, event_time=2200)                         # the second click of a double-click is ignored
    root.update()
    assert h["lb_totals"]["flights"].get().startswith("3  (")
    flights.switch_row(again, event_time=5000)                         # a later click switches it off ...
    root.update()
    assert h["lb_totals"]["flights"].get().startswith("2  (") and len(lst.get_children()) == 3
    flights.switch_row(next(i for i in lst.get_children() if flights.log_id_of(i) == log_id), event_time=9000)
    root.update()
    assert h["lb_totals"]["flights"].get().startswith("3  (")          # ... and on again: as detected

    h["lb_page"].non_flights_button.invoke()
    root.update()
    assert len(lst.get_children()) == 3 and h["lb_model"].show_non_flights is False
