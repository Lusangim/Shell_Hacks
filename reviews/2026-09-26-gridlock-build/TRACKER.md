# TRACKER — GridLock build (read first; trust over memory)

**No time limit for Codex** (founder, ~04:35: "remove the time limit just let it work"): the lead delivers
when G4 passes and rewrites `DELIVERY.md` at every gate. Deadline Sun 11:00 EDT; the founder submits by 10:30.

## Now
- Phase: **Codex build** — T0.0–T0.8 and T1.0 done (T0.7 skipped); T0.8 review "not ready" (5 HIGH,
  7 MEDIUM), all applied in 5db51e4; the founder stopped the confirmation round and said "just go"; the
  founder declined a judging-round cap ("no need for that"). **T0.9: Codex lead launched ~04:49 EDT.**
- Running: the Codex lead (`scripts\codex-lead.ps1`, brief `MISSION.md`); session id = `thread_id` in the
  first line of the newest `C:\Users\lucia\dev\gridlock-runs\codex\*-lead.jsonl`. Claude runs no agents
  while it runs.
- Codex sessions: T0.6 proof `01a0dcc9-5fe6-7a51-abf8-e8443e2bd900` (done); lead: see above.

## Decisions (founder, 2026-09-26)
- Operating model: one Codex lead (`gpt-6-sol`, high, subscription) with up to five sub-agents builds,
  gates and judges; Claude reviews last and routes large correction batches back without a Codex judging
  loop. No clock schedule.
- Downloads: "Approve all" — done in T0.1 (Chromium 1243 took 706 MB on disk; quoted ~150 MB).
- Design: **The System Wall Map combined with The Plan Sheet**, no second round ("remember the notion it
  wants it to be an interactive map"). `design/DIRECTION.md`; roll seed `3a040ed5`. The founder stopped
  the design agent; Claude wrote DIRECTION.md from the round's files.
- Hand-off: first "Sat 9:30 am … it can finish earlier than that", then (~04:35) "remove the time limit
  just let it work" — no time limit; `DELIVERY.md` at every gate lets the team review progress any time.
- Prior-art candidates (SPEC § Prior art) are not in the first Codex run unless the founder adds them.

## Checkpoint log (machine time · commit · totals · note)
- 03:29 · a65edf8 · — · session resumed after the previous one broke at a compaction (03:23)
- 03:55 · — · — · venv `%USERPROFILE%\dev\gridlock-venv` (all imports ok); Chromium 1243 ok
- ~04:00 · 5c68c9f · — · plan v3 committed in the OneDrive repo (local only)
- ~04:05 · e9613f7 · — · working clone; T0.1 downloads, pinned requirements, prior-art research
- 04:16 · 72dd54c · — · re-cloned with git data in `gridlock-git` (Codex locks `.git` folders)
- 04:19 · 72dd54c · — · T0.6 passed: two parallel sub-agents, worktrees, commits, pytest, uvicorn, Chromium
- 04:21 · 72dd54c · — · T0.5 checks re-run; mirror identical; T0.8 review started
- 04:45 · 5db51e4 · — · review findings applied; no time limit (founder); launch state committed
- 04:49 · (this commit) · — · T0.9 launch of the Codex lead on the founder's "just go"
- 04:56 · 1b190e6 · 18 passed · T0.3a contracts, exported schemas and synthetic API fixtures; DATA T0.2 and WEB T1.3 running in separate worktrees; build_time nullable for reproducible artifacts
- 04:59 · d9604b0 · 2 DATA + 18 contract passed · T0.2 merged after diff review and focused rerun; 230 kept, 181 placed, 477 overlaps, 44 cross-state; WEB T1.3 and API T1.2 running, T0.4 harness under construction
- ~05:00 · d9604b0 · — · Founder amendment 1 read: judging capped at 4 rounds after G3; gate reviewers do not count; fix P0/P1 after final round, VERIFY, then deliver for Claude review
- 05:15 · ca53d05 · 47 passed · T1.2 API merged after diff review and lane quick gate; 14 routes/filter cases extended to 23 API checks; live artifacts still legacy-shaped pending DATA T0.3b/T1.5; WEB T1.3 and DATA T0.3b running
- 05:18 · fdd8539 · 47 passed, 1 allow-listed skip · T0.4 harness/gates complete: SETUP offline pass, START fixture health 200 on 8770 and stopped, VERIFY 0 on main, scratch deleted check exit 2, occupied port exit 3; default axe/console audit activates with web shell
- 05:27 · d635f20 · 50 passed, 1 allow-listed skip · T0.3b merged after diff review and lane quick gate; all 230 project citations checked against PDF pages; artifacts contract-valid, 230/181/477/44 and top-ten order preserved; WEB T1.3 committed but waits on production basemap for its audit

## Environment facts
- Working copy `C:\Users\lucia\dev\gridlock`; git data `C:\Users\lucia\dev\gridlock-git` (the `.git` in the
  working copy is a pointer file); origin = the OneDrive repo; nothing pushed.
- Venv `C:\Users\lucia\dev\gridlock-venv`; browsers `C:\Users\lucia\dev\ms-playwright`; worktrees
  `C:\Users\lucia\dev\gridlock-wt`; runs `C:\Users\lucia\dev\gridlock-runs`.
- The Claude app redirects `%LOCALAPPDATA%` writes into its package folder: nothing shared lives there.
- Codex CLI 0.157.1: sub-agents via `collaboration.spawn_agent` (the `multi_agent` feature, on by default);
  `--add-dir` for extra writable folders; `exec resume <id>` takes `-c`, `-m`, `--enable`, `--json`, `-o`,
  `-` (stdin) but not `-s` or `--add-dir` — `codex-lead.ps1` passes the sandbox as config on resume.
- Codex's sandbox locks any folder named `.git` with DENY entries that survive a move: never edit ACLs;
  re-clone instead.
- PowerShell 5.1 re-encodes piped strings: briefs go to Codex as a stdin file handle (`codex-lead.ps1`).

## Open founder questions
- Prior-art candidates in `SPEC.md` § Prior art (none in the first Codex run unless added).
- Q2 (ask Sperry about SERTP/CEII), Q1 team roster, Q3 Claude access for briefs (optional).

## Next actions
1. On the founder's go: T0.9 launch (`scripts\codex-lead.ps1 -Brief
   reviews\2026-09-26-gridlock-build\MISSION.md`), in the background; session id here.
2. While Codex runs: no Claude agents; T5.0 pitch drafts **outside the working copy**
   (`C:\Users\lucia\dev\gridlock-runs\claude-pitch\`), moved into `pitch/` after delivery; progress reports
   from `DELIVERY.md` and this tracker when the founder asks; wait for the completion notification.
3. At delivery: F1 → F2 → F7a (`FINAL-REVIEW.md`) for the founder and team.
