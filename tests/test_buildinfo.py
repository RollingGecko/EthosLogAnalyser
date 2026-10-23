# -*- coding: utf-8 -*-
"""Test-build marker: build tag from the CI script, version and test marker shown by the app."""

import importlib.util
from pathlib import Path

import pytest

import helpers  # noqa: F401  (puts src on the path)
from ethosloganalyser import __version__, buildinfo
from ethosloganalyser.i18n import get_language, set_language

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "set_build_tag.py"
_spec = importlib.util.spec_from_file_location("set_build_tag", SCRIPT)
set_build_tag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(set_build_tag)

SHA = "abc1234def5678900000000000000000000000ff"


@pytest.fixture
def lang():
    old = get_language()
    yield set_language
    set_language(old)


# ---------------------------------------------------------------- CI script

def test_pull_request_tag():
    assert set_build_tag.make_tag(SHA, pr="12") == "pr12.abc1234"


def test_branch_tag_is_sanitised():
    assert set_build_tag.make_tag(SHA, ref="feature/PR-Test_Builds") == "feature.pr.test.builds.abc1234"
    assert set_build_tag.make_tag(SHA, ref="main") == "main.abc1234"
    assert set_build_tag.make_tag(SHA, ref="///") == "branch.abc1234"
    # a hostile branch name cannot break out of the generated Python string
    tag = set_build_tag.make_tag(SHA, ref='x"; import os; "')
    assert set_build_tag.TAG_PATTERN.match(tag) and '"' not in tag


@pytest.mark.parametrize("kw", [dict(sha="xyz"), dict(sha="abc12"), dict(sha=SHA, pr="12; rm"), dict(sha="")])
def test_invalid_input_is_rejected(kw):
    with pytest.raises(ValueError):
        set_build_tag.make_tag(**kw)


def test_exe_name():
    assert set_build_tag.exe_name("0.3.0", "pr12.abc1234") == "EthosLogAnalyser-0.3.0-pr12-abc1234.exe"


def test_script_writes_module_and_outputs(tmp_path, monkeypatch):
    tag_file, out = tmp_path / "_build_tag.py", tmp_path / "github_output"
    monkeypatch.setattr(set_build_tag, "TAG_FILE", tag_file)
    assert set_build_tag.main(["--sha", SHA, "--pr", "7", "--github-output", str(out)]) == 0
    ns = {}
    exec(tag_file.read_text(encoding="utf-8"), ns)
    assert ns["BUILD_TAG"] == "pr7.abc1234"
    lines = dict(line.split("=", 1) for line in out.read_text(encoding="utf-8").splitlines())
    assert lines == {"tag": "pr7.abc1234", "version": f"{__version__}+pr7.abc1234",
                     "exe": f"EthosLogAnalyser-{__version__}-pr7-abc1234.exe",
                     "artifact": f"EthosLogAnalyser-{__version__}-pr7-abc1234"}
    # the generated tag is accepted by the app's pattern
    assert buildinfo.TAG_PATTERN.match(ns["BUILD_TAG"])


def test_script_fails_on_bad_sha(tmp_path, monkeypatch):
    monkeypatch.setattr(set_build_tag, "TAG_FILE", tmp_path / "_build_tag.py")
    assert set_build_tag.main(["--sha", "nope", "--pr", "7"]) == 1
    assert not (tmp_path / "_build_tag.py").exists()


# ---------------------------------------------------------------- app

def test_release_build_shows_the_plain_version(lang):
    lang("de")
    assert buildinfo.full_version("") == __version__
    assert not buildinfo.is_test_build("")
    title = buildinfo.window_title("")
    assert __version__ in title and "TEST" not in title
    assert [k for k, _ in buildinfo.about_lines("")] == ["version", "info"]


@pytest.mark.parametrize("code, word", [("de", "TESTVERSION"), ("en", "TEST VERSION"), ("es", "VERSIÓN DE PRUEBA")])
def test_test_build_is_marked_in_title_and_about_box(lang, code, word):
    lang(code)
    tag = "pr12.abc1234"
    assert buildinfo.full_version(tag) == f"{__version__}+pr12.abc1234"
    title = buildinfo.window_title(tag)
    assert title.startswith(word) and f"{__version__}+pr12.abc1234" in title
    kinds = dict(buildinfo.about_lines(tag))
    assert f"{__version__}+pr12.abc1234" in kinds["version"]
    assert "pr12.abc1234" in kinds["test"]


def test_source_checkout_has_no_build_tag():
    # _build_tag.py is generated only during the CI build of the EXE and is not part of the repository
    tag_file = Path(buildinfo.__file__).with_name("_build_tag.py")
    assert buildinfo.build_tag() == ("" if not tag_file.exists() else buildinfo.BUILD_TAG)
    assert "/src/ethosloganalyser/_build_tag.py" in (SCRIPT.parent.parent / ".gitignore").read_text(encoding="utf-8")
