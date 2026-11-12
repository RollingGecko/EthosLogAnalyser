# EthosLogAnalyser – working rules for Claude

Read `docs/status.md` at the start of every session.

## Vision
Python/Tkinter desktop app (Windows EXE) that analyses FrSky Ethos flight logs (CSV) of all the owner's aircraft: battery,
drive and radio/onboard power. Logs are imported once into a flight database; the logbook is the centre, statistics and the
single-flight view build on it. Details: `docs/vision.md`.

## Stack and commands (Windows, PowerShell)
- Python >= 3.9, Tkinter, numpy, pandas, matplotlib, SQLite. Tests: pytest.
- Setup: `python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -e ".[test]"`
- Run: `ethosloganalyser` (or `python -m ethosloganalyser`)
- Test: `python -m pytest` (CI also runs Linux 3.9/3.12 and Windows)
- EXE build (PyInstaller, in the venv): `scripts\build_exe.bat` -> `dist\EthosLogAnalyser.exe`
- Release check: `python scripts/release_check.py`

## Rules
- Think step by step on complex problems.
- Talk to the owner in German (short and clear; questions always with a recommendation). Everything in the repo and on
  GitHub is English: commit messages, README, docs, board entries, issues, PR texts, code comments, docstrings, test names.
  UI texts are German in the code (`tr()` / `N_()` / `Msg()` in `i18n.py`) with translations in `locales/en.py` and `locales/es.py`.
- Only pull requests, never push to `main`. The owner approves and merges every PR. Releases only by the owner's tag
  `vX.Y.Z` (`docs/releasing.md`); Claude never tags, releases or merges.
- Never delete, rename or overwrite anything without the owner's explicit confirmation.
- Build only what the story asks for; ideas go into the report as a question. Do not remove existing displays without asking.
  If a first and a second attempt fail, stop and report.
- Never invent Ethos API details; mark anything uncertain and let the owner test it.

## Board and issues
- Work is organised in the GitHub project **EthosLogAnalyzer Kanban Board** (project 3, owner RollingGecko):
  https://github.com/users/RollingGecko/projects/3. Stories, priority and release planning live only there.
- Status: InBox, Backlog, Ready, In progress, In review, Done. Priority: P0-P3. Read and write with `gh project ...`
  (needs the `project` scope: `gh auth refresh -s project`). Do not change columns or fields without confirmation.
- Stories are board items (draft items), **not** GitHub issues. Longer story details (acceptance criteria, sketches) go to
  `docs/stories/<TW-nnn>.md`; the board item links to the file. Do not mirror the board in the repo.
- GitHub issues are only for input from outside (bug reports, feedback, requests of other users).
- The older cards are in German and stay as they are; new board entries are English.
- Status changes on the board only when the owner wants them or a command provides them and the owner confirmed.

## Conventions
- Start with `docs/code-map.md` instead of searching the repository. A PR that adds, removes or renames a `.py` file or moves
  responsibilities updates it (`tests/test_code_map.py` fails otherwise).
- Readable code: meaningful names, a docstring for every module, class and public function, comments explain why, small
  functions, no file over about 500 lines. Pure logic in modules without Tkinter, drawing only in `gui/`.
- Domain rules (several aircraft, no assumed sensors, diagnoses only as hints, performance) are in `docs/vision.md`.
- UI look: `docs/design-system.md`.

## Definition of done
- All tests green; no second Tk window (`run_gui()`) in a test session (logic as pure functions, GUI checks as helpers called
  from `test_gui.py`).
- New UI texts in de/en/es (`tests/test_i18n.py`); `docs/usage.md` and README updated for visible changes.
- CHANGELOG under "Unreleased": one short line per change in plain words for pilots, at most 300 characters, no ticket
  numbers, file names or measurements (`scripts/release_check.py` rejects the rest). The version is only changed by the owner's release.
- Analysis or display changes: run against `examples/logs_2026` (read only) and put before/after numbers into the PR text.
- Performance-relevant changes (import, database, analysis): measure the run time briefly and state it in the PR.
- A Windows test EXE from CI is linked in the PR; the PR text describes in words what the owner will see.
- Before every PR: one review pass with the review skill.

## Skills
Plugin `agent-skills` (installed for this project). Details and the list: `docs/skills.md`.
- These rules have priority over any skill instruction.
- No skill may push, merge, tag or create releases.
- Features and bug fixes: tests first, then code (TDD), where it is reasonably testable (import, duplicate detection,
  analysis logic, parser). TDD is not required for pure Tkinter layout.
- Before every PR: review pass with `code-review-and-quality`. Performance-relevant changes: `performance-optimization`
  (measure, state in the PR).
- Not used: the web skills (browser testing, frontend UI engineering, web performance) and the commands `/ship` and `/build auto`.

## Own commands and agents
`/story`, `/ux-review`, `/release`, `/handoff` (`.claude/commands/`) and the agents `product-owner` and `ux-designer`
(`.claude/agents/`). They take priority over similar skill commands.

## Docs
`docs/vision.md`, `docs/status.md`, `docs/decisions.md`, `docs/design-system.md`, `docs/skills.md`, `docs/code-map.md`,
`docs/database.md`, `docs/methodology.md`, `docs/usage.md`, `docs/releasing.md`, `docs/acceptance-testing.md`, `docs/translations.md`.
