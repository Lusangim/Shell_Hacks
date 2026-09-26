---
name: gridlock-build
description: How the GridLock hackathon app (ShellHacks 2026, Sperry Tech challenge) is built, verified, judged and submitted — Claude sets up and launches one Codex lead that builds and judges the project with up to five sub-agents and delivers by Sat 09:30; Claude then reviews last and ships with the founder. Per-merge quick gate, gates, scope ladder, demo and Devpost. Use for any work in this repo.
---

# GridLock build — from approved plan to a submitted, demo-proof app

**This file is a router.** Detail lives in `references/` and the project's own files; open a reference
only when its step arrives. The founder's rules, `CLAUDE.md` and `AGENTS.md` win over anything here.
Codex reads this same skill at `.agents/skills/gridlock-build/`; where it says "agent tool" or "Opus",
a Codex session starts a sub-agent that reads the role file as its prompt and uses its own model.

| Need | Open |
|---|---|
| What we build, contracts, rules, commands, open questions, prior art | `SPEC.md` |
| Tasks (acceptance, verify, owner) · decisions, the Codex lead, lanes, gates, ladder | `tasks/todo.md` · `tasks/plan.md` |
| Never-touch, glossary, environment, verify recipe, lenses, traps | `PROJECT-PROFILE.md` |
| Live state of the pass | `reviews/2026-09-26-gridlock-build/TRACKER.md` |
| Standing bar for "done" | `references/definition-of-done.md` |
| Interface rules and audit thresholds | `references/ui-contract.md` (+ `house-patterns.md` from G1) |
| Coordination brief (Claude API, eval, cost) | `references/ai-brief.md` |
| Mission brief, sub-agent briefs, judge and agent prompts | `references/agent-prompts.md` |
| Review checklists (merges, gates, briefs, sanitizer) | `references/review-checklists.md` |
| Demo, Q&A, Devpost, fresh-clone checks | `references/ship-checklist.md` |
| Where each idea came from | `references/sources.md` |

## 0. Always true

- **Read the machine clock first** (`Get-Date`). The only fixed times: Codex delivers by **Sat 09:30 EDT**
  at the latest (earlier if it finishes); Devpost closes **Sun 11:00 EDT**; the founder submits by 10:30.
  There is no other schedule. Every recommendation is sized to the time left.
- Nothing outward without the founder: no push unless the founder says yes each time, no Devpost
  submission, no Claude API spend without a quoted cost, a ceiling and a yes, no download not on the
  approved list.
- Nothing invented: unknowns stay "unknown"; data is shown verbatim with document + page; estimates are
  ranges (or a stated reason) labelled "estimate"; AI text is labelled "AI-drafted"; contacts are
  organisations — never a person's name, email or phone.
