---
description: UX review of a board item or story by the ux-designer agent
argument-hint: <board item, e.g. TW-061>
---

Board item: $ARGUMENTS

1. Read the item (`gh project item-list 3 --owner RollingGecko --format json --limit 500`, find the title) and any linked `docs/stories/` file.
2. Delegate to the `ux-designer` agent with the item text. It checks user flow, empty/error/loading states, readability of charts and tables, consistency with `docs/design-system.md`, and feasibility in Tkinter; it may write a wireframe to `docs/wireframes/`.
3. Summarise the result for the owner in German: findings, recommendation per finding, wireframe path if any.
4. Ask whether the result shall be recorded: as a comment text in the board card (`gh project item-edit --id <DI_...> --body ...`, keep the existing text, add the review in German at the end) or as `docs/stories/<TW-nnn>.md`. Do it only after a yes.
5. Do not change the status of the item.
