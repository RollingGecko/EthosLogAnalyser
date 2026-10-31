# -*- coding: utf-8 -*-
"""Translations: catalogs are complete and consistent, reports and charts work in every language."""

import ast
import io
import string
from pathlib import Path

import pytest

from helpers import ROOT, example_result
from ethosloganalyser import i18n
from ethosloganalyser.config import Params
from ethosloganalyser.i18n import LANGUAGES, LazyDate, Msg, N_, tr
from ethosloganalyser.plots.flight import FLIGHT_VIEWS, figure_flight
from ethosloganalyser.plots.overview import figure_akku, figure_antrieb, figure_belastung, figure_funk
from ethosloganalyser.report.text import flight_detail_lines, summary_lines

PACKAGE = ROOT / "src" / "ethosloganalyser"
TRANSLATED = [code for code in LANGUAGES if code != i18n.SOURCE_LANGUAGE]


def _msgids():
    """All string literals passed as first argument to tr(), N_() or Msg() in the package."""
    ids = {}
    for path in sorted(PACKAGE.rglob("*.py")):
        if "locales" in path.parts:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)
            arg = node.args[0]
            if name in ("tr", "N_", "Msg") and isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                ids.setdefault(arg.value, f"{path.relative_to(PACKAGE)}:{node.lineno}")
    return ids


def _fields(text):
    return sorted({f for _, f, _, _ in string.Formatter().parse(text) if f is not None})


def test_source_code_contains_translatable_texts():
    assert len(_msgids()) > 300


@pytest.mark.parametrize("lang", TRANSLATED)
def test_every_text_is_translated(lang):
    catalog = i18n.CATALOGS[lang]
    missing = [f"{msgid!r}  ({where})" for msgid, where in _msgids().items() if msgid not in catalog]
    assert not missing, f"{len(missing)} texts without {lang} translation:\n" + "\n".join(missing)


@pytest.mark.parametrize("lang", TRANSLATED)
def test_catalog_has_no_unused_entries(lang):
    unused = sorted(set(i18n.CATALOGS[lang]) - set(_msgids()))
    assert not unused, f"{lang} catalog contains texts that are no longer used:\n" + "\n".join(map(repr, unused))


@pytest.mark.parametrize("lang", TRANSLATED)
def test_translations_keep_the_placeholders(lang):
    wrong = [msgid for msgid, text in i18n.CATALOGS[lang].items() if _fields(msgid) != _fields(text)]
    assert not wrong, "placeholders differ:\n" + "\n".join(map(repr, wrong))


@pytest.mark.parametrize("lang", TRANSLATED)
def test_translations_are_not_empty(lang):
    assert all(text.strip() or not msgid.strip() for msgid, text in i18n.CATALOGS[lang].items())


def test_tr_translates_and_falls_back_to_german():
    assert tr("Zusammenfassung") == "Zusammenfassung"
    i18n.set_language("en")
    assert tr("Zusammenfassung") == "Summary"
    assert tr("zu kurz ({dur} < {min})", dur="0:12 min", min="2:00 min") == "too short (0:12 min < 2:00 min)"
    assert tr("Text, den es im Katalog nicht gibt") == "Text, den es im Katalog nicht gibt"
    i18n.set_language("es")
    assert tr("Zusammenfassung") == "Resumen"


def test_notes_of_the_recorder_aircraft_in_every_language():
    from ethosloganalyser.gui.recorder_aircraft import NO_STICKS
    from ethosloganalyser.gui.recorder_instruments import NO_ATTITUDE
    expected = {"de": ("keine Lagedaten", "keine Knüppeldaten"), "en": ("no attitude data", "no stick data"),
                "es": ("sin datos de actitud", "sin datos de los mandos")}
    for lang, texts in expected.items():
        i18n.set_language(lang)
        assert (tr(NO_ATTITUDE), tr(NO_STICKS)) == texts


def test_unknown_language_falls_back_to_english():
    i18n.set_language("xx")
    assert i18n.get_language() == "en"


def test_msg_is_translated_when_shown():
    from datetime import datetime
    m = Msg("Flug {no} ({date}): auffälliger Wert bei {label} ({value}, erwartet ca. {expected}).",
            no=3, date=LazyDate(datetime(2026, 9, 13)), label=Msg(N_("Innenwiderstand")), value="5.6", expected="4.4")
    assert str(m) == "Flug 3 (13.09.2026): auffälliger Wert bei Innenwiderstand (5.6, erwartet ca. 4.4)."
    i18n.set_language("en")
    assert str(m) == "Flight 3 (13/09/2026): unusual value for Internal resistance (5.6, expected approx. 4.4)."


def test_analysis_result_can_be_shown_in_every_language_without_new_analysis():
    res = example_result(nominal_mah=3000.0)            # produces warnings in meta
    for lang in LANGUAGES:
        i18n.set_language(lang)
        warnings = [str(text) for _, text in res.meta["warnings"]]
        assert warnings and all(warnings)
        if lang == "en":
            assert any(w.startswith("Implausible state of charge") for w in warnings)
        if lang == "es":
            assert any(w.startswith("Estado de carga inverosímil") for w in warnings)


@pytest.mark.parametrize("lang", list(LANGUAGES))
def test_reports_in_every_language(lang):
    i18n.set_language(lang)
    res = example_result()
    lines = summary_lines(res, Params())
    heads = [txt for tag, txt in lines if tag == "h"]
    assert heads[0] == tr("ÜBERSICHT")
    for path in res.df["pfad"]:
        detail = flight_detail_lines(res, Params(), path)
        assert detail[0][1].startswith(tr("Flug"))
    if lang == "en":
        assert "OVERVIEW" in heads and "TIMER RECOMMENDATION" in heads
    if lang == "es":
        assert "VISTA GENERAL" in heads


@pytest.mark.parametrize("lang", TRANSLATED)
def test_charts_in_every_language(lang):
    i18n.set_language(lang)
    res = example_result()
    figs = [fn(res, Params()) for fn in (figure_akku, figure_belastung, figure_antrieb, figure_funk)]
    figs += [figure_flight(res, Params(), res.df["pfad"].iloc[-1], view) for view in FLIGHT_VIEWS]
    for fig in figs:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=30)
        assert buf.tell() > 1000
    assert figs[0].axes[0].get_title(loc="left") == tr("Geschätzte Gesamtkapazität [mAh]")


def test_detect_language_from_environment(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    for value, expected in (("de_DE.UTF-8", "de"), ("es_ES.UTF-8", "es"), ("en_GB.UTF-8", "en"), ("fr_FR.UTF-8", "en")):
        for var in ("LC_ALL", "LC_MESSAGES", "LANGUAGE"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("LANG", value)
        monkeypatch.setattr("locale.getlocale", lambda *a: (None, None))
        assert i18n.detect_language() == expected, value
