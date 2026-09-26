# Briefs and launch prompts — GridLock

Adapted from the founder's workflow vault (`pass-templates.md` and the roles `pass-fixer`, `pass-judge`,
`pass-auditor`, `change-reviewer`, `security-reviewer`, `docs-truth` — read-only) and ECC's lane cards
(`skills/blueprint`, `team-agent-orchestration`). **One Codex lead builds and judges with up to five
sub-agents; Claude sets up, launches and reviews last** (founder, 2026-09-26). Claude runs at most three
agents at a time and none while a Codex run is active.

## Codex mission brief — `reviews/2026-09-26-gridlock-build/MISSION.md` (Claude writes it in T0.8)

Handed to `codex exec` as a stdin file handle by `scripts\codex-lead.ps1` (never as a command-line
argument or a piped string: PowerShell 5.1 splits embedded quotes and re-encodes piped text).

**The template is the live brief itself:** `reviews/2026-09-26-gridlock-build/MISSION.md` (reviewed by a
gridlock-reviewer agent before launch; 5 HIGH + 7 MEDIUM findings applied). For another run, copy it and
update the proven facts, the task queue and the dates. Its sections, which every mission keeps:
- **Your run:** the run ends when the lead's turn ends and that kills every sub-agent, so the lead never
  ends its turn before `delivered`; "stop and report" means park and continue; wait on sub-agents at most
  10 minutes at a time, then `Get-Date` and a tracker line; re-read the mission after a compaction;
  rewrite `DELIVERY.md` at every gate.
- **Read first**, with the PowerShell 5.1 UTF-8 rule (`Get-Content -Encoding UTF8`; edit with apply_patch).
- **Proven before launch** (T0.6 facts: spawn tool, shared sandbox, worktrees, git folder, runs, e2e).
- **Environment:** every command is a new shell, so each test or server command sets its own port; the
  port table; no network; git-ignored inputs only in the main copy, by absolute path.
- **Work queue:** first wave, wave-1 ownership fixes, second worktrees to keep five slots busy.
- **For each task:** brief → worktree → review → quick gate → merge (main HEAD checked, staged by path) →
  tick → tracker → relay; Claude's `pitch/` and `final-review/` untouched.
- **Gates:** no new builder, in-flight builders finish, VERIFY when none builds, reviewers on a frozen copy
  while builders resume; frozen copies named per round and HEAD-checked; JUDGMENT.md copied to main.
- **Judging, Delivery (at G4, no time limit), Scope, Never, If you stop.**

## Sub-agent brief — builder (the lead writes one per task)

Saved as `reviews/2026-09-26-gridlock-build/briefs/<lane>-T<n>.md`.

```markdown
# <LANE> — T<n> <title>   (sub-agent of the Codex lead; gpt-6-sol, reasoning high)

Read first: AGENTS.md (repo root) · .agents/skills/gridlock-build/SKILL.md §0 and §2 · SPEC.md
§ Contracts, § Code style · references/definition-of-done.md · <from G1: reviews/2026-09-26-gridlock-build/house-patterns.md> ·
<web: references/ui-contract.md, reviews/2026-09-26-gridlock-build/design/DIRECTION.md>. Nothing else unless named.
Read text with `Get-Content -Encoding UTF8`; edit files with apply_patch.

## Task
<acceptance lines, copied verbatim from tasks/todo.md>

## Verify (you run these; paste before/after output in your report)
<exact commands, each with $env:GRIDLOCK_PY for Python; the test files to create>

## You own (edit freely)
<paths>
## Read-only (never edit)
<everything else — contracts in server/schemas.py are frozen after G1a>

## Environment
Worktree <path> (branch wt/<lane>) — run every command there, never in C:\Users\lucia\dev\gridlock ·
port <877x>: every command is a new shell, so begin each test or server command with
`$env:GRIDLOCK_TEST_PORT='<877x>';` · GRIDLOCK_AI=off · Python = $env:GRIDLOCK_PY (never bare `python`) ·
PLAYWRIGHT_BROWSERS_PATH set · no network: all packages are installed; if one is missing, stop and report ·
git-ignored inputs you need: <absolute path in the main copy, read-only> · Windows PowerShell 5.1.

## Check before you report (pasted from references/review-checklists.md for this lane)
<DATA/API: §B, §C, §E · WEB/WEB-2: §D, §E, §F (the GridLock lines), §J · repair briefs: §K>

## Rules
- Test first (RED → GREEN); never weaken, skip or delete a check.
- Data shown verbatim; unknowns stay null; nothing invented.
- Stop and report instead of pushing through (AGENTS.md § Hard rules).
- Never print environment variables. Stage by path; never `git add -A`, `git stash`, `git clean` or
  `git reset --hard`.
- One commit on your branch: `<LANE>: T<n> <what>`. Do not merge, push or touch main.

## Report (your final message, also written to reviews/2026-09-26-gridlock-build/<lane>/T<n>.md)
Task · files changed · for each acceptance line: the check, its failing output before, passing after ·
suite totals · deviations declared · "For <lane>" patches · open questions · one dated one-line lesson.
```

