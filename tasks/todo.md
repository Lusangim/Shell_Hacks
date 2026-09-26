# GridLock — task list

Status: **v3, waiting for the founder's go** (2026-09-26). Rationale, lanes, gates: `tasks/plan.md`.
Tick a box only when its verification ran in this session and passed. One commit per task:
`<LANE>: T<n> <what>`. Owners: **CLAUDE** (setup, launch, final review) · **LEAD** (the Codex lead,
`gpt-6-sol`, reasoning high, subscription) · **DATA / API / WEB / WEB-2 / DOCS** (Codex sub-agents the lead
assigns) · **JUDGE** (Codex judge sub-agents during the build; Claude Opus agents in the final review) ·
**HUMAN** (founder/team). No clock schedule and no time boxes; the only times are the hand-off
(Codex delivers by **Sat 09:30 EDT** at the latest, earlier if it finishes; SPEC Q12) and the deadline
(**Sun 11:00 EDT**, submit by 10:30).
Up to five Codex sub-agents at once; at most three Claude agents at once, and none while a Codex run is
active. Every merge passes `scripts\quick-gate.ps1`; every gate passes `VERIFY.cmd`.

---

## Phase 0 — Setup and launch (CLAUDE) · after the founder's go

- [ ] **T0.0 Commit the plan** (CLAUDE)
  - Acceptance: plan docs, skill, `AGENTS.md`, `CLAUDE.md`, role files committed on `main` in the OneDrive repo (no push unless Q7 yes).
  - Verify: `git status` clean.
