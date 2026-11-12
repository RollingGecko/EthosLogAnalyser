---
description: Turn an idea into a story (product owner), then optionally add it to the board
argument-hint: <idea>
---

Idea: $ARGUMENTS

Act as the product owner (use the `product-owner` agent, or its rules from `.claude/agents/product-owner.md`).

1. Read `docs/vision.md`, `docs/decisions.md`, `docs/status.md`. Check whether the idea is already on the board or was decided against (`gh project item-list 3 --owner RollingGecko --format json --limit 500`).
2. Ask up to 3 questions, each with a recommendation, and wait for the answers (in German, with the owner). Skip questions if the idea is clear.
3. Write the story in German: "Als ... möchte ich ..., damit ...", acceptance criteria as Gegeben/Wenn/Dann, an INVEST check, and a cut into packages if it is not small.
4. Ask (in German) whether the story shall become a board item. Never create a GitHub issue.
5. Only after a yes: find the highest TW number on the board and take the next one, then
   - `gh project item-create 3 --owner RollingGecko --title "TW-nnn: <German title>" --body "<story, criteria>"`
   - set Status = Backlog and Priority (if the owner gave one) with `gh project item-edit` (ids from `gh project field-list 3 --owner RollingGecko --format json` and `gh project view 3 --owner RollingGecko --format json`; do not change columns or fields).
   - If the details are too long for the card, write `docs/stories/TW-nnn.md` (German) and link it in the card.
6. Report the board item in a few lines. Do not start building.
