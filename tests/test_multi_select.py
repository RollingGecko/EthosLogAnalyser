# -*- coding: utf-8 -*-
"""Short text of a multi-value selection field (gui/multi_select.py); the widget itself is checked in test_gui."""

import pytest

from ethosloganalyser.gui.multi_select import selection_summary, shortened
from ethosloganalyser.i18n import set_language

YEARS = [(2022, "2022"), (2023, "2023"), (2024, "2024"), (2025, "2025"), (2026, "2026")]


def fits_ten(text):
    return len(text) <= 10


@pytest.fixture(autouse=True)
def german():
    set_language("de")
    yield
    set_language("de")


def test_everything_is_alle_and_nothing_is_keine():
    assert selection_summary(None, YEARS) == "alle"
    assert selection_summary(frozenset(y for y, _ in YEARS), YEARS) == "alle"     # every value ticked
    assert selection_summary(frozenset(), YEARS) == "keine"
    assert selection_summary(None, []) == "alle" and selection_summary(frozenset(), []) == "keine"


def test_chosen_values_are_named_in_the_order_of_the_options():
    assert selection_summary({2025, 2024}, YEARS, fits_ten) == "2024, 2025"
    assert selection_summary({2026}, YEARS, fits_ten) == "2026"


def test_too_many_values_are_counted():
    assert selection_summary({2023, 2024, 2025}, YEARS, fits_ten) == "3 von 5"
    assert selection_summary({2022, 2023, 2024, 2025}, YEARS, fits_ten) == "4 von 5"
    assert selection_summary({2023, 2024, 2025}, YEARS) == "2023, 2024, 2025"        # no limit: all named


def test_values_that_are_not_options_are_not_counted():
    assert selection_summary({2024, 1999}, YEARS, fits_ten) == "2024"
    assert selection_summary({1999}, YEARS, fits_ten) == "keine"


def test_a_single_name_that_is_too_long_is_cut():
    options = [("a", "Viper-Jet-Long-Name"), ("b", "Glider")]
    assert selection_summary({"a"}, options, fits_ten) == "Viper-Jet…"
    assert selection_summary({"b"}, options, fits_ten) == "Glider"
    assert shortened("short", fits_ten) == "short" and shortened("abcdefghijklmnop", fits_ten) == "abcdefghi…"


def test_texts_follow_the_language():
    set_language("en")
    assert selection_summary(None, YEARS) == "all" and selection_summary(frozenset(), YEARS) == "none"
    assert selection_summary({2023, 2024, 2025}, YEARS, fits_ten) == "3 of 5"
    set_language("es")
    assert selection_summary(None, YEARS) == "todos" and selection_summary({2023, 2024, 2025}, YEARS, fits_ten) == "3 de 5"
