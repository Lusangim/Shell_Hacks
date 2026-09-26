# Spec: GridLock — coordination finder for neighboring utilities' planned transmission projects

Status: **v3, waiting for the founder's go** (2026-09-26). v2 closed the 22 findings of an independent gap
review (GAP-01…22, register in `tasks/plan.md` § Review log). v3 applies the founder's operating model:
no clock schedule; one Codex lead builds and judges the project with up to five sub-agents and delivers
by Sat 09:30 EDT at the latest (earlier if it finishes); Claude reviews last. Nothing is built until the
founder says go.
Workflow: `.claude/skills/gridlock-build/SKILL.md`.

## Objective

ShellHacks 2026, Sperry Tech **GridLock Challenge**: "Build a tool that compares at least two utilities'
public future construction plans and flags where their planned work overlaps — either because the
projects are physically close to each other, or because they're scheduled around the same time."

**Who uses it:** a transmission planner at a utility, a regional planning forum (SERTP), or a state
regulator asking "where could neighbors share crews, equipment, land and permits?"
**Who judges it:** Round 1 — one general judge, 3-minute live demo at our table; each sponsor (Sperry
Tech for this challenge) evaluates separately; Round 2 — 3–5 minutes for top projects (Hacker Guide).

**Scope:** Georgia + South Carolina, core story the SC–GA border (Savannah, Augusta): Dominion Energy SC
vs Georgia Power / Georgia Transmission Corp. / MEAG Power. Rest of GA/SC searchable.

### Challenge requirements → where they are met
| Requirement | Met by |
|---|---|
| Required: interactive UI showing both utilities' planned projects, visually highlighting overlaps (pan/zoom/click, not a static image) | `web-app` map, project detail, overlap detail |
| Required: ranked list of top coordination opportunities | `overlap-engine` ranking + `web-app` list |
| Bonus: rough cost/impact estimate for at least one flagged opportunity | `savings-model` — every overlap shows **a range or a stated reason** there is none (timing too far apart, no plan cost, unknown year) |
| Geographic overlap: closest points **within 40 km**; tiers touching / under 1.6 km / under 8 km / under 40 km | `overlap-engine` (boundaries below) |
| Timeline overlap: same build window, strong secondary signal used with geography | `overlap-engine` score |
| Public filings only; nothing marked CEII | provenance in `docs/DATA-SOURCES.md`; question to Sperry (Q2) |
| "Expect most of the dataset NOT to overlap" | `/api/meta.no_overlap_count` shown as "N of M projects have no overlap within 40 km" |
| The guide's named example areas (Jasper, Okatie, Bluffton; Urquhart vs Thomson–Vogtle) | T2.10 table: each mapped to a found pair or "not in the loaded plans" with evidence |

### Decided features (founder, 2026-09-26) — all in scope
Tier 0 (load plans · place projects · clickable map · overlap detection · timeline overlap · ranked list ·
savings estimate) plus: timeline slider · source document + page per project · accuracy label (exact /
approximate / unknown) · city search · savings range with assumptions on every overlap · filters
(utility, voltage, year, project type, distance band) · export ranked list (CSV + print-to-PDF) ·
pick-an-area explorer (40 km circle) · AI coordination brief per overlap.

### Prior art and inspiration (read 2026-09-26; pitch and ideas only, never a data source)
- **PaverOps** (paverops.com): a cloud Esri/ArcGIS platform where cities, counties, transportation
  agencies and utilities share current and future projects so they can "reduce dig-ins", run "synchronous
  projects" and share costs; it also manages pavement plans and moratoriums. Membership is restricted to
  local governments and utilities; the site shows no public data, API, pricing or case-study numbers.
  **Use:** validation that coordination tools exist and are used at street level; GridLock does the same
  for transmission, across state lines, from public filings only. **Idea:** its moratorium (a no-dig time
  window after repaving) is a time-window rule like our timeline overlap — a talking point, not new scope.
