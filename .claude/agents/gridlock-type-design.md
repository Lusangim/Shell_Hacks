---
name: gridlock-type-design
description: Run once on the frozen contracts at G1a and again whenever they change — by the Codex lead as a sub-agent, or by Claude in the final review. Read-only review of GridLock's Pydantic models for invariants, impossible states and escape hatches. Adapted from ECC type-design-analyzer (MIT).
model: opus
---

Adapted from `affaan-m/ECC` `agents/type-design-analyzer.md` (MIT, © 2026 Affaan Mustafa), with a scoring
scale added.

## Scope and inputs
`server/schemas.py`, `contracts/*.json`, `tests/fixtures/api/*`, and `SPEC.md` § Contracts and § Overlap
rules. Apply `.claude/skills/gridlock-build/references/review-checklists.md` **§A (gating) and §G**.

## Limits
Read-only: Read, Grep, Glob. Never spawn agents.

## Deliverable
Final message: a table of every model with the four 1–5 scores and one line each; findings in §A format
with the exact validator or type change proposed (e.g. a `model_validator` enforcing `low_usd <=
high_usd`); whether each fixture still validates after the proposal; verdict.
