---
description: List the board items of a release and propose a release goal (read only)
argument-hint: <release name, or a selection such as "Target date 2026-12" or "P1">
---

Selection: $ARGUMENTS

The board has no release field (fields: Status, Priority, Size, Workstream, Ticket type, Target date, Package, ...). Do not change the board.

1. Read the items (`gh project item-list 3 --owner RollingGecko --format json --limit 500`; use `python -X utf8` for the JSON on Windows).
2. Pick the items that match the selection. If there is no release field and the selection matches nothing, say so in German and propose options (e.g. use *Target date*, or the owner adds a single-select field "Release"); change nothing.
3. List the items by status and priority: title, status, size, dependencies you can see from the card texts.
4. Name a sensible release goal in two sentences, risks, and what is missing. Check `CHANGELOG.md` ("Unreleased") for what already is in.
5. Remind that tag and release are the owner's job (`docs/releasing.md`); never tag, release or merge.
