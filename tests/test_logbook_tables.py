# -*- coding: utf-8 -*-
"""The small tables of the logbook (per aircraft, year, month): the same calculation, the sum row, and the sizes
that follow the font (pure functions, no window)."""

import numpy as np
import pandas as pd
import pytest

from ethosloganalyser.analysis.logbook import logbook
from ethosloganalyser.gui.logbook_tables import aircraft_rows, month_label, month_rows, year_rows
from ethosloganalyser.gui.table_fit import (CELL_MARGIN, ROW_MARGIN, SORT_MARK, characters_for, column_width,
                                            REFERENCE_SCALING, row_height, scaled_window_size, shaped, widest_digits)


def _flights(rows):
    """Flight table of an analysis: (aircraft, date, duration [s], drawn mAh, battery valid)."""
    df = pd.DataFrame(rows, columns=["aircraft", "datum", "dauer_s", "entnommen_mAh", "Akku_gueltig"])
    df["datum"] = pd.to_datetime(df["datum"])
    df.insert(0, "Flug", np.arange(1, len(df) + 1))
    return df


@pytest.fixture
def book():
    return logbook(_flights([
        ("Viper", "2025-12-31 10:00", 300, 1000, True), ("Viper", "2025-12-31 11:00", 420, 1500, True),
        ("Glider", "2025-12-31 12:00", 600, 0, False), ("Glider", "2026-01-15 12:00", 240, 900, True),
        ("Viper", "2026-01-15 13:00", 360, 1200, True),
    ]))


# ---------------- per aircraft ----------------
def test_the_aircraft_table_adds_up_to_the_totals(book):
    per = book.per_aircraft
    assert list(per.index) == ["Glider", "Viper"]
    assert per["Fluege"].sum() == book.n_counted == 5
    assert per["dauer_s"].sum() == book.total_s
    assert per["entnommen_mAh"].sum() == book.mah_total              # flights with invalid battery values do not count
    assert list(per["Flugtage"]) == [2, 2]                           # flight days per aircraft ...
    assert book.flight_days == 2                                     # ... but days with any flight in total


def test_the_aircraft_table_uses_the_calculation_of_the_period_tables(book):
    only_viper = logbook(_flights([
        ("Viper", "2025-12-31 10:00", 300, 1000, True), ("Viper", "2025-12-31 11:00", 420, 1500, True),
        ("Viper", "2026-01-15 13:00", 360, 1200, True)]))
    row = only_viper.per_aircraft.loc["Viper"]
    assert (row["Fluege"], row["dauer_s"], row["Flugtage"], row["entnommen_mAh"]) == (3, 1080, 2, 3700)
    assert row["Fluege"] == only_viper.per_year["Fluege"].sum() and row["dauer_s"] == only_viper.per_year["dauer_s"].sum()


def test_empty_logbook_has_empty_tables_and_no_sum_row():
    for empty in (logbook(None), logbook(_flights([("Viper", None, 300, 1000, True)]))):    # none / no date
        assert empty.per_aircraft.empty
        assert aircraft_rows(empty) == ([], None)


def test_rows_of_the_aircraft_table_end_with_the_sum_row(book):
    rows, total = aircraft_rows(book)
    assert [row[0] for row in rows] == ["Glider", "Viper"]
    assert rows[1] == ("Viper", 3, 2, "18:00", "3700")               # name, flights, flight days, log duration, mAh
    assert total == ("Summe", 5, 2, "32:00", "4600")
    assert total[1] == sum(row[1] for row in rows) and total[3] == "32:00"


def test_rows_per_year_and_month_keep_their_content(book):
    assert year_rows(book) == [("2025", 3, "22:00", 1, "2500"), ("2026", 2, "10:00", 1, "2100")]
    assert month_rows(book) == [("12/2025", 3, "22:00", 1, "2500"), ("01/2026", 2, "10:00", 1, "2100")]
    assert month_label(2026, 3) == "03/2026"


