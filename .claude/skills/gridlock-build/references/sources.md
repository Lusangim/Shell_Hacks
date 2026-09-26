# Sources — what this workflow took from where, and what it left out

Every source was read, not installed: nothing from these sources was downloaded into the workspace, no
installer or hook of theirs ran, and the founder's workflow vault (Lucky Systems) was only read (founder's
instruction, 2026-09-26: "DO NOT CHANGE ANYTHING"). What fits was rewritten here in our own words for this
repo, this machine (Windows 11, PowerShell 5.1, OneDrive) and a 33-hour deadline. The one install on the
founder's word — the Codex CLI update — is recorded below.

## Lucky Systems workflow (the founder's own; read-only at `...\Lucky Systems\.claude\`)

| Their part | Ours | Note |
|---|---|---|
| `lucky-workflow` router: intake → route → frame → audit → isolated waves → verify → judges → close-out | `SKILL.md` §1–§9 | Route L shape kept; audit folded into gates because the product is new, not inherited |
| Standing rules: nothing outward, nothing invented, placeholders visible, Opus, ≤ 3 agents, results first | `SKILL.md` §0 | Verbatim intent; the Codex lead's own fan-out is up to 5 (founder's choice, 2026-09-26) |
| `project-profile-template.md` | `PROJECT-PROFILE.md` | Originals = the challenge text; lenses chosen for this product |
| `pass-templates.md` (BRIEF, ownership table, tracker, relay, confirmation round) | `references/agent-prompts.md` (mission brief, sub-agent and judge briefs), T0.5 pass folder | Worktrees replace folder copies because this repo has git |
| Roles `pass-fixer` / `pass-judge` / `pass-auditor` / `change-reviewer` / `security-reviewer` / `docs-truth` | `.claude/agents/gridlock-*.md` (T0.5) | Adapted: git worktrees, ports 8771–8774, this repo's never-touch list |
| `/verify` (quiet machine, fewer checks = finding, classify red lines, flake re-runs) | `SKILL.md` §5, profile verify recipe | Exit codes 0/1/2/3 kept |
| `/checkpoint`, `interruptions.md` (resume, never relaunch) | `SKILL.md` §3 | Tracker is the state |
| `eval-sets.md` (question set first, held-out third, before/after) | `references/ai-brief.md` | Deterministic grader instead of paraphrase checks |
| `auditor-lenses.md` | Profile § Auditor lenses | domain expert · first-week user · design · reliability · security · business fit |
| `examples/lucky-systems-website.md` (contract + cheat sheet + "do not read" list; scripted auditors as merge gate; hardest page first) | D9, house-patterns, ui-contract | The hardest surface first = the detail panel for #1 |
| `rules/windows-tooling.md` | Profile § Environment | Heredoc backslashes, ASCII `.ps1`, quoting, Modern Standby |
| Design craft skills (`impeccable`, `taste-skill`, `emil-design-eng`, `apple-design`, `pick-ui-library`, `prototype`, motion skills) | `references/ui-contract.md` | Digest by a read-only research agent |

## `agent-skills` — Addy Osmani (MIT; installed user-level 2026-09-02; repo read 2026-09-26)

| Their part | Ours |
|---|---|
| `spec-driven-development` (six areas, capability map, gated phases) | `SPEC.md` |
| `planning-and-task-breakdown` (vertical slices, acceptance + verify per task, checkpoints, `tasks/plan.md` + `tasks/todo.md`) | `tasks/` |
| `incremental-implementation` + `test-driven-development` (RED → GREEN → commit per task; Prove-It for bugs) | `SKILL.md` §2 |
| `/build auto` rule: stop and ask on ambiguity, failing builds, anything irreversible or touching secrets | `SKILL.md` §0 and §2 |
| `/ship` fan-out: code review · security · tests → go/no-go + rollback plan | Judge rounds (§6) and G5 |
| `references/definition-of-done.md` | `references/definition-of-done.md` (tailored) |
| `references/accessibility-checklist.md`, `security-checklist.md`, `performance-checklist.md` | Loaded by WEB, JUDGE lanes |
| `references/orchestration-patterns.md` (fan-out with merge; personas never call personas; research isolation) | The Codex lead fans out and merges; judges never build; ≤ 3 Claude agents |
| Not taken: its Haiku `Explore` suggestion for research helpers | Founder's rule: agents run on Opus |

