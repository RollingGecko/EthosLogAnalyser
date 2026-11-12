# Skills

The plugin **agent-skills** (marketplace `addy-agent-skills`, version 0.6.15) is installed for this project
(`.claude/settings.json`). The rules in `CLAUDE.md` always take priority over a skill.

## Active skills
| Area | Skill | Use for |
|---|---|---|
| Test-driven development | `test-driven-development` | tests first for import, duplicate detection, analysis logic, parser; bug fixes with a failing test first |
| Planning, task breakdown | `planning-and-task-breakdown`, `incremental-implementation` | split an approved story into small steps; build in thin slices |
| Git workflow | `git-workflow-and-versioning` | branches, small commits, PR texts. Its tagging and push advice does **not** apply |
| Code review, quality | `code-review-and-quality` (agent `code-reviewer`) | one review pass before every PR |
| Performance | `performance-optimization` | measure first (import, database, analysis); state the run time in the PR |

Further skills may be used when they fit (e.g. `debugging-and-error-recovery`, `documentation-and-adrs` for
`decisions.md`, `interview-me`, `idea-refine`).

## Not used
- Web specific: `browser-testing-with-devtools`, `frontend-ui-engineering`, agent `web-performance-auditor`, web parts of
  `performance-optimization` (Core Web Vitals, bundles). This is a Tkinter desktop app.
- Commands `/ship` (go/no-go launch review for deployments) and `/build auto` (autonomous plan, needs `SPEC.md`).
- Skills for services/web security and deployment (`ci-cd-and-automation`, `shipping-and-launch`, `observability-and-instrumentation`)
  only on explicit request; releases are the owner's job.

## Rules against conflicts
- No skill pushes, merges, tags or releases. Commits only on the working branch, PRs are opened for the owner.
- No skill creates GitHub issues; tasks go on the board.
- `/plan` would write `tasks/plan.md` and `tasks/todo.md`: tasks are tracked on the board instead (the planning skill allows
  an external tracker named in `CLAUDE.md`). Do not create `tasks/todo.md`.
- `/spec` would write `SPEC.md`: not used, the story with acceptance criteria (board item, optionally `docs/stories/`) is the specification.
- `/build` only in the single-task mode, with a commit on the branch.
- `/test` and `/review` are fine.

## Own commands next to the plugin
`/start` begins a new session (counterpart of `/handoff`). `/story` creates the story, then the planning skill splits it into steps. `/ux-review`, `/release`, `/handoff` have no
equivalent in the plugin. Own commands take priority.

## Context use
Check with `/context` how much context the plugin and the loaded skills take. Skills load only when invoked; if the context
is tight, start a new session after `/handoff`.
