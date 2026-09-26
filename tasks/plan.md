# Implementation plan: GridLock

Status: **v3, waiting for the founder's go** (2026-09-26). v3 applies the founder's operating model: no
clock schedule; one Codex lead builds and judges the whole project with up to five sub-agents; Claude sets
up, launches, then reviews last. Spec: `SPEC.md`. Tasks: `tasks/todo.md`.
Workflow: `.claude/skills/gridlock-build/SKILL.md`. Profile: `PROJECT-PROFILE.md`.

## Overview

Turn the working data pipeline and preview map into a complete, tested app. A Python pipeline builds typed
artifacts; a FastAPI service on 127.0.0.1 serves them plus area queries, search, CSV export and briefs; a
static front end with no build step renders the map, list, details, filters, timeline, search and area
explorer.

**Who does what (founder, 2026-09-26):**
1. **Claude sets up and launches:** the working copy, the environment and the approved downloads; proof
   that Codex can fan out and run the tests in its sandbox; the design round with the founder; the Codex
   mission brief.
2. **The Codex lead runs the project end to end** (`gpt-6-sol`, reasoning high, ChatGPT subscription).
   It fans out up to five sub-agents on the tasks, reviews and merges their work behind the quick gate,
   and runs the full verify at every gate. It also runs **every judging round itself** and loops on the
   findings until its judges find no material improvement. Then it delivers.
3. **Claude reviews last.** It judges the delivered app with its own Opus judges and fixes what it judges
   worth fixing. A large batch of corrections goes back to Codex **without another Codex judging loop**;
   Claude then judges again and ships with the founder.

**No time limit for Codex** (founder, 2026-09-26: "remove the time limit just let it work"; SPEC Q12): the
lead delivers when the project is complete and judged, and rewrites `DELIVERY.md` at every gate so the
founder and team can see real progress at any time. Claude's final review starts at delivery. **The only
fixed times:** Devpost closes **Sun 2026-09-27 11:00 EDT**; the founder submits by **10:30**; the team is
at the judging location by 13:00. There is no other schedule and there are no time boxes. The next round
after the review (the team builds on, another Codex run on open items, or both) is the founder's call.

## Architecture and process decisions

| # | Decision | Rationale | Reversible how |
|---|---|---|---|
| D1 | Static front end, no build step; Leaflet 1.9.4 (SVG) vendored; local GeoJSON basemap; theme via external `theme-init.js` | Offline, accessible map features, CSP `default-src 'self'` holds | Swap behind `web/js/map.js` |
| D2 | FastAPI + uvicorn on 127.0.0.1, `create_app()`, artifacts loaded once | Typed contracts, TestClient, key stays server-side | — |
| D3 | Geometry only in Python: nearest points in EPSG:5070, distance reported geodesic | One source of truth; equal-area projection is not distance-true | — |
| D4 | CSV export uses the list's query function | Export can never disagree with the screen | — |
| D5 | Briefs cached on disk, served only when `input_hash` matches; else template | Demo never waits on the network; never stale | Delete `data/briefs/` to regenerate |
| D6 | IDs: `desc-p<N>`; `sertp-p<page>-<hash6(name+description)>` + collision suffix | Unique, stable, deep-linkable | Migration map |
| D7 | Work in `%USERPROFILE%\dev\gridlock` (outside OneDrive); OneDrive copy untouched (Q8) | Git worktrees and OneDrive sync fight; founder rule | Push/pull between the two |
| D8 | One git worktree + branch + port per build lane; the Codex lead merges into `main` after review + quick gate; worktree location proven in T0.6 | Isolation; clean rollback per task commit | `git revert` per task |
| D9 | Scripted UI audits out-rank visual judgment | Measured auditors caught what eyes missed (Lucky website lesson) | — |
| D10 | Timeline = in-service year only | Plans give in-service dates, not starts | Add windows if Sperry supplies them |
| D11 | **One Codex lead (`gpt-6-sol`, reasoning high, subscription) runs the build** from a mission brief; up to **five** Codex sub-agents at once | Founder's decision (2026-09-26); five is the founder's choice for Codex's own fan-out, an exception to the standing three-agent rule | Fallback below (§ The Codex lead) |
| D12 | **Quick gate before every merge** (≤ 5 min); full matrix at gates | The merge gate must actually run at merge time | — |
| D13 | **ECC agents adopted as rewritten roles**, not installed: the lead applies `references/review-checklists.md` on every merge; specialist reviewers run as fresh sub-agents at gates (G1a contracts · G1 Python + JS · G2 tests + silent failures + domain · G4 accessibility · sanitizer at delivery); Claude reuses the same role files on Opus in the final review | Their checklists are the strongest part of ECC | Drop a gate reviewer only on the founder's word |
| D14 | **Codex judges its own build** with fresh-context judge sub-agents on frozen copies (measured evidence, verdict "material improvement still available: yes / no"); **independence comes from Claude's final review** on a different model | Founder's decision; a builder never grades its own task | Claude's final review can reopen anything |
| D15 | **Corrections after the final review go back to Codex with no judging loop**; Claude re-judges | Founder's decision; keeps one judge of record at the end | — |
| D16 | **No clock schedule and no time limit.** The lead builds in task order (the demo path first), never ends its turn before `delivered` (that would kill its sub-agents), rewrites `DELIVERY.md` at every gate from G1a, and delivers when G4 passes: VERIFY green, sanitizer, README, final `DELIVERY.md`, tag `delivered`. A blocked task is parked, its feature hidden from the demo path (never deleted) and listed for the founder; nothing is cut for time | Founder's decisions ("remove the schedule"; Codex goes "through all the judging rounds it needs"; "remove the time limit just let it work") | The founder can stop the run; the latest `DELIVERY.md` is then the hand-off |
| D17 | Claude runs at most three agents at a time and none while a Codex run is active | Founder's standing rule (interruptions, machine load) | — |

