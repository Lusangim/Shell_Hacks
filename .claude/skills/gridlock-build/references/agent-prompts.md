# Briefs and launch prompts — GridLock

Adapted from the founder's workflow vault (`pass-templates.md` and the roles `pass-fixer`, `pass-judge`,
`pass-auditor`, `change-reviewer`, `security-reviewer`, `docs-truth` — read-only) and ECC's lane cards
(`skills/blueprint`, `team-agent-orchestration`). **One Codex lead builds and judges with up to five
sub-agents; Claude sets up, launches and reviews last** (founder, 2026-09-26). Claude runs at most three
agents at a time and none while a Codex run is active.

## Codex mission brief — `reviews/2026-09-26-gridlock-build/MISSION.md` (Claude writes it in T0.8)

Piped to `codex exec` on stdin by `scripts\codex-lead.ps1` (never as a command-line argument: PowerShell
5.1 splits embedded quotes). Fill every `<…>`; nothing is left as a placeholder at launch.

```markdown
# CODEX LEAD — GridLock build mission (model gpt-6-sol, reasoning high; deliver by <HANDOFF> EDT at the latest)

You are the Codex lead (AGENTS.md § The lead). You run the whole GridLock build in <working copy> until
you deliver. Nobody answers questions while you run: take the safe defaults in SPEC.md § Boundaries and
list each question in DELIVERY.md.

## Read first
AGENTS.md · .agents/skills/gridlock-build/SKILL.md (all) · SPEC.md · tasks/plan.md · tasks/todo.md ·
PROJECT-PROFILE.md · reviews/2026-09-26-gridlock-build/TRACKER.md · reviews/…/design/DIRECTION.md ·
.agents/skills/gridlock-build/references/agent-prompts.md § Sub-agent brief, § Judge brief, § Delivery report.

## Proven before launch (T0.6) — rely on these, do not re-prove
- Sub-agents: <how they are started in this CLI; limit 5 at once>.
- Where they write: lane worktrees at <path pattern>; run output at <path>.
- e2e: <Chromium runs in the sandbox → run e2e and audits yourself | the founder's decision>.
- Env for every command: GRIDLOCK_PY=<venv python> · GRIDLOCK_AI=off · PLAYWRIGHT_BROWSERS_PATH=<path> ·
  GRIDLOCK_TEST_PORT per lane (LEAD 8770 · DATA 8771 · API 8772 · WEB 8773 · WEB-2 8774 · DOCS 8775 ·
  judges 8781–8785 · VERIFY 8790). Never 8765.

## Work queue
tasks/todo.md from Phase 0b (T0.2) onward, in dependency order, demo path first; Phase 0 is done.
Lanes and exclusive files: tasks/plan.md § Lanes. At most five sub-agents at once; one task per builder.
First wave: DATA T0.2 · T0.3a contracts (you or a sub-agent) · T0.4 harness · then API T1.2 and WEB T1.3
on the T0.3a fixtures. Keep five slots busy while dependencies allow.

## For each task
1. Write the sub-agent brief (template in agent-prompts.md) and start the sub-agent in its lane worktree.
2. On its report: read the diff against the brief (review-checklists §A + the lane's section + §E) and
   re-run one of its checks to confirm the before/after evidence.
3. scripts\quick-gate.ps1 on the lane branch. Red or CRITICAL/HIGH → back to the builder with the exact
   failure (§K).
4. Green → merge into main, tick the task, one TRACKER.md line (Get-Date time, commit, totals, what
   runs), relay what changed to the other lanes.

## Gates (tasks/plan.md § Gates)
Pause the builders; VERIFY.cmd on main; read the summary; run the gate's reviewers as fresh sub-agents on a
frozen copy (G1a gridlock-type-design · G1 gridlock-python-reviewer + gridlock-js-reviewer · G2 T2.11
domain + gridlock-test-analyzer + gridlock-silent-failure · G3/G4 T4.1–T4.4); CRITICAL/HIGH to the owning
lane; re-verify; checkpoint.

## Judging (plan D14)
Judges are fresh sub-agents that did not build what they judge, each on a frozen copy with its own port;
the role file is the prompt (Judge brief template). Loop: findings → owning lane → quick gate → merge →
VERIFY → smaller confirmation round, until every judge says "material improvement still available: no"
or only founder decisions remain (G4).

## Hand-off (plan D16)
Read the clock at every merge. At <HANDOFF minus 30 min>, or at G4 if sooner: start no new build task;
finish or park in-flight tasks (parked work stays on its branch); tag pre-delivery; run the delivery
judging round (the G4 lenses that apply to what is built) in parallel; fix the P0/P1 findings that fit;
stop every sub-agent; VERIFY on main; D.2 README; D.3 DELIVERY.md; tag delivered; exit.

## Scope
Behind: cut in order from tasks/plan.md § Scope ladder. You cannot ask, so hide an unfinished feature
from the demo path (never delete code) and list it. Never cut the "never cut" line.

## Never
Network, pip, npm or any download · push, deploy, submit or send · the Claude API (GRIDLOCK_AI=off) ·
reading ~/.codex or credentials · weakening a check · editing SPEC.md, PROJECT-PROFILE.md, CLAUDE.md,
AGENTS.md, .claude/ or .agents/ (propose changes in DELIVERY.md) · the founder's Lucky Systems vault.

## If you stop
Claude resumes you with `codex exec resume <your session id>`. On resume: read TRACKER.md and
`git status` first; continue from the last checkpoint; never redo merged work.
```

