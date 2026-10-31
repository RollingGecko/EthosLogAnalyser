"""Check that a release is consistent and extract its release notes.

Used by .github/workflows/release.yml, but also runnable locally before
setting a tag:

    python scripts/release_check.py --tag v0.3.0 --notes-out notes.md

Checks:
- the tag (if given) has the form vX.Y.Z or vX.Y.Z-beta.N (also alpha, rc) and matches ``__version__`` in
  src/ethosloganalyser/__init__.py,
- CHANGELOG.md has a non-empty section ``## X.Y.Z`` for that version.

The section body is written to ``--notes-out``. When running in GitHub
Actions, ``version`` is also written to ``$GITHUB_OUTPUT``.

Only the standard library is used, so the script runs without installing
the package.
"""

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INIT_FILE = ROOT / "src" / "ethosloganalyser" / "__init__.py"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"

# X.Y.Z, optionally with a pre-release label such as -beta.1 (alpha, beta or rc followed by a number)
VERSION_PATTERN = r"\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?"
VERSION_RE = re.compile(r"^%s$" % VERSION_PATTERN)
TAG_RE = re.compile(r"^v(%s)$" % VERSION_PATTERN)


class ReleaseError(Exception):
    """The release metadata is inconsistent."""


def read_version(init_text):
    """Return ``__version__`` from the text of ``__init__.py``."""
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', init_text, re.MULTILINE)
    if not match:
        raise ReleaseError("__version__ not found in src/ethosloganalyser/__init__.py")
    version = match.group(1)
    if not VERSION_RE.match(version):
        raise ReleaseError("__version__ = %r is not of the form X.Y.Z or X.Y.Z-beta.N" % version)
    return version


def version_from_tag(tag):
    """Return the version for a tag vX.Y.Z (or vX.Y.Z-beta.N)."""
    match = TAG_RE.match(tag)
    if not match:
        raise ReleaseError("tag %r is not of the form vX.Y.Z or vX.Y.Z-beta.N" % tag)
    return match.group(1)


def changelog_section(changelog_text, version):
    """Return the body of the ``## <version>`` section, stripped."""
    lines = changelog_text.splitlines()
    heading = re.compile(r"^##\s+v?%s\s*(?:[-–(].*)?$" % re.escape(version))
    start = None
    for i, line in enumerate(lines):
        if heading.match(line.strip()):
            start = i + 1
            break
    if start is None:
        raise ReleaseError("CHANGELOG.md has no section '## %s'" % version)
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    body = "\n".join(lines[start:end]).strip()
    if not body:
        raise ReleaseError("CHANGELOG.md section '## %s' is empty" % version)
    return body


def is_prerelease(version):
    """True for a version with a pre-release label, e.g. 1.0.0-beta.1."""
    return "-" in version


def check(tag=None, init_text=None, changelog_text=None):
    """Run all checks; return ``(version, notes)``."""
    if init_text is None:
        init_text = INIT_FILE.read_text(encoding="utf-8")
    if changelog_text is None:
        changelog_text = CHANGELOG_FILE.read_text(encoding="utf-8")
    version = read_version(init_text)
    if tag:
        tag_version = version_from_tag(tag)
        if tag_version != version:
            raise ReleaseError(
                "tag %s does not match __version__ = %s" % (tag, version))
    notes = changelog_section(changelog_text, version)
    return version, notes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", help="release tag, e.g. v0.3.0 (optional)")
    parser.add_argument("--notes-out", help="write the release notes to this file")
    args = parser.parse_args(argv)

    try:
        version, notes = check(tag=args.tag)
    except ReleaseError as exc:
        print("Release check failed: %s" % exc, file=sys.stderr)
        return 1

    if args.notes_out:
        Path(args.notes_out).write_text(notes + "\n", encoding="utf-8")
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as fh:
            fh.write("version=%s\n" % version)
            fh.write("prerelease=%s\n" % str(is_prerelease(version)).lower())
    print("Release check passed: version %s%s" % (
        version, " (tag %s)" % args.tag if args.tag else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
