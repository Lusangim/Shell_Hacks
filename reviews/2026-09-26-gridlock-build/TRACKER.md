# TRACKER — GridLock build (read first; trust over memory)

Hand-off: Codex lead delivers by **Sat 2026-09-26 09:30 EDT** at the latest (earlier if it finishes);
delivery judging round starts 30 minutes before. Deadline Sun 11:00 EDT; submit by 10:30.

## Now
- Phase: **setup (Claude)** — T0.0, T0.1 done; T0.5 scripts written; T0.6 Codex fan-out proof running;
  T1.0 design decision page shown to the founder, waiting for their pick; T0.8 mission brief next.
- Running: T0.6 proof (`gridlock-runs\t06\`); no Claude agents.
- Codex sessions: (none yet recorded)

## Decisions (founder, 2026-09-26)
- Operating model: one Codex lead (`gpt-6-sol`, high, subscription) with up to five sub-agents builds,
  gates and judges; Claude reviews last and routes large correction batches back without a Codex judging
  loop. No clock schedule.
- Downloads: "Approve all" — done in T0.1 (Chromium 1243 took 706 MB on disk; quoted ~150 MB).
- Design: impeccable's direction round. Decision page: OneDrive copy
  `reviews\2026-09-26-gridlock-build\design\decision-page.html`; roll seed `3a040ed5`; the roll's pick and
  the default if unanswered: **The Plan Sheet**; impeccable's pick: The System Wall Map.
- Hand-off: "Sat 9:30 am … it can finish earlier than that".

## Checkpoint log (machine time · commit · totals · note)
- 2026-09-26 03:29 · a65edf8 · — · session resumed after the previous one broke at a compaction (03:23)
- 2026-09-26 03:55 · — · — · venv `%USERPROFILE%\dev\gridlock-venv` (all imports ok); Chromium 1243 ok
- 2026-09-26 ~04:00 · 5c68c9f · — · plan v3 committed in the OneDrive repo (local only)
- 2026-09-26 ~04:05 · e9613f7 · — · working clone; T0.1 downloads, pinned requirements, prior-art research

## Environment facts
- The Claude app redirects `%LOCALAPPDATA%` writes into its package folder: nothing shared lives there.
- Codex CLI 0.157.1: `multi_agent` feature on by default; `--add-dir` for extra writable folders;
  `exec resume <id>` takes `-m`, `-c`, `--enable`, `--json`, `-o`, `-` (stdin).
- PowerShell 5.1 re-encodes piped strings: briefs go to Codex as a stdin file handle (`codex-lead.ps1`).

## Open founder questions
- Design pick (H0b).
- Prior-art candidates in `SPEC.md` § Prior art (none in the first Codex run unless added).

## Next actions
1. T0.6 result → record fan-out mechanism, writable folders, Chromium in the sandbox.
2. Founder's design pick → `DIRECTION.md` (design agent) → palette check with `dataviz`.
3. T0.8 mission brief → review → T0.9 launch.