## Hackathon skill — Ian Too (`ianktoo/hackathon-skill`, SKILL.md v1.3.0)

Read 2026-09-26. The SKILL.md header says MIT, but the repository has **no LICENSE file**, 0 stars, last
push 2026-04-29, and ships the same file three times for different agent runtimes. Not installed —
installing it would add a second router beside this one. Rebuilt in our words:

| Their idea | Ours |
|---|---|
| Always know the deadline; recompute hours left before every recommendation | `SKILL.md` §0–§1 |
| Scope-cut order: core demo flow > error handling > polish > stretch | `tasks/plan.md` § Scope ladder |
| Emergency scope cut at ≤ 2 hours: list done/undone; cut, fake honestly, or finish if < 30 min | `SKILL.md` §7 (we stub honestly, never fake data) |
| Demo prep: scripted click path + screenshot fallback; recorded video 60–90 s | `references/ship-checklist.md` |
| Submission checklist: repo public, README, licence, links tested from a fresh browser | `references/ship-checklist.md` |
| Presentation outline (problem, solution, demo, how it works, impact, next, team) | `docs/PRESENTATION.md` (T5.3) |
| Not taken: team formation and idea phases (done), install-per-teammate step, "fake it" for demos | — |

## ECC — Affaan Mustafa (`affaan-m/ECC`, MIT)

Read 2026-09-26 through `gh api` only (a research agent, then root re-checked the key facts). This is
the **original** project, renamed from `affaan-m/everything-claude-code` (same repository id
1136590548; the old name redirects), MIT with a LICENSE file, last push 2026-09-24, v2.2.x, ~5,000 files:
68 agents (64 pinned to Sonnet/Haiku), 292 skills, 94 commands, 121 rule files, ~44 hooks on by default.
The Lucky vault's 2026-09-19 evaluation (note 31) read an unlicensed re-upload; this one reads the source.

**Not installed, nothing copied verbatim.** Since the vault's evaluation, the `.md`-blocking hook became a
warning (`scripts/hooks/doc-file-warning.js`), but new always-on hooks refuse the first edit of each file
and the first shell command of each session until facts are restated (`gateguard-fact-force.js`), rewrite
dev-server commands into separate windows on Windows (`auto-tmux-dev.js`), format with `npx` fallbacks at
the end of each turn, log every tool call's input/output outside the project
(`continuous-learning-v2/hooks/observe.sh`), and start MCP servers to probe them; `rules/common/*` still
require proactive parallel agents, 80 % coverage, Haiku/Sonnet routing and a settings change
(`includeCoAuthoredBy: false`). All conflict with the founder's standing rules.

