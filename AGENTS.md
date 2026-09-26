# AGENTS.md — GridLock (ShellHacks 2026, Sperry Tech challenge)

Codex works here in one of two roles; the first line of your brief names yours.
- **Codex lead:** one session (`gpt-6-sol`, reasoning high) launched by Claude with `MISSION.md`. It runs
  the whole build. It assigns tasks to up to five sub-agents at once, reviews and merges their work, runs
  the gates and every judging round, and delivers when the project is complete and judged (no time limit).
- **Sub-agent:** started by the lead with a self-contained brief, either as a **builder** (one task in one
  lane) or as a **judge / reviewer** (one lens or one checklist on a frozen copy).

The founder's standing rules in `~/.codex/AGENTS.md` apply; this file adds the project's.

## Read, in this order, and nothing else unless your brief names it
1. Your brief (the lead: `MISSION.md`; a sub-agent: the brief the lead gave you) — it is self-contained.
2. `.agents/skills/gridlock-build/SKILL.md` — the lead reads all of it; builders §0 and §2; judges §0 and §7.
3. `SPEC.md` § Contracts, § Overlap rules, § Code style · `.agents/skills/gridlock-build/references/definition-of-done.md`
   · `reviews/2026-09-26-gridlock-build/house-patterns.md` once it exists · for web work
   `references/ui-contract.md` and `DIRECTION.md` · judges and reviewers: their role file in `.claude/agents/`.

## Hard rules (everyone)
- Call Python only as `$env:GRIDLOCK_PY` (the Microsoft Store `python` cannot run in the sandbox).
  `GRIDLOCK_AI=off` always. Tests use `GRIDLOCK_TEST_PORT`; Playwright uses `PLAYWRIGHT_BROWSERS_PATH`.
  No network: if a package is missing, stop.
- Test first: write the failing check, then the smallest change that passes. Never weaken, skip or delete
  a check. Show data verbatim; unknowns stay null; never invent a value, name or contact.
- Never read `%USERPROFILE%\.codex\`, any `.env`, or anything that looks like a credential; never print
  environment variables. Never push, deploy, submit or send anything; never call the Claude API.
- Every command runs in a new shell: set `$env:GRIDLOCK_TEST_PORT` to your lane's port in each test or
  server command. Read text with `Get-Content -Encoding UTF8`; edit files with apply_patch, never
  `Set-Content`, `Out-File` or `>` on a repo text file. Stage by path; never `git add -A`, `git stash`,
  `git clean` or `git reset --hard`.
- **Stop and report** instead of pushing through when: a fix adds errors · the same error survives three
  tries · you need a contract/architecture change or another lane's file · a dependency is missing · the
  task needs a decision the spec does not cover. (For the lead this means park the task and continue —
  see § The lead.)

## Builders (sub-agents)
- Work only in your lane worktree — run every command there, never in `C:\Users\lucia\dev\gridlock` — and
  only on the files your brief says you own; everything else is read-only. `server/schemas.py` and
  `contracts/` are frozen after G1a.
- One commit on your lane branch: `<LANE>: T<n> <what>`. Never merge, push, or touch `main`.
- Report (final message, also saved to `reviews/2026-09-26-gridlock-build/<lane>/T<n>.md`): task · files
  changed · each acceptance line with its check, the failing output before and the passing output after ·
  suite totals · declared deviations · "For <lane>" patches · open questions · one dated one-line lesson.
  Report only what you ran.

## Judges and reviewers (sub-agents)
- Your role file in `.claude/agents/` is your prompt; where it names Claude as the launcher, the lead
  launched you. You did not build what you judge. Work on the frozen copy and port your brief gives you;
  change no product code; write only in your folder in the pass. A judgment ends with "material
  improvement still available: yes / no".

## The lead
- Follow `MISSION.md`. At most five sub-agents at once. Review every result against its brief, run the
  quick gate, merge into `main`, tick the task, and write a tracker line in `TRACKER.md` (machine time,
  commit, totals, what runs). Your context will compact during a long run: the tracker and
  `tasks/todo.md` are your memory.
- **Your run ends when your turn ends, and that kills every sub-agent: never end your turn before the
  `delivered` tag exists.** "Stop and report" means, for you: park the blocked task, record it in
  `TRACKER.md` and `DELIVERY.md`, and continue. Wait on sub-agents with a timeout of at most 10 minutes,
  then `Get-Date` and a tracker line. After a context compaction, re-read `MISSION.md` and `TRACKER.md`.
- No time limit: deliver when G4 passes (VERIFY green, sanitizer, README, `DELIVERY.md`, tag
  `delivered`), after stopping every server and browser started during the run. Rewrite `DELIVERY.md` at
  every gate from G1a on.
- You cannot ask the founder: take the safe default in `SPEC.md` § Boundaries and list the question in
  `DELIVERY.md`. Never wait idle for an answer.

## Windows notes
PowerShell 5.1: no `&&`; quote paths with spaces; `.ps1`/`.cmd` stay ASCII with CRLF; pass long text to
native tools through files, not arguments.