- Public data only; nothing marked CEII. Secrets are never printed, logged, committed or handed to Codex.
- The founder's workflow vault is read-only; its skills are read by path. Nothing under
  `%USERPROFILE%\.codex\` is read.
- One term per concept (profile glossary). Refer to the founder as "the founder" / "they".
- State a concern once, with the number, then build. Ask only when an assumption would make the work
  unsafe or useless; otherwise proceed under the stated default and add the question to the list. The
  Codex lead cannot ask: it takes the safe default in `SPEC.md` § Boundaries and lists the question in
  `DELIVERY.md`.

## 1. Before any work — orient (2 minutes)

1. Clock → which phase are we in (setup, Codex run, delivery, final review, ship)? Is the hand-off or the
   T-2h point near? Go to §8.
2. Read `TRACKER.md` (trust it over memory): what is running, Codex session ids, last verify, next actions.
3. Pick the next unchecked task whose dependencies are checked (`tasks/todo.md`).
4. Load the skills the task's lane needs (`references/agent-prompts.md` § Skills per lane).

## 2. One task = one tested vertical slice (builders)

1. Re-read the task's acceptance and verify lines. Unclear → stop and report; do not guess.
2. **RED:** write the check first in the canonical suite for that surface; see it fail for the right
   reason. Bugs: reproduce in a test before touching code.
3. **GREEN:** the smallest change that passes; match the house patterns; no unrelated refactors.
4. **Local check:** compile + focused tests (+ the surface's e2e if the sandbox can run Chromium) on your
   port, with `GRIDLOCK_AI=off` and Python as `$env:GRIDLOCK_PY`.
5. **Definition of done** (`references/definition-of-done.md`), then one commit `<LANE>: T<n> <what>` on
   your branch and the report with before/after evidence.

Never weaken, skip or delete a check to get green. **Stop and report** when a fix adds new errors, the
same error survives three attempts, a fix needs a contract or architecture change, a dependency is
missing, or the task needs a decision the spec does not cover.

## 3. Who does what

- **Claude (this repo's session) before the launch:** setup and the approved downloads (T0.0–T0.1), pass
  folder and launch scripts (T0.5), proof that Codex can fan out and test in its sandbox (T0.6), the
  design round with the founder (T1.0), the mission brief (T0.8), the launch (T0.9). While Codex runs,
  Claude drafts the pitch (T5.0), runs no agents and never polls.
- **The Codex lead** (`gpt-6-sol`, `model_reasoning_effort="high"`, ChatGPT subscription) runs the build
  from `MISSION.md`: it assigns tasks to **up to five sub-agents at once** (founder's choice), reviews each
  result against its brief (`references/review-checklists.md` §A + the lane's section + §E), runs the
  quick gate, merges, runs VERIFY at every gate, runs every gate reviewer and judging round as fresh
  sub-agents on frozen copies, loops on the findings, and delivers (`DELIVERY.md`) by the hand-off.
- **Claude after delivery — the final reviewer:** judges with its own Opus agents (at most three at a
  time), fixes what it judges worth fixing, sends a large batch of corrections back to Codex **with no
  Codex judging loop**, judges again, then ships with the founder.
- Each build lane: its own worktree, branch `wt/<lane>`, port and **exclusive files** (`tasks/plan.md` §
  Lanes). A change needed elsewhere is an exact patch "For <lane>" in the report; the lead reassigns it.
- Checkpoint (a tracker line: machine time, commit, test totals, what runs) at every merge and gate.
  After a usage-limit stop or crash: establish what is true, then resume (`codex exec resume <session id>`
  / resume the Claude agent) — never relaunch.

## 4. Merging — the quick gate every time

Before the lead merges a sub-agent's task (and before Claude commits a final-review fix): read the diff
against the brief with `references/review-checklists.md` §A (gating) + the lane's section (§B/§C DATA and
API, §D WEB) + §E; confirm the evidence (the check failed before, passes after); run
`scripts\quick-gate.ps1` on the branch (≤ 5 min: compileall · pytest · e2e smoke 1440 light · console
errors · axe default). Red or a CRITICAL/HIGH finding → back to the builder with the exact failure (a
repair brief follows §K). Green → merge, tick the task, one tracker line with totals. Watch §L.

## 5. Gates — nothing advances past a red gate

| Gate | Proof |
|---|---|
| Go | The founder's explicit "go" (hedges are not a go) |
| Launch | T0.0–T0.8 done; Codex fan-out proven or the founder's fallback chosen; mission brief reviewed |
| G1a / G1 / G2 / G3 | `VERIFY.cmd` full matrix on `main`, quiet machine, passing totals ≥ baseline, gate reviewers' CRITICAL/HIGH closed, tracker updated |
| G4 judged | Every Codex judge "material improvement: no", or only founder decisions / external dependencies left — say which |
| Delivery | At G4 or the hand-off, whichever comes first, after the delivery judging round: `DELIVERY.md`, tag `delivered`, VERIFY summary |
| Final review | Claude's judges "no" or only founder decisions left; corrections merged; VERIFY green |
| G5 ship-ready | `references/ship-checklist.md` all green |

## 6. Verify — the project's recipe, never the demo server

`VERIFY.cmd` (recipe in `PROJECT-PROFILE.md`). Full runs on a quiet machine (no sub-agents building). Read
the summary file, not the last console line. Fewer passing checks than the baseline is a finding; skips
only via the named allow-list. A failure under load is re-run three times quietly; a repeat is a defect.
Classify every red line (defect · stale assertion · flake · environment) and name the owning lane.

## 7. Judges — different lenses, frozen copies, measured evidence

Lenses: `PROJECT-PROFILE.md` § Auditor lenses; role files in `.claude/agents/`. **During the build** the
lead runs them as fresh sub-agents: domain spot-check at G2 (T2.11); round 1 at G3 (domain expert ·
first-week user + design · reliability + security); round 2 (business / hackathon fit · change-reviewer
on every user-facing word · accessibility); a delivery round 30 minutes before the hand-off on whatever is
built. **After delivery** Claude runs the same lenses on Opus (F2–F5). Judges change nothing, report only
reproduced or line-cited findings, say what is genuinely good, and end with **material improvement still
available: yes / no**. During the build, corrections go to the owning lane → quick gate → merge → VERIFY →
smaller confirmation round. After delivery, Claude fixes or routes a batch to Codex with no judging loop.

## 8. Hand-off, scope ladder and the T-2h protocol

The lead reads the clock at every merge. **30 minutes before the hand-off** it starts no new build task,
parks what is in flight, runs the delivery judging round, fixes the P0/P1 findings that fit, runs VERIFY
and delivers. Behind: cut in order from `tasks/plan.md` § Scope ladder (cut first = 1); the founder
decides, and while they are away the unfinished feature is hidden from the demo path (never deleted) and
listed in `DELIVERY.md`. **At Sun 09:00 (T-2h):** list done / not done; each open item is cut from the
demo, stubbed honestly, or finished only if < 30 minutes remain. A working plain demo beats a broken
polished one; never cut the "never cut" line.

## 9. Ship

`references/ship-checklist.md`: docs made true by a scripted walk, Q&A crib, screenshot fallback,
presentation, Devpost (drafted early), fresh-clone rehearsal outside OneDrive, public-repo scrub, three
timed rehearsals. The founder submits. Only the founder.

## 10. Close out — lessons in their one home

Tracker final state → project lessons (from `DELIVERY.md`, `FINAL-REVIEW.md` and the tracker) into
`PROJECT-PROFILE.md` § Known traps (one dated line each) → founder preferences into memory → update this
skill in place if a step was wrong (edit, never stack) and re-mirror it to `.agents/skills/`. The
founder's vault is read-only from here: lessons for it go in a note for the founder.
