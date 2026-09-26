# Pass brief — GridLock build (2026-09-26)

**Goal:** the complete GridLock app per `SPEC.md` (plan v3), built and judged by one Codex lead with up to
five sub-agents, delivered by **Sat 2026-09-26 09:30 EDT** at the latest (earlier if it finishes), then
reviewed last by Claude. The founder and team review both results and decide the next round. Devpost
closes Sun 2026-09-27 11:00 EDT; the founder submits by 10:30.

**Working copy:** `%USERPROFILE%\dev\gridlock` (clone of the OneDrive repo; the OneDrive copy is left as it
is). Venv `%USERPROFILE%\dev\gridlock-venv`; Playwright browsers `%USERPROFILE%\dev\ms-playwright`; lane
worktrees `%USERPROFILE%\dev\gridlock-wt\<lane>`; run output `%USERPROFILE%\dev\gridlock-runs`.

**Roles:** Claude — setup, design round, mission brief, launch, final review (`CLAUDE.md`). Codex lead —
build, gates, judging rounds, delivery (`AGENTS.md`, `MISSION.md`). Founder — go, design pick, decisions
listed in `DELIVERY.md` and `FINAL-REVIEW.md`, Devpost.

**Ownership, ports, gates, ladder:** `tasks/plan.md`. **Tasks:** `tasks/todo.md`. **State:** `TRACKER.md`.

**Files in this pass folder:** `TRACKER.md` · `MISSION.md` · `DELIVERY.md` (lead) · `FINAL-REVIEW.md`
(Claude) · `design/` (DIRECTION.md) · `research/` (prior art) · `briefs/` · `<lane>/T<n>.md` reports ·
`judge-<lens>/` · `final-review/` · `pitch/`.
