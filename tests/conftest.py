# -*- coding: utf-8 -*-
"""Every test starts in German (the source language) and must not leave another language behind."""

import pytest

import helpers  # noqa: F401  (sets the import path)
from ethosloganalyser import i18n


@pytest.fixture(autouse=True)
def german_by_default():
    i18n.set_language("de")
    yield
    i18n.set_language("de")
