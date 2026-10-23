"""Tests for scripts/release_check.py (tag, version and changelog checks)."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "release_check.py"
_spec = importlib.util.spec_from_file_location("release_check", SCRIPT)
release_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(release_check)

INIT = '"""Package."""\n\n__version__ = "1.2.3"\n'
CHANGELOG = """# Changelog

## 1.2.3

- New feature.
- Fixed a bug.

## 1.2.2

- Older entry.
"""


def test_valid_tag_returns_version_and_notes():
    version, notes = release_check.check("v1.2.3", INIT, CHANGELOG)
    assert version == "1.2.3"
    assert notes == "- New feature.\n- Fixed a bug."


def test_without_tag_checks_version_and_changelog_only():
    version, notes = release_check.check(None, INIT, CHANGELOG)
    assert version == "1.2.3"
    assert "Older entry" not in notes


def test_last_section_runs_to_end_of_file():
    init = INIT.replace("1.2.3", "1.2.2")
    _, notes = release_check.check("v1.2.2", init, CHANGELOG)
    assert notes == "- Older entry."


@pytest.mark.parametrize("tag", ["v1.2.4", "1.2.3", "v1.2", "v1.2.3-rc1"])
def test_wrong_or_malformed_tag_fails(tag):
    with pytest.raises(release_check.ReleaseError):
        release_check.check(tag, INIT, CHANGELOG)


def test_missing_changelog_section_fails():
    init = INIT.replace("1.2.3", "2.0.0")
    with pytest.raises(release_check.ReleaseError, match="no section"):
        release_check.check("v2.0.0", init, CHANGELOG)


def test_empty_changelog_section_fails():
    changelog = "# Changelog\n\n## 1.2.3\n\n## 1.2.2\n\n- x\n"
    with pytest.raises(release_check.ReleaseError, match="empty"):
        release_check.check("v1.2.3", INIT, changelog)


def test_missing_version_fails():
    with pytest.raises(release_check.ReleaseError, match="__version__"):
        release_check.check(None, "x = 1\n", CHANGELOG)


def test_repository_metadata_is_consistent():
    """The real __init__.py and CHANGELOG.md must always be releasable."""
    version, notes = release_check.check()
    assert notes


def test_main_writes_notes_and_github_output(tmp_path, monkeypatch):
    out = tmp_path / "gh_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    notes_file = tmp_path / "notes.md"
    version, _ = release_check.check()
    assert release_check.main(["--tag", "v" + version,
                               "--notes-out", str(notes_file)]) == 0
    assert notes_file.read_text(encoding="utf-8").strip()
    assert out.read_text(encoding="utf-8") == "version=%s\n" % version


def test_main_fails_on_wrong_tag(monkeypatch):
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    assert release_check.main(["--tag", "v99.99.99"]) == 1
