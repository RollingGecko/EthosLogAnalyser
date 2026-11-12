# Decisions

Short records of decisions that shape the project. Format: decision, reason, date. Dates are as far as known from the
board and the history; "reason unknown" where it was not recorded.

## Workflow

### Board instead of issues for stories (2026-11-12)
- **Decision:** Stories, priority and release planning live only in the GitHub project "EthosLogAnalyzer Kanban Board"
  (project 3). GitHub issues are only for input from outside. Workflow with the agents, commands and skills in
  `CLAUDE.md`. The old package scheme (WP-nn, "start WP-nn") is replaced.
- **Reason:** One place for planning; issues stay a clean inbox for users' bug reports and feedback.

### Pull requests only, owner merges and tags (before 2026-10-23)
- **Decision:** Never push to `main`; the owner tests with the CI test EXE and merges every PR. Releases only by the
  owner's tag `vX.Y.Z`.
- **Reason:** The owner tests with real flight data on Windows and wants the final say. (Rule from the earlier `CLAUDE.md`.)

## Product

### Rebuild around a flight database (2026-10-25)
- **Decision:** The earlier state was a proof of concept; the app was rebuilt (concept of 2026-10-25, board item TW-034,
  implemented by TW-035 to TW-039).
- **Reason:** "The database becomes the basis for everything further."

### Database as a file (2026-10-25)
- **Decision:** One SQLite file (new, open, save as, empty with confirmation); the last loaded database opens at start;
  default `Documents\EthosLogAnalyser\flugbuch.db`. Raw logs are imported and kept in the database; originals stay untouched.
- **Reason:** A single copyable file; reproducible tests with an emptied database. Further reason unknown.

### Duplicates by content hash (2026-10-25)
- **Decision:** Identical content (SHA-256) is skipped; same aircraft and start time with different content is reported as
  "possible duplicate". **Reason:** reason unknown.

### One flight = one log file (2026-10-25)
- **Decision:** Each log file is one flight; logs that are not flights are imported and marked, switchable by click.
  **Reason:** reason unknown.

### Different sensors per aircraft (2026-10-25)
- **Decision:** Not every model has motor or flight battery data; flight detection uses the best available sensor and
  analyses adapt. **Reason:** The owner flies gliders and other aircraft as well, not only the Viper-Jet.

### Anomalies relative per aircraft (2026-10-25)
- **Decision:** Hints compare a flight with the median of all flights of the same aircraft (from five flights on) and
  with the flight itself; no fixed global limits. The receiver minimum voltage is the one fixed value, per aircraft, off by
  default. **Reason:** Aircraft differ too much for global limits.

### Logbook as the centre, statistics as a part (2026-10-25)
- **Decision:** The logbook is the start page. The former analysis pages became the statistics part with a shared filter
  (aircraft, year, month, date range). The filter replaces the earlier period and model filters. **Reason:** Neubau goal 3
  of the concept.

### Battery analysis marked experimental, no battery selection yet (2026-10-25)
- **Decision:** The statistics begin with a note that the area is experimental; battery selection is deliberately not
  built yet. **Reason:** The values are estimates and may change.

### Logbook simplified (2026-10-25)
- **Decision:** No charts and no "group by" in the logbook, instead tables per aircraft, year and month. **Reason:**
  "The screen is overloaded"; the filter covers grouping.

### Single flight only through the logbook (2026-10-26)
- **Decision:** No separate "single flight" tab; open by double-click, return with "< Logbook". **Reason:** The tab was
  never needed and used space.

### Charts and flight recorder are separate tabs (2026-10-28)
- **Decision:** Tabs *Charts* and *Flight recorder* of the single flight. **Reason:** reason unknown (the recorder has its
  own timeline and instruments; its position is shown as a line in the charts).

### Prepared values stored in the database (2026-10-25)
- **Decision:** Cross-flight values are computed on import and stored, not on every start. **Reason:** Start of the
  statistics fell from 2.9 s to 1.7 s (33 flights), 43 s to 4.1 s at about 1000 flights; database grew by about 47 kB per flight.

### Performance and small database as design goals (2026-10-25)
- **Decision:** No long computing times; the saved database file as small as possible (compact time series). **Reason:**
  Usability with large logbooks.

## Rejected / obsolete

### Pull request #14 (year/month) discarded (2026-10-25)
- **Decision:** Not to be taken up again. **Reason:** Covered by the rebuild (year/month selection is part of the shared
  filter); exact reason unknown.

### Packages WP-13 and WP-14 not continued (2026-10-25)
- **Decision:** Obsolete due to the rebuild. **Reason:** The rebuild replaced them.

### Receiver base current trend (TW-030) discarded
- **Decision:** Closed as "verworfen" on the board. **Reason:** reason unknown.