## Judge brief — judges and gate reviewers (the lead during the build; Claude in the final review)

```markdown
# JUDGE — <lens or role>   (you did not build this)
Role file = your prompt: .claude/agents/gridlock-<role>.md. Frozen copy: <gridlock-wt\judge-<lens>-<round>
at commit <sha> — a new name every round; its HEAD checked before you start> · port <878x> (set it in
every command) · GRIDLOCK_AI=off · never sync the copy; never touch main or port 8765; never print
environment variables.
What is built, hidden or not built: <from the tracker or DELIVERY.md>. Already established (do not
re-prove): <list>. Deliver in reviews/2026-09-26-gridlock-build/<judge-<lens> | final-review/judge-<lens>>/.
Report a finding only when reproduced or line-cited with the failing input and the callers read; an
unreproduced concern is labelled a concern; zero findings is valid. End with "material improvement
still available: yes / no".
```

## Delivery report — `reviews/2026-09-26-gridlock-build/DELIVERY.md` (the lead: rewritten at every gate from G1a, final at D.3)

0. Status line: "in progress (last gate <gN>, <time>)" or "delivered (tag `delivered`, <time>)".
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
  `PLAYWRIGHT_BROWSERS_PATH`, `GRIDLOCK_TEST_PORT=8770`; **remove every `ANTHROPIC_*`, `CLAUDE_*`,
  `CLAUDECODE` and `USE_*OAUTH` variable** (Codex must never inherit the Claude session's credentials) →
  `codex exec -C <working copy> -m gpt-6-sol -c model_reasoning_effort=high -s workspace-write
  -c approval_policy=never --add-dir <worktrees> --add-dir <runs> --add-dir <git folder>
  --enable prevent_idle_sleep --json -o <runs>\lead-last.md -` with the brief as the stdin file → JSONL to
  `<runs>\codex\<stamp>-lead.jsonl` → wait on the Codex process only (not its descendants) → print the
  session id for the tracker. `-WhatIf` prints the command only. Claude runs it in the background; the
  completion notification is the signal — never poll.
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
| DATA (Codex) | This repo's `SKILL.md` §2, `definition-of-done.md`, `review-checklists.md` §B, §C, §E. **Codex loads no skills from `%USERPROFILE%\.codex\` in this project** (the founder's rule: nothing under `.codex` is read). |
| API (Codex) | The same, plus `SPEC.md` § Contracts; T3.2 also `references/ai-brief.md` (a fake client only) |
| WEB / WEB-2 (Codex) | `references/ui-contract.md` · `design/DIRECTION.md` (palette already checked by Claude) · `review-checklists.md` §D, §E, §F, §J |
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
lead with `scripts\codex-lead.ps1 -ResumeId <session id> -Brief <note>`: what interrupted it and the
time now. A stopped Claude agent gets a message: what interrupted it, the state of its files, what
changed meanwhile, what is still owed.
