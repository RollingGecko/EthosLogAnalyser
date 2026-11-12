# Status

Updated: 2026-11-12. No backlog here, that is in the board:
https://github.com/users/RollingGecko/projects/3

**Current**: v1.0.0 published (2026-11-02). Phase: feedback and further development.

## In progress
- Nothing is being built right now. On the board in *In review*: TW-053 (recorder: sign of roll and pitch), TW-063 (example
  model files), TW-011 and TW-006 (Lua battery widget, mock for the simulator).

## Done
- v1.0.0: flight database with import and duplicate detection, logbook, notes and anomalies, single flight with charts and
  flight recorder, statistics (experimental), three UI languages, user guides (EN/DE), release pipeline with ZIP.
- Workflow changed to board stories, agents, commands and skills (this branch `chore/workflow-setup`, PR pending).

## Next
- Highest priority on the board: TW-072 (receiver current missing in logs with German sensor names, e.g. Predator).
- Then the rest of the board by priority; the owner decides.

## Open questions
- Is the sign of roll and pitch in the flight recorder correct for all manoeuvres (TW-053)?
- Does every log file contain exactly one flight? (Assumed; not guaranteed by the code.)
- Where is the concept of 2026-10-25 kept? It exists only as board item TW-034 (its source file `hub/v2-neubau.md` is not in the repo).
- Battery settings still live in the settings file of the computer, not in the database (TW-050).