| Their idea (source path) | Ours |
|---|---|
| Grounded plan: "patterns to mirror" with `path:line` from existing code, a validate command per task, approval before code (`agents/planner.md`, `commands/plan.md`) | `house-patterns.md` cites real lines; every task has a Verify line; gate G0 |
| Lean PRD with visible "TBD — needs validation via {method}" (`commands/plan-prd.md`) | `SPEC.md` open questions carry a default and how it gets answered |
| Ceremony sized by risk; security review whenever a change touches input handling, external APIs, file paths or secrets (`skills/orch-pipeline`, `orch-build-mvp`) | `references/definition-of-done.md` § Security trigger |
| Lane cards: owner, scope, must-not-touch, acceptance, merge gate, handoff file; steps self-contained for a fresh agent (`skills/blueprint`, `parallel-execution-optimizer`, `team-agent-orchestration`) | Ownership table + `references/agent-prompts.md` + `REPORT.md` handoff |
| Contract first: one machine-checkable source of truth per boundary; front end builds on schema-valid fixtures; every response path validated (live, cached, fallback, empty) (`skills/contract-first`) | T0.3a JSON Schema export + fixtures; schema-conformance tests on every path |
| Verification report PASS/FAIL → READY / NOT READY; stop and ask when a fix adds errors, the same error survives 3 tries, a fix needs architecture change, or a dependency is missing (`skills/verification-loop`, `commands/build-fix.md`) | `SKILL.md` §2 stop rules; verify summary |
| Evidence trail: each task → its test, failing output before, passing output after; never report PASS for what did not run (`skills/tdd-workflow`) | Agent `REPORT.md` format |
| Evals before prompt work; code checks → schema/regex → rubric → human; critical checks must pass every run (`skills/eval-harness`) | `references/ai-brief.md`: every cached brief passes the grader before it is saved; founder reads a sample |
| Twin paths: assert the required fields on every variant (live / cached / fallback brief; CSV / print; API / fixture) (`skills/ai-regression-testing`) | Tests in T2.4, T2.9, T3.3a |
| Pipeline hygiene: rules first with reason codes; content-hash caches keyed by input + prompt version + model; hunt swallowed errors; structured fields only into prompts; strip hidden Unicode (`skills/regex-vs-llm-structured-text`, `content-hash-cache-pattern`, `agents/silent-failure-hunter.md`) | Stage-count reconciliation in the pipeline; brief cache key; Unicode normalisation in T1.1 |
| FastAPI: `create_app()` factory, data loaded once at startup, settings object for the key, typed response models, fake LLM client via dependency overrides, spend ceiling before each call, no blocking client in async routes, no wildcard CORS (`skills/fastapi-patterns`, `rules/python/fastapi.md`, `skills/cost-aware-llm-pipeline`) | T1.2, T3.2 acceptance |
| Reviewer calibration: report only confident findings with the line, the input that fails, callers read; zero findings is valid (`agents/code-reviewer.md`) | Judge and reviewer prompts |
| Front-end QA: map what each shared-state setter sets and resets; races (slider moved while a brief loads); 375/768/1440 screenshots; SHIP / SHIP WITH FIXES / DO NOT SHIP (`skills/click-path-audit`, `browser-qa`) | Reliability lens; stale-response guard in T2.5b/T3.3b; 768 px overflow check |
| Stable browser tests: role/test-id locators, wait on responses not sleeps, run new tests 3–5× for flakiness; rehearsal script that fails loudly before recording a demo video (`skills/e2e-testing`, `skills/ui-demo`) | T1.4a conventions; T5.2 |
| Named checkpoints (time + commit + test counts); handoff sections (worked with evidence · failed with exact error · file states · decisions · one next step); compact only at phase boundaries; cut list ranked by impact × confidence ÷ effort (`commands/checkpoint.md`, `save-session.md`, `skills/strategic-compact`, `product-lens`) | TRACKER format; scope ladder ordering |

**ECC agents (second pass, 2026-09-26, founder request — "look into ECC repo and its agents"):** all 68
read through `gh api`. Adopted as rewritten role files over one checklist file
(`references/review-checklists.md`, sections credited per source): `code-reviewer` (gating → §A and
`gridlock-reviewer`) · `python-reviewer` + `fastapi-reviewer` (§B, `gridlock-python-reviewer`) ·
`silent-failure-hunter` (§C, `gridlock-silent-failure`) · `typescript-reviewer` JS parts (§D,
`gridlock-js-reviewer`) · `pr-test-analyzer` + `tdd-guide` (§E, `gridlock-test-analyzer`) · `a11y-architect`
(§F, `gridlock-a11y`; WCAG 2.2 references corrected) · `type-design-analyzer` (§G, `gridlock-type-design`) ·
`gan-evaluator` (§H, in `gridlock-judge`) · `opensource-sanitizer` (§I, `gridlock-sanitizer`, never previews
secrets, never squashes history) · `e2e-runner`, `build-error-resolver`, `loop-operator` as rules only
(§J, §K, §L). Avoided: `build-error-resolver`/`refactor-cleaner`/`code-simplifier`/`performance-optimizer`/
`doc-updater` as agents (they install, run npx, delete code or commit), the GAN generator/planner loop,
`chief-of-staff` (sends messages, pushes), `harness-optimizer` (edits settings), `opensource-forker`
(rewrites history), and every other-language reviewer.

