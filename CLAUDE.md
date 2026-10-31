# EthosLogAnalyser – working rules for Claude

Python/Tkinter desktop app (Windows EXE) that analyses FrSky Ethos flight logs (CSV): battery health and ageing, load, drive, radio and onboard power, receiver current spikes, a flight logbook (SQLite) and a flight recorder. The owner (GitHub: RollingGecko) tests on Windows with real flight data and merges every pull request himself.

## Talking to the owner
- Speak German with the owner: short and clear; questions always with a recommendation.
- Everything on GitHub is English: commit messages, PR titles and texts, README, CHANGELOG, docs/, code comments, docstrings, test names. UI texts are German in the code (`tr()` / `N_()` / `Msg()` in `i18n.py`) with translations in `locales/en.py` and `locales/es.py`.

## Work flow
1. Read `docs/code-map.md` first instead of searching the repository. Every PR that adds, removes or renames a `.py` file, or moves responsibilities, updates it (`tests/test_code_map.py` fails otherwise).
2. Work from the current `origin/main`, one branch and one PR per ticket. **Only pull requests, never push to `main`, never force-push `main`.** The owner approves with the test EXE and merges.
3. Build only what the ticket asks for. Ideas that come up go into the report as a question, not into the code. Do not remove existing displays without asking. If a first and a second attempt fail, stop and report instead of building on.
4. Before a PR: all tests green (Linux 3.9/3.12, Windows in CI), no second Tk window (`run_gui()`) in a test session (logic as pure functions with unit tests, GUI checks in `tests/recorder_checks.py`-style helpers called from `test_gui.py`), new UI texts in de/en/es (`tests/test_i18n.py`), `docs/usage.md` and README for visible changes, CHANGELOG under "Unreleased". Version stays 0.3.0 until the owner releases.
5. Analysis or display changes: run against the real logs in `examples/logs_2026` (read only) and put before/after numbers into the PR text. The PR text describes in words what the owner will see.
6. Every PR gets a Windows test EXE from CI (comment on the PR). Checks: "CI / Tests (...)", "CI / Build Windows EXE", "Check version and changelog", "Link the test EXE in the pull request". Locally tkinter may be missing; then the CI counts.
7. Releases only by the owner's tag `vX.Y.Z` (see `docs/releasing.md`).

## Kanban (tickets and packages)
Board: https://claude.ai/artifact/Nm7aVSuC74UbT8TzV8BmBN – read and write with the ArtifactData tool; collections `tickets` (TW-nnn), `packages` (WP-nn), `messages`. When you are told "start WP-nn":
1. Read `packages/WP-nn` and the tickets with that package. Set the package `status` to `delivered` (only if still `ready`) and the tickets from `ready` to `progress`. Pin every write with `if_version`.
2. Work as described above.
3. When the PR is open: set the tickets to `review`, fill `checks` ("how" = steps for the owner with the test EXE, "where" = app) and add "Ergebnis: ..." to the ticket detail. Put the short report (what was done, PR number, what to check, questions with a recommendation, chat length) into the PR text and as a message to `hub` only if a decision is needed.
4. When the owner says the PR is merged: tickets and package to `done`.

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
