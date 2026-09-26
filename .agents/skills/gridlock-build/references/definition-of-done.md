# Definition of done — GridLock

The standing bar every task clears, on top of its own acceptance criteria. Tailored once from
Addy Osmani's `agent-skills` `references/definition-of-done.md` (MIT) and the Lucky workflow's build
rules; not renegotiated under deadline pressure (that is a red flag, not a trade-off).

## Per task (before the box is ticked)

### Correctness
- [ ] Every acceptance criterion met, verified **at runtime in this session** (not "should work").
- [ ] A check that fails without the change and passes with it, in the canonical suite for that surface
      (`tests/pipeline`, `tests/api`, `tests/eval`, `tests/e2e`) — proved by running it on the pre-change code.
- [ ] Focused suites green; no regression in the surfaces you touched.
- [ ] Empty, error and "second time" paths handled, not only the happy path.
- [ ] Sibling paths given the same fix (list and export, desktop and 390 px, light and dark, map and keyboard).

### Honesty of data and words
- [ ] No invented value: unknowns are `null` in data and "not stated" / "unknown" on screen.
- [ ] Data is shown verbatim (names, descriptions) with `data-src`; only the product's own words follow
      the glossary and the copy lint.
- [ ] Every estimate is a range and says "estimate", or states why there is none; assumptions visible inline.
- [ ] Every project shown carries its source (document + real page) and accuracy label.
- [ ] Claims about a pair ("same substation", "shared endpoint") say only what the PDFs support.

### Quality
- [ ] Matches house patterns (`references/house-patterns.md` once written; `SPEC.md` § Code style before).
- [ ] No debug output, commented-out code, dead files or stray `print`/`console.log`.
- [ ] Only your lane's files changed; anything else is an exact patch in your report.
- [ ] Data strings reach the page via `textContent` / safe attributes only.

### Interface (web tasks)
- [ ] Works at 1440 and 390 px, light and dark; keyboard reachable with visible focus; labelled controls.
- [ ] Loading, empty and error states exist and read like the rest of the product.
- [ ] Scripted audits for the touched surface pass (thresholds in `references/ui-contract.md`).

### Security trigger (from ECC's risk-sized ceremony)
- [ ] If the change touches input handling (query params, search text, coordinates, radius), a file path,
      an external API (Claude), HTML rendering, CSV output or a secret: a `gridlock-security` read of the
      diff before the task is ticked, and a test for the abuse case (bad input, traversal, formula cell,
      injection string).

### Records
- [ ] One commit `<lane>: T<n> <what>`; task ticked; one tracker line (what changed, checks added, totals).
- [ ] Evidence trail in the report: task → its test → failing output before → passing output after.

## Per merge (the Codex lead, every task; Claude for its own final-review fixes)
- [ ] The diff matches the brief; the report's before/after evidence is real (re-run one check).
- [ ] `references/review-checklists.md` §A + the lane's section + §E applied; no open CRITICAL/HIGH.
- [ ] `scripts\quick-gate.ps1` green on the lane's branch (≤ 5 min).

## Per gate (the Codex lead; Claude at the final review)
- [ ] `VERIFY.cmd` full matrix on `main`, quiet machine, passing totals ≥ baseline; summary file read.
- [ ] Contracts unchanged unless the lead changed them on purpose (reason, fresh type review, fixtures
      re-validated; recorded in the tracker and `DELIVERY.md`).
- [ ] Security implications of new inputs reviewed (key, paths, HTML, CSV cells, prompt text).
- [ ] Anything user-facing that changed got a `change-reviewer` read.
- [ ] Tracker checkpoint written (machine time, commit, totals); the founder reads it there.

## Red flags — stop and fix before continuing
- "Done, I just haven't run it." · "Tests pass" standing in for runtime checks · a check removed,
  skipped or loosened to get green · a number on screen you cannot trace to a file · a feature that only
  works online or only with a key · a bar lowered because the clock is short.
