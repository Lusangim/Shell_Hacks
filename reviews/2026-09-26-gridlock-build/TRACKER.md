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
- 05:42 · 03ae694 · 58 passed, 1 allow-listed skip · G1a type review confirmed 2 HIGH closed; multiline and count guards added; 2 MEDIUM (nested mutability, exported schema cross-field constraints) documented; contracts frozen; DATA T1.5 ready for post-gate merge
- 05:45 · ab654b2 (g1a), DATA 24e50d8 · 61 passed, 1 allow-listed skip · T1.5 merged: 1,150 places, local two-state/801-label basemap, complete 128 unmapped source-row reasons; WEB synced but live audit found forbidden SVG aria-label and a session-scoped test server holding port 8773, assigned to WEB and LEAD respectively
- 05:55 · WEB a371314 merged · 73 passed + 11 shell + 1 axe · T1.3 map/list shell live on main against DATA artifacts; SVG aria-label removed, live test server function-scoped, no named skips; T1.4a audit build and DATA T1.1 field parsing underway
- 06:07 · DATA 7298579 merged · 37 focused / 98 lane gate passed · T1.1 sourced years, cost columns and flags, voltage/type/miles, verbatim DESC dashes, 459 SERTP marker accounting; WEB focus correction underway for 801 default Leaflet city pins; root T1.4a all-stop audit still red until that WEB fix
- 06:29 · WEB b74065a + DATA f05c037 merged · 135 suite + 17 shell + 18 audit passed · T1.4a seven quick audits with broken-scratch proofs and three 17-check runs complete; city pins replaced by sparse source-backed labels; source hash stable across CRLF/LF; occupied-port guard retained with transient bind retry; G1 review freeze next
- 06:36–06:44 · cf95aa7 / G1 frozen · VERIFY 135/135, 0 fail/skip, baseline 135; production screenshots 1440/390 captured; Python review found one HIGH (Georgia-only pair flagged cross-state) and one MEDIUM (non-atomic artifact publication), JS review ready; DATA G1 repair assigned, G1 tag pending
- 06:56 · 6ef63f8 · VERIFY 139/139, 0 fail/skip, baseline 139 · G1 cross-state HIGH repaired: 43 true different-state pairs, GA-only misflag removed, score 0.096→0.064; Python confirmation pending on frozen copy, publication MEDIUM tracked
- 07:02 · bec2eca (g1) · VERIFY 139/139, 0 fail/skip · G1 tagged after fresh Python confirmation (no CRITICAL/HIGH; material improvement no) and ready JS review; screenshots/house patterns and rewritten DELIVERY committed; T2.1 integration running, medium artifact-publication risk tracked
- 07:09 · 102b6ad · 156 suite + 17 shell + 18 audit lane quick gate; lead reran 21 focused · T2.1 merged after reconciling G1 state scoring: 489 geodesic overlaps, 43 cross-state, GA-only target score 0.064/rank 395, deterministic top ten; API search building, DATA T2.2 next
- 07:16 · 44aefc2 · main quick gate 168 suite + 17 shell + 18 audit passed; lead reran 12 API search checks · T2.8a merged: local typed place/project/station search, short-query 422, deterministic ≤10 results, no outbound calls; DATA T2.2 running, WEB-2 search UI next
- 07:24 · 8efaaaa · main quick gate 173 suite + 17 shell + 18 audit passed; lead reran five location checks · T2.2 merged: 55 mapped border projects provenance-audited, 49 kept unknowns with explicit reasons, Okatie still INFERRED, 489/43 pairs/cross-state and top ten unchanged; DATA T2.3 formula recorded before code, WEB-2 search UI running
- 07:30 · WEB-2 de97092 parked · seven new search e2e passed; existing 390 px shell check failed (second ranked row bottom 965 > viewport 844) after search insertion; no quick gate/merge; independent phone-layout repair on wt/web-2-b, port 8778, while DATA T2.3 continues
- 07:48 · 132bab9 + 79869e7 · main quick gate 186 suite + 17 shell + 18 audit passed; 13 focused lead rerun · T2.3 merged: 201 screening ranges (25 printed plan cost, 176 explicitly team-proxy), 214 timing-too-far, 74 no-cost, assumptions dated and basis tied to validated rates; pytest importlib collection fix permits distinct API/e2e search modules; baseline raised to 186
- 08:05 · ae1fa7a · main quick gate 204 suite + 17 shell + 18 audit passed; 18 focused lead rerun · T2.4 merged: typed overlap detail, unpaged BOM CSV with formula-safe text, two whitelisted local PDF routes; baseline raised to 204; WEB T2.5a and WEB-2 T2.8b duplicate-place repair running
- 08:12 · 321bd0e · main quick gate 214 suite + 17 shell + 18 audit passed; 10 search e2e lead rerun · T2.8b merged: keyboard search, current-query source-backed duplicate choices for Bluffton and duplicate projects, no stale selection, phone two-row sheet and 194 px visible map; baseline raised to 214; WEB T2.5a and DATA T2.10 running
- 08:18 · WEB 11a22d7 parked; repair wt/web-b at 0b9843d · 7 new detail e2e passed, pre-search branch shell/audit 33 passed + 2 failed (phone row bottom 859 > 844; map selector matched new list row); after search integration lead reran both, phone shell passed and selector remains RED; repair assigned. DATA T2.10 flagged known SPEC Q2 `(CEII)` header tension on publicly posted SERTP overview; existing-artifact citation only, question in DELIVERY for Sperry/G2 domain review
- 08:29 · 5c92423 · main quick gate 218 suite + 17 shell + 18 audit passed; four focused lead rerun · T2.10 merged: six named examples, Savannah/Augusta pair evidence and cautious rank-1 demo wording in draft METHODOLOGY; Bluffton and Thomson–Vogtle absent from loaded project names; source-page no-hit searches documented; baseline raised to 218; Q2 classification-header and IRP hand-entry remain founder/domain questions
- 08:39 · 5708198 · main quick gate 234 suite + 17 shell + 18 audit passed; 15 focused lead rerun · T2.5a project detail merged after 390 px and selector repairs; lead-owned transient Windows bind retry has a RED/GREEN harness check; baseline raised to 234; WEB T2.5b running, API T3.4a held for G2 and rechecking on synced branch
- 08:57 · LEAD port lifecycle · main quick gate 235 suite + 17 shell + 18 audit passed; 49 focused lead rerun · T3.4a lane port 8772 failed twice after many function-scoped e2e server restarts; trial session scope conflicted with shell's separate server; module-scoped `live_server` passed, occupied-port guard remains; API lane rerun pending, WEB T2.5b running
- 09:03 · API wt/api ff3e9f4 held · lane quick gate 254 suite + 17 shell + 18 audit passed, lead reran 19 focused area checks · T3.4a is ready but cannot merge before G2 tag; module-scoped test-server fix resolved the prior 8772 bind failures; WEB T2.5b still running
- 09:12 · WEB T2.5b ea1e4c1 parked for repair · after sync lane quick gate 242 passed, 2 existing project-detail e2e failed as empty-hash restore reset a just-opened Projects view; exact failures and race sent to WEB; API T3.1 assigned on held wt/api branch while Phase 2 WEB work continues
- 09:12 · API T3.1 inventory · 489 built overlaps contain 15 same_substation, 28 shared_endpoint, 429 proximity, 17 same_area_approximate and zero lines_cross; the brief's real-ID lines_cross coverage target is unattainable from this build, so API will declare the deviation and never fabricate a pair; G2 domain review to assess the zero
- 09:22 · cd7dfa8 · main quick gate 245 suite + 17 shell + 18 audit passed; lead reran two focused browser checks · T2.5b merged with both project cards, source-backed pair evidence, savings, deep links and map highlight; deterministic Projects load-race test RED/GREEN; baseline raised to 245; WEB T2.6 next, API T3.1 building on held branch
- 09:47 · API wt/api 5b6e324 held · lane quick gate 317 suite + 17 shell + 18 audit passed; lead reran 63 focused · T3.1 30 real eval IDs, organization-only contacts, deterministic grader/template 489/489; omitted stated-year defect found in lead review, RED/GREEN repair; zero real lines_cross declared; T3.2 fake-client work assigned before G2, merge remains held
- 10:14 · 633c972 · main quick gate 256 suite + 17 shell + 18 audit passed; lead reran four focused filter checks · T2.6 merged after scoped security review (no P0–P3), URL/filter API parity, 390 px keyboard order and invalid-link fallback; baseline raised to 256; API T3.2 held security review found two P2 malformed-input failures, assigned to API for repair; WEB T2.7 next
- 10:28 · LEAD shell fixture repair · main quick gate 257 suite + 18 shell + 18 audit passed · shell test server now lives for its module, preventing repeated Windows port binds; lifecycle check RED on function scope and GREEN on module scope; baseline raised to 257; API T3.2 security repairs committed on held branch, definitive lane rerun next
- 10:42 · LEAD e2e fixture repair · main quick gate 258 suite + 18 shell + 18 audit passed · API synced gate exposed 15 Windows bind denials in one production e2e module (343 passed, 15 setup errors); production server now runs once per pytest session, synthetic shell servers and later gate phases use deterministic lane-derived ports; occupied primary port check retained; baseline raised to 258; fresh T3.2 security confirmation closed both P2 findings (82 focused, no open P0–P3), API lane rerun next
- 10:56 · c3e32bb · main quick gate 267 suite + 18 shell + 18 audit passed; lead reran the 2028 timeline data check · T2.7 merged: source-year slider, pair window, URL/history, All years and play/pause, with status/keyboard integration repaired; baseline raised to 267; API held T3.2 security-repaired lane gate 359/18/18 passed, T3.3a guarded routes building; WEB-2 T2.9 export/print building
- ~11:00 · e099697 · — · Founder amendment 2 read: modern map (T1.6). Offline PMTiles and optional Google switch requested; external assets read-only, real key file off-limits; direction v2 becomes visual contract.
- ~11:00 · e099697 · — · Founder amendment 3 read: T1.7 readable text, T1.8 walkthrough. Add acceptance checks and build after map, with brief text when Phase 3 UI exists.
- ~11:00 · e099697 · — · Founder amendment 4 read: up to 8 sub-agents. This runtime exposes four total concurrent slots (lead plus three sub-agents); use every available independent slot, avoid file overlap, and monitor machine load.
- 11:10 · fd13d48 · main baseline 267/18/18; T3.3a focused 107 passed, lane gate 382 pass/2 WEB map-readiness failures · founder direction v2 and T1.6–T1.8 tasks recorded; T1.6 WEB vendor/map work, T2.9 export/print disclosure repair and WEB map-readiness repair active in separate worktrees; API T1.6 Range/config brief and worktree ready for next free agent slot

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