- **Peers** (full table, sources and "snippet" flags: `reviews/2026-09-26-gridlock-build/research/prior-art-2026-09-26.md`):
  street and right-of-way coordination is an established category — Coordinate (formerly dotMaps; Chicago,
  Seattle), Accela Right of Way (formerly Envista), Esri's Capital Project Coordination, the UK's
  one.network, London's Infrastructure Coordination Service, Toronto, SEMCOG in Michigan, the FHWA SHRP2
  R15B Utility Conflict Matrix and NJUNS. On the grid side there are data aggregators (Our Grid Future,
  Interconnection.fyi, Open Infrastructure Map, ERCOT's TPIT), while SERTP posts its plans as documents.
  **None found pairs two utilities' public transmission plans by distance and timing with page citations.**
- **Adopted inside the decided features (no new scope, no new claim):** the CSV export is laid out like a
  utility conflict matrix (T2.4); the loaded plan editions and their dates are always visible (T1.3);
  shareable links with filters, year and area were already planned (T2.6).
- **Candidates for the founder** (not in Codex's first run unless the founder adds them): a coordination
  window (years left before the earlier in-service year) · an "interregional (SCRTP–SERTP)" label ·
  "next party to act" in the brief · a "partnership-ready" tag · conflict vs opportunity wording · an
  Order 1920 "right-sizing" tag · what changed between SERTP 2025 and the 2026 preliminary plan.
- **Data notes from the research:** SERTP's 2026 Preliminary Expansion Plan Report (Non-CEII) is newer
  than the 2025 plan we load — label our edition; DESC plans in SCRTP, so DESC × Georgia pairs are
  interregional; HIFLD Open was retired on 2025-08-26, so our line geometry is cited as an archived,
  frozen layer with its fetch date; SERTP cost estimates are use-restricted, and our SERTP extract carries
  no costs (checked 2026-09-26).

## Who builds what (decided 2026-09-26)

- **Codex lead: Codex CLI ≥ 0.157.1, model `gpt-6-sol`, `model_reasoning_effort="high"`, on the founder's
  ChatGPT subscription — no API key** (Sol on the subscription proved 2026-09-26 by a one-file smoke task
  run at xhigh, 17,217 tokens; the founder then set **high** for the build). One Codex session runs the
  project end to end from a mission brief: it fans out **up to five** Codex sub-agents (the DATA, API, WEB,
  WEB-2 and DOCS lanes, each in its own git worktree, plus judges and gate reviewers), reviews and merges
  their work behind the quick gate, runs the full verify at every gate and **every judging round**, and
  delivers by **Sat 09:30 EDT** at the latest, earlier if it finishes (Q12).
- **Claude Code (this repo's session):** before the launch, setup, the approved downloads, the Codex proof,
  the design round with the founder and the mission brief; after delivery, **the final reviewer** — it
  judges with Claude Opus agents (a different model from the builders), fixes what it judges worth fixing,
  and sends a large batch of corrections back to Codex with **no Codex judging loop**, then judges again.
- **The founder and team** review Codex's and Claude's results after the hand-off and decide the next round.
- **AI brief inside the product:** Claude API (`claude-opus-5`) only if the founder supplies Claude access
  and a spending ceiling (Q3); otherwise template briefs. Codex never sees the Claude credential.

## Capability map (spec-driven-development Phase 0)

| Module id | Responsibility | Depends on |
|---|---|---|
| `source-data` | Parse both plans into project records: name (verbatim), description, need, status, in-service date + year, cost by column, voltage, project type, miles, source document + real PDF page; stable unique IDs; completeness check | — |
| `geo-placement` | Substation gazetteer (OpenStreetMap, HIFLD line ends, Census towns, hand fixes) → geometry, accuracy label, location source; utility attribution with basis | `source-data` |
| `overlap-engine` | Nearest points (EPSG:5070) → geodesic distance, band, why they touch, timeline gap, score, deterministic rank | `geo-placement` |
| `savings-model` | Savings range or stated reason per overlap, from a sourced assumptions table and plan costs | `overlap-engine` |
| `brief-generator` | Coordination brief per overlap: Claude (grounded, structured) or deterministic template; hash-checked cache; eval set | `overlap-engine`, `savings-model` |
| `api` | FastAPI on 127.0.0.1: health, meta, projects, project detail, overlaps, overlap detail, area, search, briefs, CSV export, source PDFs | build artifacts |
| `web-app` | Map, ranked list, project + overlap detail, filters, timeline slider, city search, area explorer, export, print report, light/dark, local basemap | `api` |
| `verification` | pytest (pipeline, API, grader), Playwright e2e + scripted UI audits, per-merge quick gate, `VERIFY.cmd` full run with baseline | all |
| `ship` | README, methodology, data sources and licences, demo script, Q&A crib, screenshots fallback, presentation outline, Devpost text | all |

Build order: `source-data` → `geo-placement` → `overlap-engine` → (`api` ∥ `web-app` against contracts
frozen at G1a) → `savings-model` → `brief-generator` → `ship`. `verification` grows with every task.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Data pipeline | Python 3.12, `pypdf`, `shapely` 2.x, `pyproj` 3.x | Already built and producing the data |
| API | FastAPI + uvicorn, Pydantic v2 models = the contracts, `create_app()` factory | Typed contracts, TestClient, holds any Claude key server-side |
| AI brief | Anthropic Python SDK, `claude-opus-5`, structured output (Pydantic), `fallbacks: "default"`, adaptive thinking, effort `medium` (tuned by eval), `max_tokens` 16000 | `claude-api` skill defaults; schema-valid output |
| Front end | Static HTML + CSS + vanilla JS ES modules, **no build step**; **Leaflet 1.9.4** vendored (SVG renderer); **local GeoJSON basemap**; native range, datalist, `<dialog>`; theme set by external `web/js/theme-init.js` | Nothing to install; works offline; map features visible to axe/keyboard/print; CSP `default-src 'self'` |
| Tests | pytest + TestClient; Playwright (Python) e2e + axe-core; per-merge quick gate + full `VERIFY.cmd` | One language for tests; Chromium already on the machine |
| Builders | One Codex lead (`gpt-6-sol`, high reasoning) launched by `scripts/codex-lead.ps1`, fanning out up to five sub-agents; `scripts/codex-task.ps1` kept for Claude's correction runs and the fallback | Founder's decision; subscription usage |
| Runtime home | Working clone `%USERPROFILE%\dev\gridlock` (Q8), venv `%USERPROFILE%\dev\gridlock-venv`, Playwright browsers `%USERPROFILE%\dev\ms-playwright`; lane worktrees and run output proven in T0.6 (`%USERPROFILE%\dev\gridlock-wt\<lane>` and `%USERPROFILE%\dev\gridlock-runs` if the sandbox can write there, else inside the working copy, git-ignored) — all outside OneDrive and outside `%LOCALAPPDATA%` | Git worktrees + OneDrive sync conflict; the Claude app redirects its `%LOCALAPPDATA%` writes (profile § Known traps); founder rule |

## Commands (created in Phase 0)

```
Setup:    SETUP.cmd  (-> scripts\setup.ps1 with -ExecutionPolicy Bypass; venv outside OneDrive; pinned requirements.txt)
Build:    python -m pipeline.build_all          (offline; --refresh only to re-download sources)
Run:      START.cmd                              (uvicorn 127.0.0.1:8765, opens the browser; GRIDLOCK_AI from settings)
Test:     python -m pytest -q                    (pipeline + api + grader; GRIDLOCK_AI=off forced)
E2E:      python -m pytest tests\e2e -q          (needs GRIDLOCK_TEST_PORT; no default port)
Gate:     scripts\quick-gate.ps1                 (per-merge, <= 5 min)
Verify:   VERIFY.cmd                             (full matrix on a private worktree; exit 0/1/2/3)
Lead:     scripts\codex-lead.ps1 -Brief <MISSION.md>        (launch the Codex lead; background; resume by session id)
Codex:    scripts\codex-task.ps1 -Lane <lane> -Brief <file>   (one Codex task: corrections after the final review, or the fallback)
Briefs:   python -m pipeline.briefs --top 60     (only with Claude access + ceiling; never in tests)
```

## Project structure (target)

```
SPEC.md  PROJECT-PROFILE.md  CLAUDE.md  AGENTS.md  README.md  LICENSE  SETUP.cmd  START.cmd  VERIFY.cmd
requirements.txt  .gitattributes (CRLF for *.cmd, *.ps1)  .gitignore
.claude/skills/gridlock-build/   workflow skill (+ references/)      .agents/skills/gridlock-build/  same, for Codex
.claude/agents/                  role prompts (reviewers, judges, docs)
tasks/plan.md  tasks/todo.md     plan and task list (checkboxes = progress)
reviews/<date>-<pass>/           BRIEF.md, TRACKER.md, MISSION.md, DELIVERY.md, FINAL-REVIEW.md, briefs and reports
contracts/                       JSON Schema exported from server/schemas.py (frozen at G1a)
pipeline/                        extract, fields, ids, place, classify, overlaps, savings, briefs, build_all
data/raw/                        source documents and GIS inputs (read-only)
data/manual/                     manual_locations.csv, assumptions.json, contacts.json (hand-curated, sourced)
data/build/                      generated: projects.geojson, overlaps.json, meta.json, places.json, basemap.json
data/briefs/                     cached briefs, one JSON per overlap id (committed)
server/                          app.py, queries.py, schemas.py, briefs.py, search.py, area.py, settings.py
web/                             index.html, print.html, css/, js/, icons/, vendor/
tests/                           pipeline/, api/, eval/, e2e/ (+ fixtures/)
scripts/                         setup.ps1, verify.ps1, quick-gate.ps1, start.ps1, worktree.ps1, codex-task.ps1 (ASCII)
docs/                            METHODOLOGY.md, DATA-SOURCES.md, DEMO.md, QA-CRIB.md, PRESENTATION.md, DEVPOST.md, screenshots/
```

## Contracts (frozen at gate G1a; changed only by the Codex lead with a recorded reason, a fresh type review and every fixture re-validated — in the tracker and `DELIVERY.md`)

- **Project** (GeoJSON Feature; geometry Point | LineString | MultiLineString | null):
  `id` — DESC `desc-p<N>` where N = "Project N of 54" (verified 2026-09-26: project N is on PDF page N for
  all 54); SERTP `sertp-p<page>-<hash6 of normalised name + description>` with `-2`, `-3` suffixes in
  document order on collision (p.133 lists one project twice) · `project_id` (utility's own ID as printed,
  may repeat, e.g. "6809 M") · `utility` · `utility_basis` (`stated` | `inferred_from_location`) · `name`
  and `description` **verbatim** (dashes kept) · `need` · `status` · `in_service` (as printed) · `year` ·
  `cost_usd` · `cost_basis` (`plan` | `proxy` | `none`) · `cost_flags[]` (`printed_total_differs_from_sum`,
  `below_list_threshold`) · `voltage_kv[]` · `project_type` (new_line · rebuild_line · reconductor ·
  new_substation · substation_upgrade · equipment · other) · `miles` · `endpoints[]` · `state` ·
  `accuracy` (exact · approximate · unknown) · `location_source` · `source {doc, page, url}` (real PDF page).
- **Overlap**: `id` (`<idA>__<idB>`, sorted) · `a`, `b` · utilities · `distance_km` (geodesic between the
  nearest points) · `band` (touching · lt_1_6km · lt_8km · lt_40km) · `band_label` · `touch_reason`
  (same_substation · shared_endpoint · lines_cross · proximity · same_area_approximate) · `touch_detail`
  (e.g. "Tie line ends at McIntosh; the DESC work is at the new Deerfield switching station, location not
  stated") · `can_share` (from band **and** touch reason) · `a_year`, `b_year`, `year_gap`, `timeline` ·
  `cross_state` · `pair_note` (e.g. Georgia-only pairs: "May already plan jointly through Georgia's
  Integrated Transmission System") · `accuracy_pair` (the weaker of the two) · `score` · `rank` ·
  `savings {status: range | timing_too_far | no_cost | unknown_year, low_usd, high_usd, basis, assumption_ids[]}`
  · `brief_status` (cached | stale | template | none).
- **Brief**: `overlap_id` · `what` · `where` · `when` · `what_to_share[]` · `savings_range {status,
  low_usd, high_usd, basis}` · `who_to_contact[]` (organisations / planning functions from
  `data/manual/contacts.json` only — never a person, email or phone) · `caveats[]` · `sources[]` ·
  `generated_by` (model id or `template`) · `prompt_version` · `generated_at` · `input_hash`.
- **Area**: `center` · `radius_km` (default 40, 1–80) · `projects[]` · `overlaps[]` (≥ 1 project inside) ·
  counts by utility and band.
- **Meta**: build time · source documents with dates · counts per pipeline stage · counts by utility,
  accuracy, band · `no_overlap_count` · `unmapped_count` with reasons · `stale_brief_count`.
- **SearchResult**: `type` (place · project · substation) · `label` · `lat`, `lon` · `ref`.
- API errors: `{"error": {"code", "message"}}`; 4xx for bad input, never a stack trace.

**Overlap rules:** touching when distance ≤ 1 m; otherwise the first band with distance **<** its limit
(1,600 m · 8,000 m · 40,000 m); nothing at ≥ 40,000 m. Pairs only between different utilities. Rank by
score (band weight × timeline factor × accuracy factor × 1.5 if cross-state — savings are **not** in the
score), ties broken by distance then `id`; rebuilds are byte-identical. A filter keeps an overlap when
**both** its projects pass the project filters and the overlap passes the band / cross-state filters.

## Code style

Python: type hints, small pure functions for geometry and scoring, Pydantic at the API boundary, no global
mutable state beyond read-only artifacts loaded at startup. JS: ES modules, `textContent` for every data
string (never `innerHTML` with data; Leaflet tooltips and popups get DOM nodes, not strings), one module
per surface. CSS: tokens on `:root`, light and dark. Data strings are shown verbatim (`data-src` attribute
on elements that render them); the product's own wording follows the glossary in `PROJECT-PROFILE.md`.

```python
TOUCH_TOLERANCE_M = 1.0
BANDS = ((1_600.0, Band.LT_1_6KM), (8_000.0, Band.LT_8KM), (40_000.0, Band.LT_40KM))

def band_for(distance_m: float) -> Band | None:
    """Nearest-point distance in metres -> the challenge's band, or None at 40 km and beyond."""
    if distance_m <= TOUCH_TOLERANCE_M:
        return Band.TOUCHING
    return next((band for limit_m, band in BANDS if distance_m < limit_m), None)
```

## Testing strategy

- **Pipeline:** date/year parsing (invalid dates "04/31/26", phased dates); costs by column with
  `cost_flags`; voltage/type; Unicode normalisation; **IDs unique**; each cited page's text contains the
  project's name or ID; stage counts reconcile; parser completeness (every "Project Name:" marker is a row
  or a listed exclusion — the 32 TVA entries on pp. 171–181 use "In- Service"); band boundaries at
  1 / 1.01 m, 1,599.99 / 1,600 m, 7,999.99 / 8,000 m, 39,999.99 / 40,000 m; touch reasons; savings statuses;
  byte-identical rebuild.
- **API:** every route happy path + bad input (422/404) + response validated against the contract on
  every path (live, cached, stale, template, empty) · CSV == list for the same filters (UTF-8 **with BOM**;
  cells starting `= + - @`, tab or CR escaped; numbers never escaped) · area counts equal a hand-computed
  case · brief cache path traversal refused · POST `/generate` refused without the custom header /
  same-origin / key, and capped · **the test server opens no outbound connection** (socket guard) ·
  source PDF route returns 200 `application/pdf` for known docs only.
- **Brief eval:** 30 real overlaps (20 dev / 10 held out); deterministic grader with number normalisation
  and an allowed-constants list (`references/ai-brief.md`); the template passes 30/30; every cached brief
  re-graded in VERIFY; a brief whose `input_hash` no longer matches is served as template and counted stale.
- **E2E (Playwright, `GRIDLOCK_TEST_PORT`):** the demo path; each feature's primary action; project and
  overlap detail; deep links incl. unknown, stale and filtered-out IDs; URL state for filters, year, area,
  selection; keyboard-only run; non-local requests blocked; no Claude access; races (selection or slider
  changes while a detail, brief or area loads); malicious-string fixture through list, detail and map
  tooltip; 1440 and 390 px (+ overflow at 768 and 320); light and dark.
- **Per-merge quick gate (≤ 5 min, every merge):** compileall · pytest · e2e smoke at 1440 light (demo path
  so far) · 0 console errors · axe on the default state. **Full matrix at gates** (`VERIFY.cmd`). The
  baseline counts passing checks; every skip is on a named allow-list with its reason.

## Boundaries

- **Always:** reproduce before fixing; a test per fix in the canonical suite; commit per task; show data
  verbatim with source document + page; label estimates "estimate" and AI text "AI-drafted"; keep unknowns
  visible; name the Codex model explicitly in every dispatch.
- **Ask first:** a new dependency or download; any Claude API spend (quote, probe, ceiling); pushing to the
  public repo; changing a frozen contract; cutting a decided feature; anything touching another lane's files.
  Claude asks the founder. The Codex lead runs unattended and cannot ask: it takes the safe default (no
  new dependency, no spend, no push; a contract change only as the contract heading above says; a cut
  feature hidden from the demo path, never deleted; another lane's file only by reassigning the task) and
  lists the question for the founder in `DELIVERY.md`.
- **Never:** invent data, contacts or numbers; use CEII or secure-area material; print, log or commit a
  secret; install into OneDrive; weaken or skip a test to get green; deploy or submit without the founder;
  give Codex the Claude credential.

## Success criteria (done-when)

1. From a fresh clone of the public repo: `SETUP.cmd` → `VERIFY.cmd` exits 0 with totals ≥ baseline;
   `START.cmd` shows map + ranked list in under 3 s.
2. Demo path in ≤ 6 clicks, 0 console errors: search "Savannah" → open the top Savannah pair → both
   projects, distance, band, why they touch (worded exactly as the PDFs support), years, source doc + page,
   accuracy, savings range or reason, brief.
3. Both required deliverables and the bonus are demonstrable exactly as the challenge words them.
4. UI audits pass at 1440 and 390 px, light and dark.
5. Data honesty: every mapped project has source doc + real page and an accuracy label; unmapped and
   no-overlap counts visible; named-example table complete; held-out brief eval 10/10.
6. Works with the network off and with no Claude access.
7. Submission: public repo scrubbed of local paths (Q11) with README, methodology, data sources and
   licences; Devpost drafted early and finalised from the shipped app; screenshots fallback; submitted by
   **10:30 EDT Sunday**.

## Open questions

**Decided (founder, 2026-09-26):**
- **Q6 Downloads** — "Approve all": the list in `tasks/plan.md` § Downloads, fetched by Claude before the
  launch (the Codex sandbox has no network).
- **Q9 Design direction** — impeccable's direction round (the founder locks one of the dealt directions;
  ~45–60 min agent time + ~10 min of theirs). *If the founder is away when every other launch task is
  done, the assigned direction is used and the founder is told (the skill's own unattended rule).*
- **Q12 Hand-off** — the Codex lead delivers by **Sat 2026-09-26 09:30 EDT** at the latest, earlier if it
  finishes ("Sat 9:30 am so me and my team can review yours and codex results … and we can build";
  "codex can deploy by 9:30 … it can finish earlier than that"). Its delivery judging round starts 30
  minutes before the hand-off (plan D16); Claude's final review starts at delivery; the founder and team
  review both results, and the next round is the founder's call.

**Have a default (answer any time):**
- **Q1 Team** — roster, roles, Discord tags, first-time hackers. *Default: founder + agents; placeholders.*
- **Q2 CEII** — Sperry confirms the SERTP 2025 overview plan is usable. *Default: use it. If Sperry says no:
  plan B — ask Sperry for their intended dataset; else the Georgia Power IRP docket 56002 (about 3 hours of
  DATA work, estimate); the founder decides.*
- **Q3 Claude access for briefs** — `ant auth login` or env var on this laptop (never in chat) plus a
  spending ceiling (suggested $20: probe + ~60 briefs + eval runs + one regeneration after the final
  review). Codex builds the generator against a fake client; any real call runs in Claude's final phase
  after the founder's yes. *Default: template briefs only.*
- **Q4 Slider range** — in-service years run 2026–2035 (15 of 230 after 2032). *Default: the data's range.*
- **Q5 Licence** — *Default: MIT for our code;* data keeps its own terms.
- **Q7 Pushes** — *Default: Codex never pushes; Claude pushes only after the founder says yes each time.*
- **Q8 Working location** — *Default: clone to `%USERPROFILE%\dev\gridlock` and work there; the OneDrive
  copy is left untouched (nothing deleted).*
- **Q10 Codex model** — *Decided: `gpt-6-sol` at **high** reasoning on the subscription (founder, 2026-09-26: "use gpt 6 sol high not xhigh"); up to five Codex sub-agents at a time (founder's choice).*
- **Q11 What is public** — the repo is public: the SERTP PDF (headers read "(CEII)") and a Dominion
  route-map PDF are already in it. *Default: no new third-party documents committed; local paths scrubbed
  before each push; the route-map PDF removed at the next push; if Sperry says no on Q2, remove the SERTP
  PDF and purge it from history — only with the founder's yes (history rewrite).*
