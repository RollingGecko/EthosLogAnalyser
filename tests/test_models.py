# -*- coding: utf-8 -*-
"""Several aircraft in one folder: model from the file name, one model per analysis, period filter per model."""

import shutil
from pathlib import Path

import pytest

import helpers
from ethosloganalyser import Params, analyse_folder
from ethosloganalyser.analysis.fleet import default_model, find_logs, models_in
from ethosloganalyser.config import model_label
from ethosloganalyser.gui.app_settings import battery_unset_for
from ethosloganalyser.gui.common import export_table
from ethosloganalyser.i18n import set_language
from ethosloganalyser.io.ethos_log import UNKNOWN_MODEL, model_from_filename


@pytest.mark.parametrize("name, model", [
    ("Viper-Jet-2026-04-19-13-25-36.csv", "Viper-Jet"),             # hyphen in the model name
    ("-Viper-Jet-2022-07-30-12-12-38.csv", "Viper-Jet"),            # leading "-" is ignored
    ("Extra-330SC-2025-08-17-14-09-46.csv", "Extra-330SC"),         # digits in the model name
    ("Jet-1234-2026-04-19-13-25-36.csv", "Jet-1234"),               # digits right before the time stamp
    ("F16_2026-04-19_13-25-36.csv", "F16"),                         # other separators
    ("Edge 540-2026-05-01.csv", "Edge 540"),                        # date only
    ("2026-04-19-13-25-36.csv", UNKNOWN_MODEL),                     # no model part
    ("log.csv", UNKNOWN_MODEL),                                     # no date at all
    ("sub/dir/Glider-2026-06-01-10-00-00.csv", "Glider"),           # path
])
def test_model_from_file_name(name, model):
    assert model_from_filename(name) == model


def test_unknown_model_label():
    set_language("de")
    assert model_label(UNKNOWN_MODEL) == "(unbekannt)"
    assert model_label("Viper-Jet") == "Viper-Jet"
    set_language("en")
    assert model_label(UNKNOWN_MODEL) == "(unknown)"
    set_language("de")


def _two_model_folder():
    """The three example logs as model "Viper-Jet" plus two of them renamed to an older model "Edge-540"."""
    d = Path(helpers.tmpdir())
    for f in helpers.EXAMPLE_FILES:
        shutil.copy(f, d / f.name)
    sub = d / "edge"
    sub.mkdir()
    for f, stamp in zip(helpers.EXAMPLE_FILES[:2], ("2025-06-01-10-00-00", "2025-06-01-11-00-00")):
        shutil.copy(f, sub / f"Edge-540-{stamp}.csv")
    return d


def test_grouping_and_default_model():
    d = _two_model_folder()
    groups = models_in(find_logs(d))
    assert {m: len(g["files"]) for m, g in groups.items()} == {"Viper-Jet": 3, "Edge-540": 2}
    assert default_model(groups) == "Viper-Jet"                      # the model with the newest log
    assert default_model({}) is None


def test_one_model_per_analysis():
    d = _two_model_folder()
    p = Params()
    res = analyse_folder(str(d), p)                                  # default: newest model
    assert res.meta["model"] == "Viper-Jet" and res.meta["models"] == {"Viper-Jet": 3, "Edge-540": 2}
    assert len(res.df) == 3 and set(res.df["Modell"]) == {"Viper-Jet"} and res.total == 3
    edge = analyse_folder(str(d), p, model="Edge-540")
    assert len(edge.df) == 2 and set(edge.df["Modell"]) == {"Edge-540"}
    assert list(edge.df["Flug"]) == [1, 2]                           # numbered per model
    assert analyse_folder(str(d), p, model="Unknown plane").meta["model"] == "Viper-Jet"


def test_period_filter_within_a_model():
    d = _two_model_folder()
    res = analyse_folder(str(d), Params(date_from="2026-09-20"), model="Viper-Jet")
    assert len(res.df) == 2 and res.meta["outside_period"] == 1      # only this model's logs are counted
    res = analyse_folder(str(d), Params(date_from="2026-09-20"), model="Edge-540")
    assert res.df.empty and res.meta["outside_period"] == 2


def test_single_model_folder_is_unchanged_and_export_has_model_column():
    res = helpers.example_result()
    assert res.meta["models"] == {"Viper-Jet": 3} and res.meta["model"] == "Viper-Jet"
    set_language("de")
    out = export_table(res.df)
    assert list(out["Modell"]) == ["Viper-Jet"] * 3
    res.df.loc[:, "Modell"] = UNKNOWN_MODEL
    assert list(export_table(res.df)["Modell"]) == ["(unbekannt)"] * 3
    res.df.loc[:, "Modell"] = "Viper-Jet"                            # cached result: leave it as it was


def test_empty_folder():
    res = analyse_folder(helpers.tmpdir(), Params())
    assert res.df.empty and res.meta["model"] is None and res.meta["models"] == {}


def test_battery_unset_only_without_stored_settings():
    """The battery hint (TW-033) is shown only for a model whose battery fields hold just the defaults."""
    old = {"language": "de", "chem": "Li-Ion", "cells": "13", "nominal_mah": "9000"}
    # first model: settings from before models existed are taken over -> set up; none at all -> unset
    assert not battery_unset_for("Viper-Jet", {}, old)
    assert battery_unset_for("Viper-Jet", {}, {"language": "de"})
    # another model without stored settings -> unset; stored models keep their flag
    ms = {"Viper-Jet": {"chem": "Li-Ion", "cells": "13", "nominal_mah": "9000"}}
    assert battery_unset_for("Edge-540", ms, old)
    assert not battery_unset_for("Viper-Jet", ms, old)
    ms["Edge-540"] = {"chem": "LiPo", "cells": "0", "nominal_mah": "0", "unset": True}
    assert battery_unset_for("Edge-540", ms, old)
    ms["Edge-540"] = {"chem": "LiPo", "cells": "0", "nominal_mah": "0"}       # chemistry chosen (LiPo)
    assert not battery_unset_for("Edge-540", ms, old)