def test_an_aircraft_without_valid_battery_values_shows_a_dash():
    book = logbook(_flights([("Glider", "2026-01-15 12:00", 240, 900, False)]))
    assert aircraft_rows(book)[0] == [("Glider", 1, 1, "4:00", "–")]


# ---------------- sizes that follow the font ----------------
def _font(pixels_per_character):
    """A fake font: every character is this wide; digits are one pixel wider than letters."""
    return lambda text: sum(pixels_per_character + 1 if char.isdigit() else pixels_per_character for char in text)


def test_a_column_is_as_wide_as_its_widest_text_plus_the_margin():
    measure = _font(8)
    assert column_width(measure, measure, "Flüge", ["00000"]) == measure("00000") + CELL_MARGIN      # the value
    assert column_width(measure, measure, "entnommen mAh", ["0"]) == measure("entnommen mAh") + CELL_MARGIN
    assert column_width(measure, measure, "Flüge", [], sortable=True) == measure("Flüge" + SORT_MARK) + CELL_MARGIN
    assert column_width(measure, measure, "Nr.") == measure("Nr.") + CELL_MARGIN                    # no samples


def test_heading_and_cell_text_are_measured_with_their_own_fonts():
    heading, cell = _font(9), _font(7)
    assert column_width(heading, cell, "Datum", ["00.00.0000"]) == max(heading("Datum"), cell("00.00.0000")) + CELL_MARGIN


@pytest.mark.parametrize("scaling", [1.0, 1.25, 1.5])
def test_nothing_is_cut_off_at_any_scaling(scaling):
    """The font grows with the display scaling; widths and heights computed from it grow along."""
    measure = _font(round(8 * scaling))
    headings = ["Flugzeug", "Flüge", "Flugtage", "Log-Dauer", "entnommen mAh"]
    values = ["Viper-Jet", "99999", "9999", "999:59:59", "9999999"]
    for heading, value in zip(headings, values):
        width = column_width(measure, measure, heading, [value], sortable=True)
        assert width >= measure(heading + SORT_MARK) and width >= measure(value)
    assert row_height(round(17 * scaling)) == round(17 * scaling) + ROW_MARGIN


def test_widths_and_row_height_grow_with_the_font():
    widths = [column_width(_font(size), _font(size), "Log-Dauer", ["999:59:59"]) for size in (8, 10, 12)]
    heights = [row_height(line) for line in (17, 21, 25)]
    assert widths == sorted(set(widths)) and heights == sorted(set(heights))


def test_the_widest_digit_and_shaped_texts():
    measure = lambda text: sum(10 if char == "8" else 7 for char in text)           # "8" is the widest digit
    assert widest_digits(measure, 3) == "888"
    assert shaped("12:05:09", "8") == "88:88:88" and shaped("Mai 2026", "8") == "Mai 8888"


def test_characters_for_the_widest_entry():
    measure = lambda text: 6 * len(text)                                            # "0" is 6 pixels wide
    assert characters_for(measure, ["a" * 10], minimum=5) == 12                     # 10 characters plus 2
    assert characters_for(measure, ["a" * 10], minimum=46) == 46                    # never below the minimum
    assert characters_for(measure, ["a" * 200], minimum=46, maximum=90) == 90       # nor above the maximum
    assert characters_for(measure, [], minimum=44) == 44


def test_the_window_grows_with_the_display_scaling_but_stays_on_the_screen():
    full_hd = (1920, 1080)
    assert scaled_window_size(REFERENCE_SCALING, (1400, 950), full_hd) == (1400, 950)            # 100 %
    assert scaled_window_size(REFERENCE_SCALING * 1.25, (1400, 950), (2560, 1440)) == (1750, 1188)
    assert scaled_window_size(REFERENCE_SCALING * 1.5, (1400, 950), full_hd) == (1880, 1000)     # limited by the screen
    assert scaled_window_size(REFERENCE_SCALING * 0.8, (1400, 950), (3840, 2160)) == (1400, 950)  # never smaller