- [ ] **T0.1 Clone + environment + approved downloads** (CLAUDE)
  - Acceptance: free disk space recorded; working clone `%USERPROFILE%\dev\gridlock` (Q8); `SETUP.cmd` → `scripts\setup.ps1` creates `%USERPROFILE%\dev\gridlock-venv` from Python 3.12.4 with pinned `requirements.txt` (incl. shapely, pyproj, pypdf) and sets `PLAYWRIGHT_BROWSERS_PATH=%USERPROFILE%\dev\ms-playwright`; nothing under `%LOCALAPPDATA%`; idempotent; `.gitattributes` forces CRLF for `*.cmd`/`*.ps1`; every item in `tasks/plan.md` § Downloads fetched into its folder (Chromium only if the installed builds don't match the pin); nothing written inside OneDrive.
  - Verify: run twice; venv imports all packages; each download present with its size; `git status` shows only the intended files.
  - Files: `requirements.txt`, `SETUP.cmd`, `scripts/setup.ps1`, `.gitattributes`, `web/vendor/`, `tests/e2e/vendor/`, `web/icons/`, `data/raw/` (counties).
- [ ] **T0.5 Pass + launch scripts** (CLAUDE)
  - Acceptance: `reviews/2026-09-26-gridlock-build/BRIEF.md` + `TRACKER.md` (ownership, ports, worktrees; checkpoint log with machine-read time, commit, test totals, Codex session ids; handoff sections); `scripts/worktree.ps1 <lane>`; `scripts/codex-lead.ps1` and `scripts/codex-task.ps1` per `tasks/plan.md` § The Codex lead (prompt via stdin file, `-m gpt-6-sol`, reasoning high, workspace-write, approval never, `GRIDLOCK_AI=off`, JSONL under the run folder, session id printed); role files `.claude/agents/gridlock-*.md`, `AGENTS.md`, `CLAUDE.md` and the `.agents/skills/` mirror checked against the final scripts.
  - Verify: create + remove a throwaway worktree; both scripts' `-WhatIf` print the exact command; mirror identical to `.claude/skills/gridlock-build/` (hash compare).
- [ ] **T0.6 Prove Codex, including fan-out** (CLAUDE → Codex)
  - Acceptance: a test mission through `codex-lead.ps1` makes the lead spawn two sub-agents that each, in their own lane worktree, run `$env:GRIDLOCK_PY -m pytest --version` and commit one file; the lead then starts uvicorn on 8770 and launches Playwright Chromium headless once. Recorded in the tracker: how sub-agents were enabled, where they could write (worktree and run-output folders), Chromium yes/no. Fan-out fails → the founder picks the fallback (`tasks/plan.md` § The Codex lead). Chromium fails → the founder decides how e2e and audits run.
  - Verify: the lead's last-message file + session id in the tracker; both sub-agent commits exist; the test worktrees removed afterwards.
- [ ] **T0.7 Read the two Codex plugins** (CLAUDE) — only if they have synced; the scripts do not need them
  - Acceptance: read-only evaluation (hooks, MCP command, sandbox defaults, what they send where) in the tracker; a plugin is used only if it enforces cwd, sandbox and model as the scripts do.
- [ ] **T1.0 Design direction** (CLAUDE: `gridlock-design` agent + HUMAN) — runs alongside T0.1–T0.6
  - Acceptance: impeccable's direction round ran (its scripts read first and proven to write nothing in the Lucky vault, or copied here without `node_modules`; Node 24 runs them) and the founder locked a direction — or, if the founder is away when every other launch task is done, the assigned direction is used and the founder is told; the direction contract (THESIS · OWN-WORLD · STORY · FIRST VIEWPORT · FORM) is written to `reviews/.../design/DIRECTION.md` for WEB; Claude checks its utility palette with the `dataviz` validator (contrast, colour-vision) before launch.
- [ ] **T0.8 Codex mission brief** (CLAUDE)
  - Acceptance: `reviews/2026-09-26-gridlock-build/MISSION.md` from `references/agent-prompts.md` § Codex mission brief, filled with the hand-off time, the T0.6 results (fan-out mechanism, worktree and run folders, e2e path), `DIRECTION.md`, the task queue and the judging plan; reviewed by a `gridlock-reviewer` agent for gaps against plan v3 and the standing rules; findings fixed.
- [ ] **T0.9 Launch** (CLAUDE)
  - Acceptance: tracker checkpoint written; `scripts\codex-lead.ps1 -Brief MISSION.md` running in the background; session id in the tracker; the founder told in one line. Claude then waits for the completion notification (no polling) and does T5.0 meanwhile.

### Checkpoint Launch
- [ ] Downloads in place · [ ] Codex fan-out proven (or the founder's fallback chosen) · [ ] direction set · [ ] mission brief reviewed · [ ] lead running, session id recorded

---

## Phase 0b — Foundations (LEAD and sub-agents) → G1a

- [ ] **T0.2 Restructure into packages** (DATA) — first build task
  - Acceptance: `git mv` into `pipeline/` + `data/raw` + `data/manual` + `data/build`; `python -m pipeline.build_all` offline (`--refresh` only for downloads); stage counts reconcile and are written to `meta.json` (every source row kept, dropped with a reason, or the build fails); counts unchanged (230 kept · 181 placed · 477 overlaps · 44 cross-state) and top-10 pairs unchanged — any later legitimate change needs a before/after table the lead approves and records; v0 `preview.html`/`build_preview.py` removed; `gridlock-data/README.md` correction kept.
  - Verify: `tests/pipeline/test_rebuild_regression.py` green; two rebuilds byte-identical.
- [ ] **T0.3a Contracts + fixtures** (LEAD) — parallel with T0.2
  - Acceptance: `server/schemas.py` = every model in SPEC § Contracts incl. `utility_basis`, `cost_flags`, `touch_reason` (5 values), `pair_note`, `savings.status`, `brief_status`, `no_overlap_count`, `unmapped_count`, `stale_brief_count`, Area, SearchResult, Error; JSON Schema exported to `contracts/`; fixtures in `tests/fixtures/api/` (normal, empty, unknown-location, no-cost, stale-brief, malicious-string) all schema-valid. **Frozen at G1a.**
  - Verify: `tests/pipeline/test_contracts.py` validates fixtures.
- [ ] **T0.3b Stable IDs + real pages** (DATA) — after T0.2, T0.3a
  - Acceptance: IDs per SPEC (`desc-p<N>`; `sertp-p<page>-<hash6(name+description)>` + `-2` in document order on collision); `source.page` = the real PDF page; all artifacts validate against `contracts/`.
  - Verify: `tests/pipeline/test_ids.py` — unique across all rows; identical across two rebuilds; for every project the cited page's text contains its name or project_id.
- [ ] **T0.4 Harness + gates** (LEAD)
  - Acceptance: `pytest.ini`; fixture starting uvicorn on `GRIDLOCK_TEST_PORT` (required; no default) against a given folder; socket guard failing any non-loopback connection from the server under test; `scripts/quick-gate.ps1` (compileall · pytest · e2e smoke 1440 light · console errors · axe default; ≤ 5 min); `scripts/verify.ps1` + `VERIFY.cmd` + `START.cmd` (ASCII; clear messages for missing venv / busy port); `python -m server` for non-Windows teammates; run output in the folder T0.6 proved; `scripts/verify-baseline.json` counts **passing** checks; skips only via a named allow-list; exit 0/1/2/3.
  - Verify: quick gate and VERIFY = 0 on the skeleton; delete a check in a scratch copy → 2; occupied port → 3.

### Checkpoint G1a — foundations
- [ ] Merged verify green · [ ] contracts frozen and committed · [ ] `gridlock-type-design` review of the contracts closed (§G) · [ ] tracker line

---

## Phase 1 — Walking skeleton (DATA ∥ API ∥ WEB) → G1

- [ ] **T1.1 Project fields** (DATA)
  - Acceptance: year from in-service text (invalid "04/31/26"/"06/31/2026"; phased → last phase); cost read **by column** (Previous, years, Total) with `cost_flags` (`printed_total_differs_from_sum` — e.g. 6846 A prints $1,238,443 but its columns sum to $2,088,443; `below_list_threshold`); voltage, type, miles; names and descriptions **verbatim** (remove the en-dash rewrite in `extract.py`); NFKC + control/zero-width stripping; parser completeness: every "Project Name:" marker is a row or a listed exclusion (TVA pp. 171–181 "In- Service"); unknowns null.
  - Verify: `tests/pipeline/test_fields.py` (≥ 20 real cases incl. the odd dates, both low costs, the p.133 duplicate) + `test_completeness.py`; five costs hand-checked against their pages in the report.
- [ ] **T1.5 Build extras** (DATA)
  - Acceptance: `build_all` also writes `places.json` (Census places GA + SC), `basemap.json` (state outlines + city labels now; counties added in T3.5), and full `meta.json` (stage counts, `no_overlap_count`, `unmapped_count` with reasons incl. unplaced Southern Company rows); `utility_basis` set (`inferred_from_location` for unprefixed Southern rows placed in GA).
  - Verify: `tests/pipeline/test_build_extras.py`.
- [ ] **T1.2 API skeleton** (API)
  - Acceptance: `create_app()`; artifacts loaded once and validated at startup (refuses to start with a clear message if missing/invalid); settings object (no key read at import; `GRIDLOCK_AI` on/off); typed `response_model` everywhere; no CORS; 127.0.0.1 only; host check (127.0.0.1/localhost); security headers (CSP `default-src 'self'`, nosniff, referrer policy); `GET /api/health`, `/api/meta`, `/api/projects` (+ filters), `/api/projects/{id}`, `/api/overlaps` (filters per SPEC semantics; rank order; limit ≤ 500, offset); errors `{error:{code,message}}`.
  - Verify: `tests/api/test_core.py` — happy paths, 422s, limit cap, bad host 400, contract validation of every response, socket guard.
- [ ] **T1.3 Web shell** (WEB) — after T1.0 and T0.3a (fixtures until T1.2 lands)
  - Acceptance: layout per `references/ui-contract.md` + `DIRECTION.md` (desktop map + side panel; 390 px bottom sheet); Leaflet SVG; local basemap from `basemap.json`; tokens light/dark (the utility palette from `DIRECTION.md`, already checked with the `dataviz` validator); `theme-init.js` external, loaded before first paint; projects coloured by utility, accuracy styled (solid / dashed / listed only); ranked overlaps list; loading / empty / error states; data via `textContent` with `data-src`; map tooltips as DOM nodes; `<noscript>` notice; footer disclaimer and the loaded plan editions with their dates from `/api/meta` (e.g. "SERTP 2025 regional plan · DESC SCRTP 2026–2030 list"; prior art: provenance earns trust).
  - Verify (per the e2e path set in T0.6): `tests/e2e/test_shell.py` — map features = API placed-project count; list ≥ 10; 0 console errors at 1440/390; malicious-string fixture rendered as text in list and tooltip.
- [ ] **T1.4a Quick-gate audits** (LEAD)
  - Acceptance: `tests/e2e/audits/` checks 1, 2, 3, 6, 7 (demo-path subset), 10, 15 of the ui-contract gate, ported from the four Lucky website auditors (in-page JS reused in Python Playwright; their three flaws fixed) + axe; conventions: role/label/`data-testid` locators, wait on responses never sleeps, each new test run 3× before it enters the baseline.
  - Verify: each check fails on a deliberately broken scratch page, then passes on the shell.

### Checkpoint G1 — walking skeleton
- [ ] Merged verify green · [ ] gate reviewers `gridlock-python-reviewer` + `gridlock-js-reviewer` as sub-agents — CRITICAL/HIGH closed · [ ] screenshots 1440/390 in the pass folder for the founder · [ ] `references/house-patterns.md` written from the skeleton (patterns with `path:line`)

---

## Phase 2 — Core demo path → G2

- [ ] **T2.1 Bands and why they touch** (DATA)
  - Acceptance: SPEC overlap rules (touching ≤ 1 m; strict `<` limits); geodesic distance between nearest points; `touch_reason` — `same_substation` only when both projects are work at the same named substation (both voltages shown), `shared_endpoint` when a line ends where the other project works, else `lines_cross` / `proximity` / `same_area_approximate`; `touch_detail` quotes what the PDFs support; `can_share` from band + reason; ties by distance then id.
  - Verify: `tests/pipeline/test_bands_touch.py` — boundary points (1/1.01 m, 1,599.99/1,600, 7,999.99/8,000, 39,999.99/40,000); DESC Okatie–McIntosh tie × McIntosh 230 kV relays = `shared_endpoint` with the Deerfield detail; × SAV Goshen–McIntosh 115 kV = `shared_endpoint` at McIntosh 115 kV.
- [ ] **T2.2 Location quality, border region** (DATA; HUMAN H1 if done before this task)
  - Acceptance: every project with an endpoint in lat 31.5–34.0, lon −82.8 to −80.5 placed from a named source or marked unknown with the reason; each hand fix in `data/manual/manual_locations.csv` has source + note; Okatie verified by the founder or kept INFERRED; before/after counts reported.
  - Verify: `tests/pipeline/test_manual_locations.py`; rebuild; before/after table approved by the lead and recorded.
- [ ] **T2.3 Savings model** (DATA) — formula written into the task report **before** code
  - Acceptance: `data/manual/assumptions.json` (id, low/high, unit, rationale, source + date or "team assumption"); per overlap `savings.status` = range · timing_too_far (gap > 2 years) · no_cost · unknown_year; range never a single number; plan cost used when present, proxy flagged; rounding to the assumptions' precision.
  - Verify: `tests/pipeline/test_savings.py` — hand-computed cases for each status.
- [ ] **T2.10 Named examples + demo pair** (DATA)
  - Acceptance: table in `docs/METHODOLOGY.md` draft section: Jasper, Okatie, Bluffton, Urquhart, McIntosh, Thomson–Vogtle → the pair found, or "not in the loaded plans" with evidence (search terms, pages); the top Savannah and Augusta pairs listed with their exact wording; whether to hand-enter Thomson–Vogtle from the Georgia Power IRP (with its source) is listed as a founder question in `DELIVERY.md`.
  - Verify: `tests/pipeline/test_named_examples.py` asserts each row's claim against the artifacts.
- [ ] **T2.4 Details, CSV, source documents** (API)
  - Acceptance: `GET /api/overlaps/{id}` (both projects, savings breakdown, touch reason, sources); `GET /api/export/overlaps.csv` (same query function; UTF-8 with BOM; cells starting `= + - @`, tab or CR escaped; numbers never escaped; columns laid out like a utility conflict matrix, FHWA SHRP2 R15B: rank, overlap id, both projects and utilities, band, distance km, why they touch, both in-service years and the gap, both accuracy labels, both sources with pages, savings status and range, and an empty "Coordination status" column for the planner); `GET /api/sources/{doc_id}` whitelist → 200 `application/pdf`.
  - Verify: `tests/api/test_detail_export.py` — CSV == list for 3 filter sets; unknown id 404; traversal 404; formula/tab/CR escaping; numeric cells untouched; PDF headers.
- [ ] **T2.5a Project detail** (WEB)
  - Acceptance: clicking a project (map or a Projects tab in the panel) shows it with source link (`#page=N`), accuracy, cost or "not stated", its overlaps (or "no overlap within 40 km"); meta line "N of M projects have no overlap within 40 km".
  - Verify: `tests/e2e/test_project_detail.py`.
- [ ] **T2.5b Overlap detail** (WEB)
  - Acceptance: both projects, distance + band + why they touch + `touch_detail` + what can be shared, timeline, accuracy chips ("possibly touching" when approximate), `pair_note`, source links, savings range or its reason with assumptions inline; map highlights the pair; deep link `#overlap=<id>`; unknown / stale / filtered-out ids handled with a message; late responses ignored (request token / AbortController).
  - Verify: `tests/e2e/test_overlap_detail.py` — list and map entry; deep links (valid, unknown, filtered); keyboard; 390 px; race test.
- [ ] **T2.6 Filters** (WEB)
  - Acceptance: utility, voltage, year range, type, band, cross-state; counts; "Location unknown (n)" drawer with reasons; filter semantics per SPEC; URL state for filters, year, area centre and selection.
  - Verify: `tests/e2e/test_filters.py` — list count == API overlap count; map project features == API project count; clear-all; URL round trip.
- [ ] **T2.7 Timeline slider** (WEB)
  - Acceptance: native range over the data's in-service years (Q4) + "All years" + play/pause; year Y emphasises projects **entering service in Y** and lights up overlaps whose two projects both enter service within Y ± 1; `<output>` + `aria-valuetext`; no animation on input; reduced motion honoured.
  - Verify: `tests/e2e/test_timeline.py` — 2028 lights the McIntosh pairs; arrows step; play stops at the end; All years restores.
- [ ] **T2.8a Search API** (API)
  - Acceptance: `GET /api/search?q=` over `places.json` + project and substation names; prefix + word match; ≤ 10 typed results; q < 2 chars → 422.
  - Verify: `tests/api/test_search.py` ("sav" → Savannah first; "okat" → Okatie projects).
- [ ] **T2.8b Search UI** (WEB-2)
  - Acceptance: `<input type="search" list>` + `<datalist>` (ARIA combobox only if an audit fails); Enter zooms and offers "Explore this area".
  - Verify: `tests/e2e/test_search.py` keyboard-only.
- [ ] **T2.9 Export and print** (WEB-2)
  - Acceptance: "Export CSV" downloads the server CSV for current filters; "Print report": ranked table, selected overlap, assumptions, sources, attribution; Letter without cut-off columns.
  - Verify: `tests/e2e/test_export.py` — CSV rows == visible list == API list; print view has the CSV's required fields; `media=print` screenshot.
- [ ] **T2.11 Domain spot-check** (JUDGE, Codex sub-agent with `gridlock-judge.md`, domain lens) — at G2
  - Acceptance: a transmission-planning read of the top 10 pairs, their wording, bands, years, costs and sources against the PDFs; Georgia-only pairs' note; findings to the owning lanes before G3.

### Checkpoint G2 — core demo path
- [ ] Demo path e2e green · [ ] merged verify green · [ ] gate round (build lanes paused while it runs): T2.11 + `gridlock-test-analyzer` + `gridlock-silent-failure` as sub-agents — findings closed or assigned · [ ] screenshots for the founder · [ ] cuts per the ladder if the hand-off is near, hidden features listed

---

## Phase 3 — Brief, area explorer, resilience → G3

- [ ] **T3.1 Eval set, grader, template** (API) — before any model code
  - Acceptance: 30 real overlaps (20 dev / 10 held-out; hard classes per `references/ai-brief.md` incl. an injection fixture); deterministic grader with number normalisation and allowed constants; `data/manual/contacts.json`; template brief 30/30.
  - Verify: `tests/eval/test_grader.py` catches seeded bad briefs (invented number, person, missing caveat, dash in the product's own wording).
- [ ] **T3.2 Claude brief generator, offline** (API) — no key, no spend
  - Acceptance: per `references/ai-brief.md`: `claude-opus-5`, parse + Pydantic, `fallbacks:"default"`, adaptive, effort medium, `max_tokens` 16000 (a `max_tokens` stop → template); structured fields only; cache key SHA-256(input + prompt version + model), atomic write, corrupt = miss; saved only if graded pass; spend ceiling checked before every call; the batch script refuses to run without Claude access and a ceiling. Real calls happen only in F6.
  - Verify: `tests/api/test_briefs.py` with a fake client via dependency overrides (pass, refusal, `max_tokens`, error, ceiling reached).
- [ ] **T3.3a Brief routes** (API)
  - Acceptance: `GET /api/briefs/{id}` → cached if `input_hash` matches, else template (stale counted in meta); `POST /api/briefs/{id}/generate` only with Claude access **and** header `X-GridLock: 1` **and** same-origin; one at a time; capped by `GRIDLOCK_MAX_ONDEMAND` (default 5) and the spend ceiling; 409 otherwise.
  - Verify: `tests/api/test_brief_routes.py` — twin paths (cached, stale, template, no access, refusal) carry the same required fields; cross-origin POST refused; cap enforced; concurrent POSTs → one generation; atomic cache.
- [ ] **T3.3b Brief UI** (WEB)
  - Acceptance: card labelled "AI-drafted from public plan data. Check before use." or "Template"; sources; "Copy brief"; no Send.
  - Verify: `tests/e2e/test_brief.py` — cached, template, no access; switching overlap while a brief loads shows only the new one.
- [ ] **T3.4a Area API** (API)
  - Acceptance: `GET /api/area?lat&lon&radius_km=40` (1–80; buffer in EPSG:5070; projects intersecting; overlaps with ≥ 1 project inside; counts).
  - Verify: `tests/api/test_area.py` — hand-computed case around McIntosh; bad input 422.
- [ ] **T3.4b Area UI** (WEB-2)
  - Acceptance: map click or "Explore this area" draws the circle + summary panel; Esc clears; a second click while loading shows only the second result; area centre in the URL.
  - Verify: `tests/e2e/test_area.py` (click + keyboard path + race).
- [ ] **T3.5 Resilience and dark theme** (WEB)
  - Acceptance: counties in the basemap; dark theme remaps every token incl. the basemap (no flash); every surface's states per the contract; reduced motion; bottom sheet at 390 px.
  - Verify: `tests/e2e/test_offline.py` (non-local requests blocked → fully usable, 0 console errors); audits dark 1440/390.
- [ ] **T1.4b Full audit gate** (LEAD) — by G3
  - Acceptance: remaining checks (4, 5, 8, 9, 11–14, 16–19, 21; 20 optional) over the six states × 1440/390 × light/dark; baseline raised.
  - Verify: each check proven against a broken scratch page.

### Checkpoint G3 — feature freeze
- [ ] All features demoable, or hidden per the ladder and listed · [ ] full matrix green · [ ] held-out eval 10/10 (template) · [ ] tracker checkpoint · [ ] tag `g3`

---

## Phase 4 — Codex judging and corrections → G4

- [ ] **T4.1 Judges round 1** (JUDGE ×3, Codex sub-agents with `gridlock-judge.md`, frozen `g3` worktrees, ports 8781–8783): domain expert · first-week user + design (ui-contract critique procedure) · reliability + security.
- [ ] **T4.2 Judges round 2** (×3): business / hackathon fit (`gridlock-judge.md`) · change-reviewer on every user-facing word (`gridlock-reviewer.md`) · accessibility (`gridlock-a11y.md`, §F).
- [ ] **T4.3 Corrections wave** (builder sub-agents by ownership): reproduce → fix → check added → quick gate → merge; merged verify.
- [ ] **T4.4 Confirmation round** (JUDGE, combined lenses): stop when every judge says "no" or only founder decisions remain.

### Checkpoint G4
- [ ] No open P0–P1 · [ ] merged verify green, totals ≥ baseline · [ ] tracker checkpoint

---

## Phase D — Delivery (LEAD) · by Sat 09:30 EDT at the latest

- [ ] **D.1 Delivery judging round** (JUDGE sub-agents) — **at 09:00, 30 minutes before the hand-off**, unless G4 already passed
  - Acceptance: no new build task starts; in-flight tasks finished or parked (parked work stays on its branch, listed); frozen copy tagged `pre-delivery`; the G4 lenses that apply to what is built run as fresh sub-agents in parallel; P0/P1 findings that fit before the hand-off are fixed behind the quick gate; the rest go into `DELIVERY.md`.
- [ ] **D.2 README true for the delivered state** (DOCS sub-agent or LEAD)
  - Acceptance: `README.md` says what works now, what is hidden or not built, and how to run `SETUP.cmd`, `START.cmd` and `VERIFY.cmd`; nothing claimed that the delivered commit does not do.
- [ ] **D.3 Deliver** (LEAD) — at the hand-off, or at G4 if earlier
  - Acceptance: VERIFY on the delivered commit with no sub-agents running; tag `delivered`; `reviews/2026-09-26-gridlock-build/DELIVERY.md`: each task done / partly done / not started, with evidence · VERIFY summary path and totals · each judge's verdict and the open findings · cuts and hidden features · founder questions · lessons (one dated line each) · session ids and how to resume. The lead then exits.

---

## Phase F — Final review (CLAUDE) · starts at delivery

- [ ] **F1 Freeze and verify** (CLAUDE)
  - Acceptance: `DELIVERY.md` and the tracker read; tag `delivered` checked; `VERIFY.cmd` on a quiet machine; summary read and every red line classified; `START.cmd` on 8765 for the founder and team.
- [ ] **F2 Judges round 1** (CLAUDE: Claude's own §H walkthrough + up to three Opus agents on frozen `delivered` copies, ports 8781–8783): domain expert · first-week user + design · reliability + security.
- [ ] **F7a First review report** (CLAUDE) — right after F2, for the founder and team's review
  - Acceptance: `reviews/2026-09-26-gridlock-build/FINAL-REVIEW.md`: verdict per lens, what is genuinely good, the ranked findings, what Claude will fix itself and what goes back to Codex, founder decisions, a suggested next round.
- [ ] **F3 Judges round 2** (CLAUDE, ≤ 3 Opus agents): business / hackathon fit · change-reviewer on every user-facing word · accessibility; gate reviewers (Python, JS, tests, silent failures) where Claude sees a need.
- [ ] **F4 Fix or route back** (CLAUDE; Codex for a large batch)
  - Acceptance: small, local findings fixed by Claude (test first → quick gate → commit `CLAUDE: F4 <what>`). A large batch (more than five P0–P2 fixes, or any fix spanning lanes or a contract) goes to Codex as one corrections brief (`codex exec resume <lead session id>` or `codex-task.ps1`): fix, check added, quick gate, VERIFY — **no judging rounds**.
  - Verify: merged verify green, totals ≥ baseline.
- [ ] **F5 Confirmation round** (CLAUDE, combined lenses, smaller): until every judge says "no" or only founder decisions remain.
- [ ] **F6 Brief refresh** (CLAUDE) — only with Q3 (Claude access + ceiling)
  - Acceptance: one probe → measured cost per brief → quoted total → the founder's yes → dev before/after table; held-out 10/10; top 60 generated within the ceiling; every cached brief graded; the founder reads 5.
- [ ] **F7b Final review report** (CLAUDE): `FINAL-REVIEW.md` updated after F5.

---

## Phase 5 — Ship (CLAUDE + founder) → G5

- [ ] **T5.0 Pitch drafts** (CLAUDE) — during the Codex run; no agents, no product files
  - Acceptance: drafts in `reviews/2026-09-26-gridlock-build/pitch/` — Q&A crib, presentation outline, Devpost text — with PaverOps and the other prior art from SPEC § Prior art and `research/prior-art-2026-09-26.md` (every claim cited; "snippet" claims verified or dropped); every number left as a visible placeholder until the build verifies it.
- [ ] **T5.1b Docs made true** (CLAUDE: `gridlock-docs` Opus agent) — after the last code change: README, `docs/METHODOLOGY.md` (incl. the named-example table and the ranking formula — savings are not in the score), `docs/DATA-SOURCES.md` (licences, attribution; the HIFLD line layer cited as archived and frozen — HIFLD Open retired 2025-08-26 — with its fetch date; the SERTP edition loaded and the newer 2026 preliminary report named), `docs/DEMO.md` (3-min and 5-min beats) — every click path verified by a scripted walk; `LICENSE` (Q5).
- [ ] **T5.2 Screenshot fallback** (CLAUDE + HUMAN): one per demo beat at 1440; optional 60–90 s recording after a rehearsal script that fails loudly on any missing element.
- [ ] **T5.3 Presentation + Q&A crib** (CLAUDE): `docs/PRESENTATION.md` and `docs/QA-CRIB.md` from the T5.0 drafts, made true (how distances are measured, why accuracy labels, what the savings assume, what "shared endpoint" means, data limits, CEII answer, competitors and prior art).
- [ ] **T5.4 Devpost final** (CLAUDE + HUMAN): `docs/DEVPOST.md` from the H9 draft; Sperry Tech challenge opted in; GitHub link; Discord tag; full names; AI assistance disclosed.
- [ ] **T5.5 Fresh-clone rehearsal** (CLAUDE + `gridlock-sanitizer`): sanitizer PASS on the commit to submit (§I; also before every earlier push); clone the public repo into a temp folder outside OneDrive → SETUP → VERIFY → START; local paths scrubbed (Q11); README renders; repo public.

### Checkpoint G5 — ship-ready
- [ ] T-2h review at Sun 09:00 (emergency protocol if red) · [ ] H7 rehearsal ×3 timed · [ ] H8 founder submits by **10:30 EDT** · [ ] at the judging spot by 13:00

---

## Human tasks (founder / team)

- [ ] **H0** Now: say "go" (Q6 downloads, Q9 design and Q12 hand-off are answered).
- [ ] **H0b** When the design decision page is ready: pick one look (~10 min).
- [ ] **H1** Any time before T2.2: verify Okatie and the top-10 endpoints on Dominion's route map / aerial maps (otherwise Okatie stays "inferred").
- [ ] **H2** At the venue: ask Sperry (a) is the SERTP overview plan acceptable? (b) what were the placeholder data links meant to contain?
- [ ] **H3** Only if you want Claude briefs: Claude access on this laptop (never in chat) + a spending ceiling.
- [ ] **H4** Any time: team roster, roles, Discord tags, first-time hackers, licence (Q1, Q5).
- [ ] **H5** Keep the laptop plugged in and awake while Codex runs.
- [ ] **H6** From the hand-off (Sat 09:30 at the latest): the team reviews `DELIVERY.md`, the running app and `FINAL-REVIEW.md` as it lands; the founder decides the next round.
- [ ] **H7** Before submitting: three timed rehearsals with the screenshot fallback ready.
- [ ] **H8** Sun ≤ 10:30: submit on Devpost (only the founder submits).
- [ ] **H9** Early: Devpost project created, teammates invited, draft text in (AI assistance disclosed).