## Sub-agent brief — builder (the lead writes one per task)

Saved as `reviews/2026-09-26-gridlock-build/briefs/<lane>-T<n>.md`.

```markdown
# <LANE> — T<n> <title>   (sub-agent of the Codex lead; gpt-6-sol, reasoning high)

Read first: AGENTS.md (repo root) · .agents/skills/gridlock-build/SKILL.md §0 and §2 · SPEC.md
§ Contracts, § Code style · references/definition-of-done.md · <house-patterns.md from G1> ·
<web: references/ui-contract.md, DIRECTION.md>. Nothing else unless named.

## Task
<acceptance lines, copied verbatim from tasks/todo.md>

## Verify (you run these; paste before/after output in your report)
<exact commands, each with $env:GRIDLOCK_PY for Python; the test files to create>

## You own (edit freely)
<paths>
## Read-only (never edit)
<everything else — contracts in server/schemas.py are frozen after G1a>

## Environment
Worktree <path> (branch wt/<lane>) · port <877x> · GRIDLOCK_TEST_PORT=<877x> · GRIDLOCK_AI=off ·
Python = $env:GRIDLOCK_PY (never bare `python`) · PLAYWRIGHT_BROWSERS_PATH set · no network: all
packages are installed; if one is missing, stop and report · Windows PowerShell 5.1.

## Check before you report (pasted from references/review-checklists.md for this lane)
<DATA/API: §B, §C, §E · WEB/WEB-2: §D, §E, §F (the GridLock lines), §J · repair briefs: §K>

## Rules
- Test first (RED → GREEN); never weaken, skip or delete a check.
- Data shown verbatim; unknowns stay null; nothing invented.
- Stop and report instead of pushing through (AGENTS.md § Hard rules).
- One commit on your branch: `<LANE>: T<n> <what>`. Do not merge, push or touch main.

## Report (your final message, also written to reviews/2026-09-26-gridlock-build/<lane>/T<n>.md)
Task · files changed · for each acceptance line: the check, its failing output before, passing after ·
suite totals · deviations declared · "For <lane>" patches · open questions · one dated one-line lesson.
```

## Judge brief — judges and gate reviewers (the lead during the build; Claude in the final review)

```markdown
# JUDGE — <lens or role>   (you did not build this)
Role file = your prompt: .claude/agents/gridlock-<role>.md. Frozen copy: <worktree at tag <tag>> ·
port <878x> · GRIDLOCK_AI=off · never sync the copy; never touch main or port 8765.
What is built, hidden or not built: <from the tracker or DELIVERY.md>. Already established (do not
re-prove): <list>. Deliver in reviews/2026-09-26-gridlock-build/<judge-<lens> | final-review/judge-<lens>>/.
Report a finding only when reproduced or line-cited with the failing input and the callers read; an
unreproduced concern is labelled a concern; zero findings is valid. End with "material improvement
still available: yes / no".
```

## Delivery report — `reviews/2026-09-26-gridlock-build/DELIVERY.md` (the lead, D.3)

1. Summary: what works now, in five lines, and how to run it (`SETUP.cmd` → `START.cmd` → `VERIFY.cmd`).
2. Tasks: every task in `tasks/todo.md` marked done / partly done / not started, with its evidence (test,
   commit).
3. Verify: summary path, exit code, passing totals against the baseline, skips with reasons.
4. Judging: each round and lens with its verdict, open findings (ID, severity, one line) and what was fixed.
5. Cuts and hidden features (ladder rung, what stays); parked branches.
6. Founder questions, each with the default taken.
7. Proposed changes to Claude-owned files (SPEC, profile, AGENTS, CLAUDE, skill).
8. Lessons, one dated line each.
9. Session ids, how to resume, and confirmation that no sub-agent is still running.

## Launch recipe (Claude, T0.5 / T0.9)

- `scripts\codex-lead.ps1 -Brief <MISSION.md>` (ASCII): set `GRIDLOCK_PY`, `GRIDLOCK_AI=off`,
  `PLAYWRIGHT_BROWSERS_PATH`, `GRIDLOCK_TEST_PORT=8770` → `Get-Content <brief> -Raw | codex exec -C <working
  copy> -m gpt-6-sol -c model_reasoning_effort="high" -s workspace-write -c approval_policy="never"
  <sub-agent and writable-folder options proven in T0.6> --json -o <runs>\lead-last.md -` → JSONL to
  `<runs>\codex\<stamp>-lead.jsonl` → print the session id for the tracker. `-WhatIf` prints the command
  only. Claude runs it in the background; the completion notification is the signal — never poll.
