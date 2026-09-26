# CLAUDE.md — GridLock (ShellHacks 2026, Sperry Tech challenge)

The Codex lead has **no time limit** (founder: "remove the time limit just let it work"): it delivers when
the project is complete and judged. Devpost closes **Sun 2026-09-27 11:00 EDT**; the founder submits by
10:30. Read the machine clock before planning anything.

**Workflow:** load the `gridlock-build` skill (`.claude/skills/gridlock-build/SKILL.md`) for any work here.
State lives in `reviews/2026-09-26-gridlock-build/TRACKER.md` — read it first and trust it over memory.
Spec `SPEC.md` · tasks `tasks/todo.md` · plan, the Codex lead, lanes, gates `tasks/plan.md` · profile `PROJECT-PROFILE.md`.

**Roles.** This Claude session sets up the working copy, the environment and the approved downloads. It
proves Codex can fan out in its sandbox, runs the design round with the founder, writes the mission brief
and launches the **Codex lead** (`scripts\codex-lead.ps1`; `gpt-6-sol` at high reasoning on the founder's
ChatGPT subscription, never an API key). The lead builds, gates and judges the whole project with up to
five Codex sub-agents, then delivers. Claude **reviews last**: it judges with Claude Opus agents, fixes
what is worth fixing, and sends a large batch of corrections back to Codex with no Codex judging loop,
then judges again. Claude runs at most three agents at a time and none while a Codex run is active. It
never polls.

**Never:** push, submit to Devpost, spend on the Claude API, or download anything without the founder's yes;
read `%USERPROFILE%\.codex\` or print any credential; edit the founder's workflow vault (read-only);
invent data; weaken a test; install into OneDrive or create tool state under `%LOCALAPPDATA%` (this app
redirects it; see the profile's Known traps). Unknowns stay visible placeholders.

**This machine:** Windows 11, PowerShell 5.1 (no `&&`; pass long prompts to native tools via stdin files,
never as arguments); write files with the Write tool; call Python by full path (`$env:GRIDLOCK_PY`);
long runs in the background — never poll; keep the laptop awake during unattended runs.
