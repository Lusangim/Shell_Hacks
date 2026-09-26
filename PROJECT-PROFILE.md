---
title: GridLock (ShellHacks 2026) — project profile
type: project-profile
kind: client-software
status: active
updated: 2026-09-26
---

# GridLock — project profile

Template: the founder's workflow vault `lucky-workflow/references/project-profile-template.md` (read-only).
Workflow for this repo: `.claude/skills/gridlock-build/SKILL.md` (Codex: `.agents/skills/gridlock-build/`).
Spec: `SPEC.md`.

## What it is, for whom, and the bar

A web app for the Sperry Tech GridLock Challenge (ShellHacks 2026, FIU, Sep 25–27): it places two
neighboring utilities' public planned transmission projects on a map, finds pairs within 40 km with
overlapping timelines, ranks them by a transparent score (distance band × timeline × location accuracy,
cross-state weighted — savings are shown, not scored), estimates savings as a range with its assumptions,
and drafts a coordination brief. Judged live: Round 1 one general judge (3 min) with the sponsor judging
separately; Round 2 3–5 min. Prizes: 1st guaranteed internship + laptop; 2nd interview + laptop; 3rd
interview (Notion Hacker Guide). The founder's bar, in their words: "complete from front to backend …
working with no bugs and have a clean UI … per the MVP we made together."

## Where it lives

| What | Path |
|---|---|
| Repo (public) | https://github.com/Lusangim/Shell_Hacks |
| Working clone (Q8) | `%USERPROFILE%\dev\gridlock` (the OneDrive copy is left untouched) |
| Plan, tasks, spec | `SPEC.md` · `tasks/plan.md` · `tasks/todo.md` |
| Pass folder | `reviews/2026-09-26-gridlock-build/` (BRIEF, TRACKER, MISSION, DELIVERY, FINAL-REVIEW, briefs, reports) |
| Notes (not in repo) | the founder's Obsidian notes for this hackathon (hacker-guide notes, feature list) |
| Outside OneDrive and AppData | venv `%USERPROFILE%\dev\gridlock-venv` · worktrees `%USERPROFILE%\dev\gridlock-wt\<lane>` (or `.wt\<lane>` in the clone, per T0.6) · runs `%USERPROFILE%\dev\gridlock-runs` · Playwright browsers `%USERPROFILE%\dev\ms-playwright` (`PLAYWRIGHT_BROWSERS_PATH`) |
| Challenge source | Notion "Hacker Guide" page `cade86546e9182339a8701de4fddc32e` (re-fetch; organisers update it) |

## Never touch