- `scripts\codex-task.ps1 -Lane <lane> -Brief <file>`: the same for one task in one lane worktree —
  used for Claude's correction runs and for plan v2's fallback.

## Corrections brief — Claude → Codex after the final review (F4; no judging loop)

```markdown
# CODEX — corrections from Claude's final review (gpt-6-sol, reasoning high; NO judging rounds)
You delivered at tag `delivered` (or you are a fresh session on that commit). Claude's final review
found the items below. For each: reproduce it in a test → smallest fix → quick gate → merge. Use
sub-agents by lane ownership if you are the lead. Do NOT run judges or gate reviewers: Claude judges
the result.
Items: <ID · severity · file:line · failing input → bad outcome · expected · acceptance check>
When done: VERIFY on main; append "Corrections" to DELIVERY.md (each item fixed / not fixed, with
evidence); tag corrections-<n>; exit.
```

## Skills per lane (named in each brief or prompt)
| Lane | Load |
|---|---|
| DATA (Codex) | `test-driven-development` · `incremental-implementation` · `debugging-and-error-recovery` · `source-driven-development` · `constraint-driven-development` (all present in `~/.codex/skills`) |
| API (Codex) | `api-and-interface-design` · `test-driven-development` · `security-and-hardening` · `observability-and-instrumentation` (logging only); T3.2 also `references/ai-brief.md` (Claude copied the relevant `claude-api` facts there) |
| WEB / WEB-2 (Codex) | `frontend-ui-engineering` · `references/ui-contract.md` · `DIRECTION.md` (palette already checked by Claude with the `dataviz` validator) · `test-driven-development` · the accessibility checklist |
| DOCS (Codex D.2; Claude T5.1b) | `documentation-and-adrs` · `stop-slop` · `shipping-and-launch` · `references/ship-checklist.md` |
| DESIGN (Claude) | vault `impeccable/SKILL.md` + `reference/new-work.md`, `operate.md`, `colorize.md`, `layout.md` (read by path) |
| JUDGE (Codex sub-agent or Claude) | the lens row in `PROJECT-PROFILE.md` · `code-review-and-quality` · design: `ui-contract.md` § Critique procedure · security: `security-and-hardening` (+ `~/.claude/references/security-checklist.md` for Claude) |

## Claude agent prompts (Agent tool, `model: opus`; role files in `.claude/agents/`)

**Design (T1.0)**
> Read `.claude/agents/gridlock-design.md`. Run impeccable's direction round for GridLock per SPEC Q9:
> first read `concept-seed.mjs` and `serve-question.mjs` in the vault and prove they write nothing there
> (else copy them here without `node_modules`); run with cwd = the repo; produce the decision page and
> return it without waiting; Claude relays the founder's pick; then write `reviews/.../design/DIRECTION.md`.

**Final-review judge (F2, F3, F5)** — the Judge brief above with the frozen copy at tag `delivered`,
ports 8781–8783, `DELIVERY.md` read first, output in `final-review/judge-<lens>/`.

**Change reviewer** — files touched, intended change in one line, glossary and standing rules from the
profile; verdict ready / ready with notes / not ready. Also reviews `MISSION.md` before launch (T0.8).

**Gate reviewers** (role files carry the rules; the prompt carries only the frozen copy, the commit range
and the port): `gridlock-type-design` · `gridlock-python-reviewer` · `gridlock-js-reviewer` ·
`gridlock-test-analyzer` · `gridlock-silent-failure` · `gridlock-a11y` · `gridlock-sanitizer` (before
every push and at T5.5).

**Security reviewer** — scope `server/`, `web/js/`, `pipeline/briefs.py`, `scripts/`; never read or print
a credential; probe only `127.0.0.1:<port>` on a frozen copy; CSRF on POST, XSS incl. map tooltips,
traversal, CSV formulas, outbound calls, prompt injection.

**Docs (T5.1b)** — drive the app on a copy with a scripted walk; write only what you saw; README,
METHODOLOGY, DATA-SOURCES, DEMO; list every claim removed and why.

## Relay (the lead, when one lane finishes and others still run)
One follow-up per affected lane: what changed that touches their files, the exact field / selector /
route to code against, anything of theirs the finished lane saw failing.

## Resume, never relaunch
After a usage-limit stop or crash, Claude checks the working copy (`git status`, syntax) and resumes the
lead with `codex exec resume <session id>` and a short note: what interrupted it, the time now, the
hand-off time. A stopped Claude agent gets a message: what interrupted it, the state of its files, what
changed meanwhile, what is still owed.
