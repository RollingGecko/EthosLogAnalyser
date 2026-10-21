# -*- coding: utf-8 -*-
"""Textberichte und Diagramme lassen sich ohne Oberfläche erzeugen."""

import io

from helpers import example_result
from ethosloganalyser.config import Params
from ethosloganalyser.plots.flight import FLIGHT_VIEWS, figure_flight
from ethosloganalyser.plots.overview import figure_akku, figure_antrieb, figure_belastung, figure_funk
from ethosloganalyser.report.text import flight_detail_lines, summary_lines


def _render(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=40)
    assert buf.tell() > 1000


def test_zusammenfassung_hat_alle_abschnitte():
    lines = summary_lines(example_result(), Params())
    heads = [txt for tag, txt in lines if tag == "h"]
    for h in ["ÜBERSICHT", "AKKU ÜBER ALLE FLÜGE", "ALTERUNG UND RESTKAPAZITÄT", "TIMER-EMPFEHLUNG",
              "ANTRIEB UND SENSOREN", "WARNUNGEN UND AUFFÄLLIGKEITEN"]:
        assert h in heads
    assert all(tag in {"h", "ok", "warn", "bad", "info"} for tag, _ in lines)


def test_einzelflug_bericht_fuer_jeden_flug():
    res = example_result()
    for path in res.df["pfad"]:
        lines = flight_detail_lines(res, Params(), path)
        assert lines[0][0] == "h" and "Flug" in lines[0][1]
        assert any("Innenwiderstand" in txt for _, txt in lines)


def test_uebersichtsdiagramme():
    res = example_result()
    for fn in (figure_akku, figure_belastung, figure_antrieb, figure_funk):
        _render(fn(res, Params()))


def test_einzelflug_ansichten():
    res = example_result()
    path = res.df["pfad"].iloc[-1]
    for view in FLIGHT_VIEWS:
        _render(figure_flight(res, Params(), path, view))