- The founder's workflow vault (Lucky Systems) — read-only (founder, 2026-09-26: "DO NOT CHANGE ANYTHING").
- `data/raw/*` source documents — read-only inputs.
- Port **8765** while the founder demos; Codex lead 8770; lanes 8771–8775; judges 8781–8785; verify 8790.
- Credentials: Claude access (`ANTHROPIC_API_KEY` / `ant` profiles), `gh` token, anything under
  `%USERPROFILE%\.codex\` (auth.json, config.toml) — never read, printed or passed to an agent.
- SERTP "Secure Area" and SCRTP CEII-NDA material — never requested or used.

## Originals — what "exactly like the original" means here

No client originals. The deliverable follows the **challenge text** (Hacker Guide, GridLock section),
quoted in `SPEC.md`. Data facts follow the **source PDFs** page by page (DESC SCRTP 2026–2030 list;
SERTP 2025 overview plan): names and descriptions are shown verbatim, with document + real page.

## Standing rules for this project

- 2026-09-26 founder: scope GA + SC, core story the SC–GA border; all decided features in scope.
- 2026-09-26 founder: plan first; nothing built before approval.
- 2026-09-26 founder: builders are Codex `gpt-6-sol` at **high** reasoning on the ChatGPT subscription — "i want to use
  my subscription usage no api", then "use gpt 6 sol high not xhigh"; Codex CLI updated to 0.157.1 on the founder's word.
- 2026-09-26 founder, operating model: "remove the schedule"; one Codex lead runs the whole project, fans
  out **up to 5** sub-agents (the founder's choice for Codex's own fan-out; Claude's agents stay ≤ 3) and
  goes "through all the judging rounds it needs"; Claude is "the last reviewer" and routes a large bug
  batch back to Codex without a Codex judge loop, then judges it. Codex delivers by **Sat 09:30 EDT** at
  the latest ("it can finish earlier than that"); the founder and team then review and keep building.
- 2026-09-26 founder: all listed downloads approved ("Approve all"); design by impeccable's direction round.
- Nothing invented: unknowns stay "unknown"; estimates say "estimate" and show assumptions; AI text says
  "AI-drafted"; contacts are organisations / planning functions, never people.
- Public data only; nothing marked CEII (Q2 pending with Sperry). Nothing outward without the founder.
- **Glossary (one term per concept):** *project* · *utility* (Dominion Energy SC, Georgia Power, Georgia
  Transmission Corp., MEAG Power, Dalton Utilities, Georgia ITS (joint); "Georgia Power (inferred)" when
  the plan names only Southern Company) · *overlap* (two projects from different utilities within 40 km,
  nearest points) · *coordination opportunity* (an overlap as ranked in the list) · *distance band*
  (Touching / Under 1.6 km / Under 8 km / Under 40 km) · *why they touch* (Same substation / Shared
  endpoint / Lines cross / Close by / Same area, approximate) · *in-service year* ("enters service in") ·
  *accuracy* (Exact / Approximate / Unknown) · *source* (document + page) · *savings estimate* (a range,
  or the reason there is none) · *coordination brief* (AI-drafted or Template) · *cross-state*.

## House patterns (the cheat sheet)

`.claude/skills/gridlock-build/references/house-patterns.md` — written at G1 from the skeleton with
`path:line` examples; until then lanes follow `SPEC.md` § Contracts and § Code style.
**Do not read (WEB and API lanes):** `data/raw/*`, `data/build/*` (use the API, the schema or the
fixtures), `web/vendor/*`, other lanes' folders. **DATA** reads `data/raw/*` through the pipeline and may
open a PDF page to check a value; nobody reads `%USERPROFILE%\.codex\`.

## Environment recipe

- Python 3.12.4 (`%LOCALAPPDATA%\Programs\Python\Python312\python.exe`) → venv
  `%USERPROFILE%\dev\gridlock-venv` via `SETUP.cmd`; pinned `requirements.txt`. Always call Python by full
  path (`$env:GRIDLOCK_PY` = the venv's `Scripts\python.exe`); the Microsoft Store `python` alias cannot
  start inside Codex's sandbox. **Never create tool state under `%LOCALAPPDATA%` from the Claude app** —
  see Known traps.
- Codex CLI 0.157.1 at `%LOCALAPPDATA%\Programs\OpenAI\Codex\bin\codex.exe`, ChatGPT sign-in; dispatch
  with `scripts\codex-task.ps1` (model named explicitly: the user config's default was rejected on 0.154).
  Sandbox: workspace-write, network restricted, localhost binding works (proved 2026-09-26).
- Node 24 is used only by the Q9 design round (impeccable's `.mjs` scripts). Playwright 1.63.0 needs
  Chromium build 1243; the machine had only 1223/1234, so 1243 is installed in
  `%USERPROFILE%\dev\ms-playwright` and every script sets `PLAYWRIGHT_BROWSERS_PATH` to it.
- Windows traps: write files with the Write tool; `.ps1`/`.cmd` ASCII, CRLF via `.gitattributes`;
  PowerShell 5.1 (no `&&`; embedded quotes in native arguments split — pass prompts via stdin files);
  quote paths with spaces; prove a process is ours before stopping it; keep the laptop awake.
- Disk: 24.6 GB free (2026-09-26); Codex keeps ~4.3 GB of session history.

## Verify recipe (what `/verify` runs) — created in T0.4

- **Per merge:** `scripts\quick-gate.ps1` (≤ 5 min): compileall · pytest (with `GRIDLOCK_AI=off` and the
  outbound-socket guard) · e2e smoke at 1440 light on `GRIDLOCK_TEST_PORT` · console errors · axe default.
- **Per gate:** `VERIFY.cmd` → `scripts\verify.ps1`: private worktree at HEAD → compileall → pytest →
  uvicorn on 8790 → Playwright e2e + the full audit matrix (six states × 1440/390 × light/dark) →
  `<runs>\<stamp>\summary.md` (`%USERPROFILE%\dev\gridlock-runs`, or `.runs\` in the clone per T0.6). Exit **0** green · **1** failed · **2** green but
  fewer passing checks than `scripts\verify-baseline.json` · **3** could not start. Skips only via the
  named allow-list. Flake policy: re-run 3× quietly; a repeat is a defect. Expected totals: set at G1a.
- Non-developer before a demo: double-click `VERIFY.cmd`, then `START.cmd`.

## Auditor lenses for this project

| Lens | Why | What it measures |
|---|---|---|
| **domain expert** (transmission planner / Sperry engineer) — spot-check at G2, full at G4 | One wrong number or overstated claim loses the room | Re-derive 5 distances; bands, years, costs, voltages and sources against the PDFs; "why they touch" wording |
| **first-week user / 3-minute judge** | The demo is 3 minutes | Time and clicks to find and understand the top pair cold |
| **ui / design** ("clean UI") | Founder's explicit bar | ui-contract critique procedure + scripted audits |
| **reliability** | "No bugs" | Bad input, no network, no Claude access, races, deep links, 390 px, empty results |
| **security** | Keys, PDF-derived text in prompts and UI, localhost POST | CSRF on POST, XSS incl. map tooltips, traversal, CSV formulas, outbound calls |
| **business / hackathon fit** | Prizes depend on the brief | Every required deliverable and bonus as worded; honest claims; README/Devpost/demo |

## Known traps

- 2026-09-26 SERTP "Southern" list includes Alabama/Mississippi; unprefixed rows placed in GA are
  "Georgia Power (inferred)"; unplaced ones are counted as unmapped, not dropped silently.
- 2026-09-26 "Goshen" exists near Savannah ("SAV:") and near Augusta (MEAG) — region-scope lookups.
- 2026-09-26 "0 km" usually means a shared substation point; the DESC Okatie–McIntosh work is at the new
  Deerfield switching station — say "shared endpoint", not "same substation".
- 2026-09-26 Okatie location is inferred (HIFLD tap on Jasper–Yemassee), not verified.
- 2026-09-26 SERTP p.133 lists one project twice; DESC project_id "6809 M" repeats; IDs must not key on them.
- 2026-09-26 32 SERTP entries (TVA, pp. 171–181) print "In- Service" and were missed by the v0 parser.
- 2026-09-26 DESC 6846 A prints a total ($1,238,443) that differs from its year columns ($2,088,443).
- 2026-09-26 211 of 326 Southern project names contain en dashes — show data verbatim; lint only our words.
- 2026-09-26 the guide's "Urquhart vs Thomson–Vogtle" and "Bluffton" examples are not in the loaded plans.
- 2026-09-26 overpass-api.de returned 406 to a bare request; the kumi.systems mirror worked.
- 2026-09-26 extract.py once shipped broken because a patch was committed without re-running it.
- 2026-09-26 Codex 0.154 rejected `gpt-6-sol` on the subscription; 0.157.1 accepts it. The Store `python`
  fails in Codex's sandbox. Three user-level Codex MCP servers (Hugging Face, n8n, Notion) error at start.
- 2026-09-26 the Claude desktop app is an MSIX package: files its processes create under `%LOCALAPPDATA%`
  are redirected to `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local\…` (a venv made there
  printed "Actual location … Packages\Claude_…"), invisible to the founder's own terminal and possibly to
  Codex's sandbox. Keep the venv, runs and browsers under `%USERPROFILE%\dev\`.
- 2026-09-26 an auto-compaction right after loading the long `/last30days` skill left a session unable to
  answer; run long-instruction skills inside a sub-agent.

## Open founder inputs

`SPEC.md` § Open questions (Q6, Q9, Q10 and Q12 decided 2026-09-26; the rest have defaults).

## History

- 2026-09-26 — research, data pipeline v0 (230 projects, 181 placed, 477 overlaps, 44 cross-state),
  preview map, public repo; plan v1; independent gap review (22 findings) → plan v2; Codex CLI 0.157.1
  proven with `gpt-6-sol` on the subscription (smoke test at xhigh; the build runs at high, founder's choice).
- 2026-09-26 — plan v3: the founder's operating model (Codex lead + up to five sub-agents builds and
  judges; Claude reviews last; no clock schedule; hand-off by Sat 09:30); prior art (PaverOps and peers).
