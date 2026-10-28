# -*- coding: utf-8 -*-
"""The code map (docs/code-map.md) lists every Python file and no file that is gone.

The map has one table per directory. A heading with the directory in backticks (``## `src/ethosloganalyser/gui/` ``)
opens a table whose rows start with the file name in backticks (``| `app.py` | ...``); a row may name several files
(``| `__init__.py`, `en.py` | ...``). The full path of a file is the directory of the heading plus the name. The
test checks which files are listed, not how they are described.
"""

import re

from helpers import ROOT

CODE_MAP = ROOT / "docs" / "code-map.md"
CODE_ROOTS = ("src/ethosloganalyser", "tests", "scripts")      # directories whose Python files the map covers
GENERATED = {"src/ethosloganalyser/_build_tag.py"}             # written by the CI for test builds, not in git
UPDATE_HINT = ("Update docs/code-map.md in the same pull request: add a row for each new file, remove or fix the "
               "row of each file that was removed or renamed.")

HEADING_DIRECTORY = re.compile(r"^#{2,3}\s+`([^`]+/)`")
BACKTICKED_PYTHON_FILE = re.compile(r"`([^`]+\.py)`")


def python_files_of_the_project():
    """Paths (relative to the repository root, with '/') of every Python file the map has to list."""
    found = set()
    for root_name in CODE_ROOTS:
        found.update(path.relative_to(ROOT).as_posix() for path in (ROOT / root_name).rglob("*.py"))
    return found - GENERATED


def files_listed_in_the_map(text):
    """Paths of the Python files that table rows of the map name (directory of the heading + file name)."""
    listed = set()
    directory = None
    for line in text.splitlines():
        if line.startswith("#"):
            heading = HEADING_DIRECTORY.match(line)
            directory = heading.group(1) if heading else None      # a heading without a directory ends the table
        elif line.startswith("|") and directory is not None:
            first_cell = line.split("|")[1]
            listed.update(directory + name for name in BACKTICKED_PYTHON_FILE.findall(first_cell))
    return listed


def test_every_python_file_has_a_row_and_every_row_names_an_existing_file():
    listed = files_listed_in_the_map(CODE_MAP.read_text(encoding="utf-8"))
    existing = python_files_of_the_project()
    missing, stale = sorted(existing - listed), sorted(listed - existing)
    problems = []
    if missing:
        problems.append("Python files without a row in docs/code-map.md:\n  " + "\n  ".join(missing))
    if stale:
        problems.append("Rows in docs/code-map.md naming files that do not exist:\n  " + "\n  ".join(stale))
    assert not problems, "\n".join(problems) + "\n" + UPDATE_HINT


def test_the_checker_finds_rows_under_their_directory_heading():
    text = "\n".join([
        "## `src/pkg/`", "", "| File | Purpose |", "|---|---|",
        "| `a.py` | one |", "| `__init__.py`, `b.py` | two files in one row |", "",
        "## Where do I look", "| `not_a_file_of_a_table.py` | no directory heading above |", "",
        "### `tests/`", "| `test_a.py` | checks a |", "| `data.txt` | not Python |",
    ])
    assert files_listed_in_the_map(text) == {"src/pkg/a.py", "src/pkg/__init__.py", "src/pkg/b.py", "tests/test_a.py"}


def test_a_missing_or_stale_row_is_reported():
    text = CODE_MAP.read_text(encoding="utf-8")
    existing = python_files_of_the_project()
    without_row = text.replace("| `flight_filter.py` |", "| `renamed_filter.py` |", 1)
    listed = files_listed_in_the_map(without_row)
    assert "src/ethosloganalyser/gui/flight_filter.py" in existing - listed
    assert "src/ethosloganalyser/gui/renamed_filter.py" in listed - existing
