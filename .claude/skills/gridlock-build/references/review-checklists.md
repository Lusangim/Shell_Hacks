# Review checklists — GridLock

One home for the review checklists. Rewritten in our own words from ECC agent definitions
(`affaan-m/ECC`, MIT, © 2026 Affaan Mustafa — file named per section), read 2026-09-26 and adapted to
this stack, this machine and the founder's rules. Used three ways:
**The Codex lead on every merge** (§A + the lane's section + §E; Claude on its own final-review fixes) ·
**sub-agent briefs** (the lane's sections pasted as "check before you report") · **gate reviewer roles**
in `.claude/agents/` (one or two sections each), run as Codex sub-agents during the build and as Claude
Opus agents in the final review.

## A. Review gating — every reviewer (ECC `agents/code-reviewer.md`)
- Read the whole changed files plus their callers, imports and tests before judging.
- Report a finding only if all four hold: the exact line is cited · a concrete trigger is named (input,
  state → bad outcome) · the surrounding context was read · the severity is defensible. Otherwise drop
  it or label it a concern.
- CRITICAL and HIGH findings also show the snippet, the failure scenario, and why existing guards
  (types, validation, framework defaults) do not already catch it.
- Zero findings with "ready" is a valid result; manufactured nits are the failure mode to avoid.
- Skip known false positives: error handling already done upstream · validation done by the caller ·
  well-known constants (40 km, band limits) called magic numbers · long tables in config or tests ·
  guarded null access · loops over a fixed small set called N+1 · hardcoded values in fixtures.
- Output per finding: `[SEVERITY] title · file:line · issue · fix`; then a count per severity and the
  verdict. **CRITICAL or HIGH → back to the owning builder.** MEDIUM → fix if cheap or list for G4 (or for
  `DELIVERY.md`). LOW → note.

## B. Python and FastAPI — DATA and API lanes (ECC `agents/python-reviewer.md`, `agents/fastapi-reviewer.md`)
- CRITICAL: injection into shell or SQL · path traversal (any id that maps to a file must be validated) ·
  `eval`/`exec` · pickle or unsafe YAML (caches are JSON) · hardcoded secrets · bare or swallowed `except` ·
  files opened without a context manager.
- HIGH: untyped public functions or `Any` · mutable default arguments · an enum written as loose strings ·
  functions over ~50 lines or nesting over 4 · blocking work (shapely, pyproj, file I/O) inside
  `async def` routes — use plain `def` routes or precompute in the pipeline · a route without a
  `response_model` (the web lanes code against the OpenAPI output) · wrong dependency overrides in tests ·
  outbound HTTP (the Claude client) without a timeout · a key read anywhere but settings, or ever logged.
- MEDIUM: `print` instead of logging · `== None` · `import *` · missing error responses in OpenAPI.
- LOW (never blocking): style, docstrings, comprehension preferences.
- GridLock specifics: Pydantic v2 idioms, `extra="forbid"` on inputs · no CORS (same origin) and bind to
  127.0.0.1 · error bodies never carry tracebacks · pyproj transformers built with `always_xy=True` ·
  ruff or mypy only if already in the venv — never install a tool. Leave test runs to the launcher's gate.

## C. Silent failures — DATA and API (ECC `agents/silent-failure-hunter.md`)
Hunt, and report with location, severity, impact and fix:
- empty `except`/`catch`, or an error turned into `None`, `[]` or `0` without context;
- logging without context, at the wrong level, or logged and then ignored;
- fallbacks that hide failure (a default that looks like data);
- lost tracebacks, generic re-raises, async calls never awaited;
- file or network I/O with no timeout or error path; half-written outputs (write to temp, then rename).
GridLock targets: a PDF page yielding empty text silently drops a project (stage counts must reconcile) ·
an unparseable date becomes `None` and changes an overlap verdict · empty or invalid geometry measures
0 m and reads "touching" · wrong axis order gives plausible but wrong kilometres · a missing cost produces
a default savings number instead of a visible reason · the API returns 200 with `[]` on an internal error ·
a `fetch` without an `ok` check renders "no pairs" when the call failed · a failed or truncated brief shown
as AI output instead of labelled Template.

## D. JavaScript and Leaflet — WEB and WEB-2 (JavaScript parts of ECC `agents/typescript-reviewer.md`)
- CRITICAL: `eval` / `new Function` · XSS through `innerHTML`, `insertAdjacentHTML`, `document.write` or
  Leaflet `bindPopup` / `bindTooltip` with a string built from data (project names and brief text come
  from outside — pass DOM nodes filled with `textContent`) · merging untrusted objects into prototypes.
- HIGH: floating promises · `forEach(async …)` · awaiting independent requests one by one · empty
  `catch` · `JSON.parse` without a guard · throwing non-Error values · module-level mutable state outside
  `state.js` · `var` · `==` · a stale response overwriting a newer selection (use a request token or
  `AbortController`) · map layers added without `clearLayers()` (duplicated paths and listeners) · inline
  event handlers or inline scripts (CSP blocks them) · imports without explicit `.js` extensions.
- Reports only; never rewrites code.

## E. Tests — every lane (ECC `agents/pr-test-analyzer.md`, edge cases from `agents/tdd-guide.md`)
- Map each changed function or route to the tests that exercise it; list untested paths as critical /
  important / nice-to-have.
- Tests assert behaviour (real values), not "does not throw"; they are isolated; names say the behaviour.
- Edge cases to demand where they apply: null, empty and invalid input · boundaries · error paths ·
  special characters and very long strings · a few thousand items where performance matters.
- GridLock: band edges at 1 m and exactly 1,600 / 8,000 / 40,000 m per the contract's inclusive and
  exclusive rule · missing or phased dates · deterministic tie-breaks · savings low ≤ high with
  assumptions, and each non-range status · API 422 paths · contract validation on every response path.
- Red flags: tautological tests (expected values computed with the code under test) · tests skipped,
  weakened or stripped of assertions since the brief · e2e tests with fixed sleeps · fewer passing checks
  than the baseline.

## F. Accessibility — WEB gates (ECC `agents/a11y-architect.md`, criteria re-checked against WCAG 2.2)
- Contrast 4.5:1 for text, 3:1 for UI components and graphics (SC 1.4.3, 1.4.11) · reflow at 320 px
  (1.4.10) · everything operable by keyboard (2.1.1) with no trap (2.1.2) · visible focus (2.4.7) that is
  not hidden behind sticky panels (2.4.11 Focus Not Obscured) · a single-pointer alternative to dragging
  (2.5.7) · targets at least 24×24 px (2.5.8; our contract asks 44×44 at phone width) · status messages
  announced (4.1.3) · name, role and value for every control (4.1.2).
- GridLock: the ranked list is a complete path that never needs the map (Leaflet vector layers take no
  keyboard focus) · Tab can always leave the map (Leaflet captures arrow keys) · bands and utilities
  encoded by more than colour (dash pattern, label, legend) with 3:1 against the basemap · filter changes
  announce the result count in a live region · the brief panel manages focus · `flyTo` respects reduced
  motion · axe misses most map problems, so a scripted keyboard walk is required.
- Output: what a screen reader announces for each surface, the criteria that apply, a one-line reason
  for each ARIA choice. Read-only.

## G. Types and contracts — once at G1a, again when they change (ECC `agents/type-design-analyzer.md`)
Score each model 1–5 on: encapsulation · impossible states made unrepresentable · usefulness to callers
· escape hatches (`Any`, loose `dict`, string enums). Targets: band as an enum that agrees with the
distance; `distance_km ≥ 0`; savings `low ≤ high` with a unit and non-empty assumptions when
`status = range`; a canonical pair order (no duplicate pairs); "unknown" as explicit `null`, never 0;
records frozen where they are read-only.

## H. Live walkthrough — judges (procedure from ECC `agents/gan-evaluator.md`)
- First state the mode actually achieved (live browser · screenshots · code only) and any fallback.
- First impression: loads cleanly, looks like a product, clear hierarchy.
- Each feature: the happy path; edge input (empty, 500+ characters, `<script>` and non-Latin text, rapid
  repeated clicks); error states; one screenshot each. Widths 375/390, 768, 1440; hover, focus and active
  states; generic "AI-looking" design tells; Tab, Enter and Escape; loading states.
- Anchored 1–10 per lens (4–5 tutorial grade · 7 solid junior · 8 professional); every issue names the
  element, gives a number where possible, cites the spec, and proposes a fix; track regressions since the
  last run; resist generosity. Our four lenses and the verdict line stay; its own weights do not.

## I. Public-release sanitizer — before every push and at T5.5 (ECC `agents/opensource-sanitizer.md`)
Read-only; any CRITICAL = FAIL. Report **file:line and the pattern name only — never any part of a
secret**; never open `.env` or credential files, only report that they exist.
- Secret patterns: `sk-ant-`, `sk-` (OpenAI), `OPENAI_API_KEY=`/`ANTHROPIC_API_KEY=` with a value,
  bearer tokens, JWTs, private keys, GitHub/Google/Slack tokens, URLs with credentials.
- Personal data and paths: the founder's personal email; `C:\Users\` paths in docs, briefs, fixtures,
  Playwright traces and screenshots metadata.
- Files that must not ship: `.env*`, keys, certificates, `credentials.json`, local settings, venvs,
  run output.
- Judgment calls for the founder (Q11): whether `.claude/`, `reviews/` briefs and notes ship; third-party
  PDFs and their redistribution terms.
- History: `git log -G<regex> --format=%h --name-only` (names only, never `-p` output). Never squash
  history — commits made during the event are evidence.

## J. End-to-end tests — WEB briefs (ECC `agents/e2e-runner.md`)
Choose journeys by risk; cover happy, edge and error paths; locate by role, label or `data-testid`; assert
at every step; wait on conditions or responses, never fixed sleeps (`expect()`, `expect_response`);
tests independent of each other; tracing retained on failure; run each new test 3–5 times before it enters
the baseline; a flaky test is quarantined only with the lead's approval (Claude's after delivery) and
always reported.

## K. Repair brief — when a gate is red (rules from ECC `agents/build-error-resolver.md`)
Collect every error first; fix each with the smallest change; re-run after each fix; no refactoring, no
renames, no new dependencies; stop and report instead of installing anything or touching another lane.

## L. Escalation triggers — the Codex lead; Claude after delivery (from ECC `agents/loop-operator.md`)
Stop dispatching and reassess when: no progress across two checkpoints · the same stack trace repeats ·
merge conflicts block the queue · a usage-limit stop · verify totals drop · the hand-off is 30 minutes away.