## The Codex lead (D11, D14–D16)

- **Launch (Claude, T0.9):** `scripts\codex-lead.ps1 -Brief reviews\2026-09-26-gridlock-build\MISSION.md`
  runs `codex exec -C %USERPROFILE%\dev\gridlock -m gpt-6-sol -c model_reasoning_effort="high"
  -s workspace-write -c approval_policy="never" --json -o <runs>\lead-last.md -` in the background, with
  the mission brief as a stdin file handle (never as an argument or a piped string: PowerShell 5.1 splits
  embedded quotes and re-encodes piped text), plus `--add-dir` for the worktree, run and git folders and
  `--enable prevent_idle_sleep`. Env: `GRIDLOCK_AI=off`, `GRIDLOCK_PY=<venv python>`,
  `GRIDLOCK_TEST_PORT=8770`, `PLAYWRIGHT_BROWSERS_PATH`; every `ANTHROPIC_*`, `CLAUDE_*`, `CLAUDECODE` and
  `USE_*OAUTH` variable is removed first, so Codex never inherits the Claude session's credentials. JSONL
  goes to `<runs>\codex\`; the session id goes in the tracker. The script waits on the Codex process only,
  so a leftover server cannot hold it open. The completion notification is the signal; nobody polls.
- **Mission brief** (`reviews/2026-09-26-gridlock-build/MISSION.md`, reviewed before launch): the run
  rules (never end the turn early; park and continue; wait at most 10 minutes; re-read after compaction;
  `DELIVERY.md` at every gate), the task list as the work queue, lanes and exclusive files, fan-out ≤ 5,
  per-command ports, the merge rule, gates and their reviewers, frozen judge copies, judging rounds, and
  delivery at G4.
- **Fan-out:** builders get one task each with a self-contained brief. Judges and gate reviewers are fresh
  sub-agents that did not build what they judge, each on a frozen copy with its own port (8781–8785).
- **Memory across a long run:** the lead's context will compact. `reviews/2026-09-26-gridlock-build/TRACKER.md`
  and the ticks in `tasks/todo.md` are its memory: it writes a checkpoint line at every merge and gate.
- **Proven on this machine (2026-09-26):** the subscription accepts `gpt-6-sol` on CLI 0.157.1; real
  Python 3.12 runs (the Microsoft Store `python` alias does not); localhost ports bind. **T0.6 (04:16–04:19):**
  the lead started two sub-agents in parallel with its `collaboration.spawn_agent` tool; each created and
  used its own worktree under `%USERPROFILE%\dev\gridlock-wt`, ran pytest 9.1.1 from the venv and
  committed on its branch; uvicorn served on 127.0.0.1:8770; Playwright Chromium 1243 launched. Sub-agents
  share the lead's filesystem sandbox, so lane limits are instructions the lead enforces at review.
- **Git inside the sandbox:** Codex's sandbox locks any folder named `.git` (explicit DENY entries, kept
  if the folder is moved). The working copy therefore keeps its git data in a fresh
  `%USERPROFILE%\dev\gridlock-git` (`git clone --separate-git-dir`), which `codex-lead.ps1` passes with
  `--add-dir` together with the worktree and run folders.
- **Fallback, not needed after T0.6:** plan v2's model (Claude dispatches one Codex session per lane with
  `scripts\codex-task.ps1`, reviews and merges).
- **Stops:** a usage-limit stop or a crash pauses the lead. Claude checks the working copy, then resumes it
  with `codex exec resume <session id>`; it is never relaunched.
- **Codex MCP noise:** three broken user MCP servers (Hugging Face, n8n, Notion) print errors at start;
  harmless. Nothing in `~/.codex` is changed.
- **Plugins:** the two claude.ai Codex plugins (plan review; MCP dispatch) are read before any use (T0.7);
  the scripts work without them.

## Lanes and ownership

| Lane | Runs on | Owns (exclusive) | Port |
|---|---|---|---|
| CLAUDE | Claude (this session) | Everything it creates in T0.0–T0.9; always `SPEC.md`, `PROJECT-PROFILE.md`, `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.agents/`, `docs/PRESENTATION.md`, `docs/DEVPOST.md`, `docs/QA-CRIB.md`, `reviews/.../pitch/`, `reviews/.../final-review/` | 8765 demo |
| LEAD | Codex lead | `tasks/todo.md` (ticks), the pass folder (except Claude's folders), `scripts/`, `*.cmd`, `requirements.txt`, `.gitattributes`, `.gitignore`, `server/schemas.py`, `contracts/`, `tests/fixtures/api/`, `tests/conftest.py`, `tests/pipeline/test_contracts.py`, `tests/e2e/test_demo_path.py`, `tests/e2e/audits/`, `reviews/.../house-patterns.md`; merges into `main` | 8770 · 8776 (sub-agents on LEAD files) · 8790 verify |
| DATA | Codex sub-agent | `pipeline/` (except `briefs.py`), `data/manual/` (except `contacts.json`), `data/build/`, `tests/pipeline/` | 8771 |
| API | Codex sub-agent | `server/` (except `schemas.py`), `pipeline/briefs.py`, `data/briefs/`, `data/manual/contacts.json`, `tests/api/`, `tests/eval/` | 8772 |
| WEB | Codex sub-agent | `web/` (except WEB-2 files), `tests/e2e/` (except LEAD's and WEB-2's) | 8773 |
| WEB-2 | Codex sub-agent | `web/js/search.js`, `web/js/export.js`, `web/js/area.js`, `web/css/print.css`, `web/print.html`, their e2e files | 8774 |
| DOCS | Codex sub-agent (T5.1a); Claude Opus agent (T5.1b) | `README.md`, `docs/` (except Claude's three), `LICENSE` | 8775 |
| JUDGE / gate reviewers | Codex sub-agents during the build; Claude Opus agents in the final review | Their own folder in the pass only | 8781–8785 |

## Gates — no clock times; nothing advances past a red gate

| Gate | Who | Must be true |
|---|---|---|
| Go | founder | The founder's "go" (Q6 downloads, Q9 design and Q12 no time limit were answered 2026-09-26) |
| Launch | Claude | T0.0–T0.8 done: plan committed; working copy, venv and downloads; pass folder and scripts; Codex proven (fan-out, pytest, uvicorn, Chromium); direction locked; mission brief reviewed |
| G1a foundations | Codex lead | Contracts frozen and type-reviewed; harness + quick gate; VERIFY green; baseline set |
| G1 walking skeleton | Codex lead | Map + list from the API; T1.4a audits green; Python and JS reviewers' CRITICAL/HIGH closed |
| G2 core demo path | Codex lead | Search → pair → detail → sources → export green; domain spot-check, test analysis and silent-failure sweep closed or assigned |
| G3 feature freeze | Codex lead | Every feature in, or hidden per the ladder; full matrix green; held-out eval 10/10 (template, or Claude briefs with Q3) |
| G4 judged | Codex lead | Every Codex judge says "material improvement: no", or only founder decisions / external dependencies are left |
| Delivery | Codex lead | When G4 passes (no time limit, D16): VERIFY green, sanitizer, README, final `DELIVERY.md`, tag `delivered` |
| Final review | Claude | First report (`FINAL-REVIEW.md`) right after round 1; then Claude's judges say "no" or only founder decisions are left; corrections merged; VERIFY green |
| G5 ship-ready | Claude + founder | `references/ship-checklist.md` green; the founder submits by 10:30 |

## Scope ladder — cut first = 1

The founder decides cuts. While the founder is away, the Codex lead does not wait: it hides the unfinished
feature from the demo path (code stays) and lists the cut as a founder question in `DELIVERY.md`.
Ordered by impact on the judged demo × confidence ÷ effort left (ECC `product-lens`).

| # | Cut | Saves (est.) | What stays |
|---|---|---|---|
| 1 | Print view | ~1.5 h | CSV export |
| 2 | Timeline play button | ~0.5 h | Slider + "All years" |
| 3 | On-demand brief generation | ~1 h | Cached + template briefs |
| 4 | Dark theme (toggle hidden; audits light only) | ~2 h | Light theme |
| 5 | Area-explorer UI | ~2.5 h | `/api/area`, search "zoom to place" |
| 6 | Claude briefs entirely | ~3 h | Template briefs |

**Never cut:** map + ranked list + project and overlap detail with sources and accuracy + savings range or
reason + filters + city search + CSV + demo path + green verify.
**T-2h (Sun 09:00, two hours before the deadline):** list done / not done; each open item is cut from the
demo, stubbed honestly, or finished only if < 30 minutes remain.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| No time limit: a long run leaves less time for Claude's review and the founder's rehearsals before Sun 10:30 | High | `DELIVERY.md` rewritten at every gate, so the founder can follow progress and stop the run with a usable hand-off; Claude reports progress when the founder asks; the demo path is built first |
| The lead ends its turn early and kills its sub-agents | High | MISSION "Your run" rules: never end the turn before `delivered`; park and continue; bounded waits |
| Sub-agent fan-out unproven inside `codex exec` | High | T0.6 proves it before launch; fallback above |
| Codex judging its own build | Med | Fresh-context judge sub-agents on frozen copies with measured evidence (D14); Claude's independent final review on a different model |
| #1 story wording overstated (DESC work is at Deerfield on the Okatie–McIntosh tie) | High | `shared_endpoint` reason; T2.10 + domain spot-check at G2 pick the demo pair from evidence |
| Location accuracy (49/230 unknown; Okatie inferred) | High | T2.2 + H1; accuracy on every project; counts visible |
| SERTP CEII question | High | H2 at the venue; plan B in SPEC Q2 |
| Codex usage limits / sandbox limits (Chromium untested) | Med | T0.6 proves the sandbox; Claude resumes a stopped lead; the founder decides the e2e path if Chromium fails |
| Five sub-agents on a laptop with a nearly full disk | Med | Free space checked in T0.1; small traces; prune `<runs>`; nothing else heavy runs during the build |
| API spend without a yes (browser CSRF; `ant` profile found by tests) | Med | Header + same-origin + cap on POST; `GRIDLOCK_AI=off` in tests; outbound-socket guard; Codex never holds the credential |
| Stale briefs after corrections | Med | Hash check; stale count in meta; one regeneration after the final review, inside the ceiling |
| Public repo exposure (CEII-header PDF, local paths) | Med | Q11 default; scrub before push; counts-only secret scan |
| Git + OneDrive + worktrees | Med | D7: work outside OneDrive |
| Venue Wi-Fi | Med | Nothing needs the network; screenshot fallback |
| Windows traps (PS 5.1 quoting, Store python, CRLF) | Low | Prompts via stdin files; `GRIDLOCK_PY`; `.gitattributes` |

## Downloads — approved by the founder 2026-09-26 ("Approve all")

Claude fetches them in T0.1, before launch, because the Codex sandbox has no network. Nothing beyond this
list is downloaded.

| What | Source | Size (approx.) | Where | Licence |
|---|---|---|---|---|
| Python packages: fastapi, uvicorn, pydantic, anthropic, pytest, httpx, playwright, **shapely, pyproj, pypdf** (+ deps) | PyPI | 90–120 MB | `%USERPROFILE%\dev\gridlock-venv` | MIT/BSD/Apache |
| Leaflet 1.9.4 dist | cdnjs / npm registry | ~0.2 MB | `web/vendor/` (committed) | BSD-2 |
| axe-core 4.x `axe.min.js` (tests only; read before use) | cdnjs / npm registry | ~0.6 MB | `tests/e2e/vendor/` | MPL-2.0 |
| ~8 Tabler icons as SVG text | tabler.io / GitHub | < 10 KB | `web/icons/` | MIT |
| Census counties 1:500k (GA + SC extracted) | www2.census.gov | ~10 MB zip → ~1 MB kept | `data/raw/` | Public domain |
| Playwright Chromium matching the pinned version, only if the installed 1223/1234 builds don't match (Playwright 1.63.0 needs 1243: fetched) | Playwright CDN | quoted ~150 MB; **706 MB on disk** with the headless shell, ffmpeg and winldd (fetched 2026-09-26) | `%USERPROFILE%\dev\ms-playwright` | Apache-2.0 |
| Claude API calls — only with Q3 | api.anthropic.com | ceiling set by the founder | `data/briefs/` | — |

## Gap check — every requirement and feature traced

| Item | Task(s) | Verified by |
|---|---|---|
| Interactive UI, both utilities, overlaps highlighted | T1.3, T2.5a/b | e2e shell + details; business-fit judge |
| Ranked list | T0.2, T1.3 | byte-identical rebuild + top-10 regression; e2e |
| Savings estimate (range or reason) | T2.3, T2.5b | savings tests; detail e2e |
| 40 km rule + 4 tiers + boundaries | T2.1 | boundary tests |
| Timeline overlap | T2.7 | e2e; score tests |
| Public only / CEII | H2, Q2, Q11, T5.1 | tracker; DATA-SOURCES |
| No-overlap count | T1.5 meta, T2.5b | API + e2e |
| Named example areas | T2.10 | test + METHODOLOGY table |
| Timeline slider | T2.7 | e2e |
| Source doc + real page | T0.3b, T1.1, T2.4 | page-contains-name test; PDF route test |
| Accuracy label | T2.2, T1.3 | e2e; data tests |
| City search | T2.8a/b | API + e2e |
| Filters | T1.1, T1.2, T2.6 | filter e2e (API = list; map = project count) |
| Export CSV + print | T2.4, T2.9 | twin-path tests |
| Area explorer | T3.4a/b | API + e2e |
| AI brief | T3.1, T3.2, T3.3a, T3.3b, F6 | grader, hash check, e2e |
| Project detail | T2.5a | e2e |
| States, 1440/390, light/dark, keyboard | T1.3, T1.4a/b, T3.5 | audits |
| Offline + no Claude access | T3.5, T3.3b | e2e (non-local blocked; outbound guard) |
| Security | T1.2, T2.4, T3.3a | API tests; security judge |
| Operating model (lead, fan-out, delivery, final review) | T0.6, T0.8, T0.9, D.1–D.3, F1–F5 | fan-out proof; mission-brief review; `DELIVERY.md`; final-review judgments |
| Codex environment | T0.6, T0.7 | smoke tasks in the tracker |
| Prior art and pitch (PaverOps and peers) | SPEC § Prior art, T5.0, T5.3 | sources cited; change-reviewer read |
| Docs, Q&A, demo, Devpost, fresh clone | T5.0–T5.5, H9 | docs-truth walk; checklist |

## Review log — independent gap review (2026-09-26, Claude Opus, fresh context)

Verdict received: "ready to approve after fixes". Claude re-checked the data claims before fixing:
duplicate SERTP p.133 entry ✓ · duplicate DESC project_id "6809 M" ✓ · 459 markers vs 427 rows ✓
(the 32 missed are all TVA, pp. 171–181, "In- Service") · no Thomson/Vogtle/Bluffton project in the loaded
plans ✓ · 211 of 326 Southern names with en dashes ✓ · two DESC totals < $2M ✓ (6846 A printed total
$1,238,443 ≠ its year columns' sum) · DESC page = project number for all 54 (the "row number" concern is
moot, the page is still recorded explicitly).

| Finding | Fixed in |
|---|---|
| GAP-01 Q6 default blocks build; geo packages missing | SPEC open questions (Q6 explicit); Downloads table |
| GAP-02 ID collisions; real pages | SPEC contracts; T0.3a, T0.3b |
| GAP-03 schedule | v2: lanes (WEB-2), T1.4a/b, DATA starts at T0.2; v3: the clock schedule is gone (D16) |
| GAP-04 ladder | Scope ladder numbered with hours |
| GAP-05 #1 pair wording | `shared_endpoint`; T2.1; T2.10; demo pair chosen from evidence |
| GAP-06 named examples; parser completeness; README claim | T2.10; T1.1 completeness test; data README corrected |
| GAP-07 dash lint vs data | ui-contract lint scope; one label text; names verbatim (T1.1) |
| GAP-08 costs; savings formula; statuses | T1.1 cost by column + flags; T2.3 formula first; `savings.status` |
| GAP-09 project view; no-overlap count | T2.5a; meta field |
| GAP-10 producers, split tasks, freeze time, merges | T1.5; a/b tasks; freeze at G1a; D8 |
| GAP-11 merge gate | D12; T1.4a quick gate |
| GAP-12 test holes (CSV BOM, deep links, ties, concurrency, PDF, count changes, filter semantics) | SPEC testing; T0.2/T2.4/T2.5b/T2.6/T3.3a |
| GAP-13 band boundaries; share text | SPEC overlap rules; T2.1 |
| GAP-14 utility attribution; GA-only pairs | `utility_basis`; `pair_note`; unmapped reasons; G2 domain spot-check (T2.11) |
| GAP-15 unapproved API spend paths | T3.3a protections; `GRIDLOCK_AI=off`; outbound guard |
| GAP-16 public repo | Q11; scrub + counts-only scan (ship checklist) |
| GAP-17 CSP vs inline theme script; Leaflet HTML strings | `theme-init.js`; DOM-node tooltips; fixture |
| GAP-18 founder-gated fallbacks | Answers at Go; design lock or the assigned direction; Q2 plan B; Q3 ceiling |
| GAP-19 stale briefs | D5 hash check; stale count; regeneration |
| GAP-20 OneDrive/Windows | D7; run output outside OneDrive; `GRIDLOCK_TEST_PORT`; judge ports; SETUP.cmd; `.gitattributes` |
| GAP-21 grader numbers; max_tokens; ranking text; judges; Devpost timing | ai-brief; SPEC; profile; T5.3 Q&A crib; H9 |
| GAP-22 housekeeping | Wording, geodesic distance, Q-list, design timing, Node note, do-not-read scope, T0.0 commit |

**ECC agents review (2026-09-26, founder request):** 68 agents read through `gh api` (MIT; all shipped
descriptions say "PROACTIVELY"/"use immediately", so none is installed as-is). Adopted, rewritten as
role files over one checklist file (`references/review-checklists.md`): code-reviewer (gating) ·
python-reviewer + fastapi-reviewer · silent-failure-hunter · typescript-reviewer (JS parts) ·
pr-test-analyzer + tdd-guide · a11y-architect (WCAG refs corrected) · type-design-analyzer ·
gan-evaluator (judge walkthrough) · opensource-sanitizer (never prints secrets, never squashes) ·
e2e-runner, build-error-resolver, loop-operator as rules only. Avoided: agents that install packages,
run npx, delete code, commit or push, send messages, or edit settings.

**v3 (2026-09-26, founder's operating model):** clock schedule removed (gate targets, time boxes, founder
schedule, sleep blocks); one Codex lead runs the build, the gates and every judging round with up to five
sub-agents; Claude sets up, launches and reviews last; corrections after the final review go back to Codex
without a judging loop; downloads approved; design: The System Wall Map with The Plan Sheet's details; no
time limit for Codex (the founder removed the Sat 09:30 hand-off), `DELIVERY.md` at every gate (D16);
prior art added (PaverOps and peers, SPEC § Prior art). Pre-launch review of `MISSION.md` (5 HIGH, 7
MEDIUM) applied: run rules, credential scrub in the launch script, committed launch state, per-round
frozen copies, per-command ports, main-copy guard, wave-1 ownership, UTF-8 reading, house-patterns path.
