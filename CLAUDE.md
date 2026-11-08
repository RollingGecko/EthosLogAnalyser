# EthosLogAnalyser – working rules for Claude

Python/Tkinter desktop app (Windows EXE) that analyses FrSky Ethos flight logs (CSV): battery health and ageing, load, drive, radio and onboard power, receiver current spikes, a flight logbook (SQLite) and a flight recorder. The owner (GitHub: RollingGecko) tests on Windows with real flight data and merges every pull request himself.

## Talking to the owner
- Speak German with the owner: short and clear; questions always with a recommendation.
- Everything on GitHub is English: commit messages, PR titles and texts, README, CHANGELOG, docs/, code comments, docstrings, test names. UI texts are German in the code (`tr()` / `N_()` / `Msg()` in `i18n.py`) with translations in `locales/en.py` and `locales/es.py`.

## Work flow
1. Read `docs/code-map.md` first instead of searching the repository. Every PR that adds, removes or renames a `.py` file, or moves responsibilities, updates it (`tests/test_code_map.py` fails otherwise).
2. Work from the current `origin/main`, one branch and one PR per ticket. **Only pull requests, never push to `main`, never force-push `main`.** The owner approves with the test EXE and merges.
3. Build only what the ticket asks for. Ideas that come up go into the report as a question, not into the code. Do not remove existing displays without asking. If a first and a second attempt fail, stop and report instead of building on.
4. Before a PR: all tests green (Linux 3.9/3.12, Windows in CI), no second Tk window (`run_gui()`) in a test session (logic as pure functions with unit tests, GUI checks in `tests/recorder_checks.py`-style helpers called from `test_gui.py`), new UI texts in de/en/es (`tests/test_i18n.py`), `docs/usage.md` and README for visible changes, CHANGELOG under "Unreleased" (it becomes the release notes: one short line per change in plain words for pilots, at most 300 characters, no ticket numbers, file names or measurements; `scripts/release_check.py` rejects the rest). Version stays 0.3.0 until the owner releases.
5. Analysis or display changes: run against the real logs in `examples/logs_2026` (read only) and put before/after numbers into the PR text. The PR text describes in words what the owner will see.
6. Every PR gets a Windows test EXE from CI (comment on the PR). Checks: "CI / Tests (...)", "CI / Build Windows EXE", "Check version and changelog", "Link the test EXE in the pull request". Locally tkinter may be missing; then the CI counts.
7. Releases only by the owner's tag `vX.Y.Z` (see `docs/releasing.md`).

## Kanban (tickets and packages)
Board: GitHub project https://github.com/users/RollingGecko/projects/3, read and written with `gh project` (the token needs the `project` scope: `gh auth refresh -s project`). Tickets are draft items titled "TW-nnn: ..."; the card text holds the detail, "### Checks" and "### Kommentare". Fields: `Status` (InBox, Backlog, Ready, In progress, In review, Done), `Priority` (P0–P3), `Ticket`, `Ticket type`, `Area`, `Workstream`, `Package` (WP-nn). A package is the set of tickets with the same `Package` value; there are no package cards. The old claude.ai board (until 2026-11-07) is read-only history. When you are told "start WP-nn":
1. List the items (`gh project item-list 3 --owner RollingGecko --format json --limit 500`) and read the tickets with that package. Move them from Ready to In progress (`gh project item-edit --project-id <project id> --id <item id> --field-id <Status field id> --single-select-option-id <option id>`; ids from `gh project view` / `gh project field-list`).
2. Work as described above.
3. When the PR is open: move the tickets to In review and update the card text (`gh project item-edit --id <draft issue id DI_...> --body ...`, keep the existing text): add the PR number, the steps for the owner with the test EXE under "### Checks" and "Ergebnis: ..." at the end. Put the short report (what was done, PR number, what to check, questions with a recommendation, chat length) into the PR text.
4. When the owner says the PR is merged: tickets to Done.
New tickets go in as draft items with the next free TW number, status InBox and the fields filled in.

## Code style
- Readable, maintainable code: meaningful names (no `df2`, `res`, `p`), a docstring for every module, class and public function, comments explain why, small functions, no file over about 500 lines. Code language is English. Bring old code into this style when you touch it.
- Pure logic in modules without Tkinter, drawing only in `gui/`. Move existing canvas items (`coords`, `itemconfigure`) instead of recreating them. Fonts and minimum sizes follow the line height of the font (Windows scaling up to 150 %).

## Domain rules
- Logs of several aircraft: the model comes from the file name; never assume the number of servos, control surfaces, motor or battery sensors. Battery settings are per model.
- Do not assume measurements the log does not have (e.g. only the total receiver current exists, not one per servo). Never present a diagnosis as fact (always a hint or an estimate).
- Never invent Ethos API details; mark anything uncertain and let the owner test it in the simulator or at the transmitter.
- Performance: no long waits for the owner (single flight opens in under a second; redraw per recorder row in milliseconds).
- UI languages: German, English, Spanish, switchable and saved; the first start follows the system language if supported, else English.
- Raw logs stay out of project documents; they are in `examples/logs_2026`.
