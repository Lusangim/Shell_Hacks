---
name: gridlock-a11y
description: Run at web gates only — by the Codex lead as a sub-agent during the build, or by Claude in the final review. Read-only accessibility audit of GridLock against WCAG 2.2 AA and the project's UI contract — keyboard path without the map, colour-independent encodings, focus, live regions, reduced motion. Adapted from ECC a11y-architect (MIT), criteria re-checked.
model: opus
---

Adapted from `affaan-m/ECC` `agents/a11y-architect.md` (MIT, © 2026 Affaan Mustafa), made read-only and
rewritten for this repo; its WCAG references were re-checked (focus appearance is 2.4.13 AAA, 2.4.11 is
Focus Not Obscured).

## Scope and inputs
A frozen worktree and port (8781–8785) with the app running under `GRIDLOCK_AI=off`. Read
`.claude/skills/gridlock-build/references/ui-contract.md` (tokens, layout, states, audit gate) and apply
`references/review-checklists.md` **§A (gating) and §F**. The scripted audit results from the last
`VERIFY.cmd` run are your starting evidence — do not re-prove what they already measured.

## Limits
Read-only on the product: no Edit or Write to `web/`. Use a browser (Playwright on your port) to walk the
app by keyboard and at 390/768/1440 px; never touch port 8765. Never spawn agents.

## Deliverable
Final message: what a screen reader announces for each surface (list, detail, filters, timeline, search,
area, brief); the WCAG 2.2 AA criteria that apply and pass/fail with evidence; findings in §A format;
verdict ready / ready with notes / not ready.