**Not taken:** any install (plugin, `npx` installer, hooks runtime, rules copy); the agents as shipped
(self-invoking descriptions); outward or external-model tools (`commands/multi-*`, `santa-loop` which pushes, autonomous
`claude -p` loops); the continuous-learning observer; tmux workflows; the GAN build loop (ECC's own
estimate 4–6 hours and $125–200 per app); multi-browser test matrices and global `npm install`; MCP
config templates (`npx -y …@latest`); its model prices (the `claude-api` skill is the pricing source);
the glass/grain/bento style menu (wrong target for a planning tool; its anti-template list agrees with
`ui-contract.md`).

## Claude API skill (bundled with Claude Code)

Model, structured-output, refusal-fallback, caching and pricing facts for the coordination brief:
`references/ai-brief.md`. The skill's files are authoritative over memory; re-read before coding.

## Codex CLI (OpenAI) — the builders

Founder's decision 2026-09-26: build work goes to Codex on the ChatGPT subscription ("i want to use my
subscription usage no api"), model `gpt-6-sol`, then set to **high** reasoning ("use gpt 6 sol high not xhigh"). Facts established that day, read-only except the
update the founder asked for:
- CLI updated 0.154.0 → 0.157.1 with OpenAI's own installer (`codex update`); on 0.154 the subscription
  rejected `gpt-6-sol`; on 0.157.1 it ran (17,217 tokens for a one-file smoke task).
- `codex doctor`: ChatGPT sign-in; sandbox restricted filesystem + restricted network; approval on request
  by default (we pass `approval_policy="never"` and `-s workspace-write` per task); three user MCP servers
  fail at start (Hugging Face auth, a missing n8n workspace, a revoked Notion grant) — left as they are.
- `codex sandbox` proved: real Python 3.12 runs, localhost binds, writes are confined; the Microsoft Store
  `python` alias cannot start in the sandbox → Python is always called by full path.
- OpenAI's own model list describes `gpt-6-astra` as "Frontier intelligence for the most demanding work"
  and `gpt-6-sol` as "Workhorse model for coding and everyday work"; the founder chose Sol, at high reasoning.
- Never read: `%USERPROFILE%\.codex\auth.json`, `config.toml` (credentials). The repo's `AGENTS.md` and
  `.agents/skills/gridlock-build/` carry our rules to Codex; the user-level `~/.codex/AGENTS.md` carries the
  founder's standing rules.
- Two claude.ai plugins (Codex plan review; Codex dispatch via MCP) were enabled by the founder but had not
  synced to this machine on 2026-09-26; T0.7 reads them before any use.
- Operating model (founder, 2026-09-26, plan v3): one Codex lead runs the build and every judging round
  with up to five sub-agents, with no time limit ("remove the time limit just let it work"); Claude
  reviews last. Codex's sub-agent support inside `codex exec` was proven in T0.6 before the launch.

## Prior art (read 2026-09-26) — pitch and inspiration only, never a data source

- **PaverOps** (https://www.paverops.com/, read with WebFetch 2026-09-26): cloud Esri/ArcGIS platform for
  cities, counties, transportation agencies and utilities to share current and future projects — overlap
  detection, pavement plans and moratoriums, utility data sharing, "synchronous projects, cost sharing";
  membership restricted to local governments and utilities; no public data, API, pricing or case-study
  numbers on the site. Used in `SPEC.md` § Prior art, the Q&A crib, the presentation and the Devpost text.
- **Peers** — the 2026-09-26 research (the `/last30days` skill v3.18.4 run inside a Claude Opus sub-agent,
  plus WebSearch/WebFetch on vendors' pages): `reviews/2026-09-26-gridlock-build/research/prior-art-2026-09-26.md`
  holds the tool table with URLs, the triaged ideas, the data notes and the pitch lines. Claims marked
  "snippet" rest on search-result text (the site blocked automated reading) and are verified before any
  pitch use. Taken: the conflict-matrix CSV layout (FHWA SHRP2 R15B), the visible plan editions, the
  interregional framing (SCRTP–SERTP, FERC Order 1920) and the HIFLD archive note. Left for the founder:
  the candidate ideas listed in `SPEC.md` § Prior art.
