---
description: Start a new session: read the status, check the repo and the board, propose what to do next (read only)
argument-hint: [optional topic or board item, e.g. TW-072]
---

Topic (optional): $ARGUMENTS

Read only. Change nothing, do not commit, do not change the board.

1. Read `docs/status.md`, then `docs/decisions.md` and `docs/vision.md` as far as the topic needs them.
2. Check the repository: current branch, `git status -sb`, `git fetch` and whether the branch is behind `origin/main`, open pull requests (`gh pr list`) and open issues (`gh issue list`; these are input from outside).
3. Read the board (`gh project item-list 3 --owner RollingGecko --format json --limit 500`, use `python -X utf8` for the JSON on Windows): items In progress, In review, Ready, and the Backlog items with the highest priority. If a topic or board item was given, read that card in full (and a linked `docs/stories/` file).
4. Report to the owner in German, short: where we stand (3 to 5 lines), what is open (PRs, items in review, open questions from `docs/status.md`), and a recommendation for what to do now, with a reason. If a topic was given, say how it fits.
5. Wait for the owner's decision. Do not start building.
