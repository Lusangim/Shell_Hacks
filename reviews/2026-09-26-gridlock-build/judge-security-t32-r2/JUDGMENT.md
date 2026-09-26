# T3.2 security confirmation, round 2

Reviewed 2026-09-26, 10:38–10:40 EDT, frozen HEAD `4da4089`, repair `9bc7e83`, port 8785. Mode: code review, canonical focused tests, and in-memory fake-client probes. I did not build this change.

## Scope and method

Read the repair's five changed files in full, the generator caller, prior judgment, GridLock security role, relevant contracts/boundaries, house patterns and review checklists A/C/E. Searched generator/cache/grader callers in server, scripts and tests. The generator still has only test callers; this confirmation does not approve future route wiring or real-client use.

Every test/probe command set `GRIDLOCK_AI=off` and `GRIDLOCK_TEST_PORT=8785`; Python ran only through `& $env:GRIDLOCK_PY`. No SDK construction, network requests, credential reads, product edits or test edits occurred. Additional probes mocked cache reads and publication in memory; canonical tests used their isolated temporary files. No server or browser was started.

## Confirmed repairs

### SEC-T32-01 [previous P2] — closed

`tests/eval/grader.py:75` now bounds dollar digits, uses a local Decimal context sized to the input, and rejects `InvalidOperation`. The exact original development-case input, `" A cost is $1." + "0" * 40 + "."`, now becomes an ordinary failed grade at both callers: `server/brief_generator.py:156` (model candidate) and `server/brief_generator.py:177` (matching-key cached candidate).

The canonical regression at `tests/api/test_briefs.py:159` passed: two bad fake responses return the identical template with `grade_rejected`, two calls and no cache file. Its matching-key poisoned-cache branch returns the identical template with `access_disabled` and zero calls. Direct grading regression at `tests/eval/test_grader.py:187` passed.

Independent in-memory confirmation supplied the same bad completion followed by a valid completion. Result: model origin, no failure reason, exactly two fake calls, exactly $0.48 reserved, and exactly one publication of the valid result. A separate correctly keyed, model/version-matching poisoned cache decoded successfully, then failed regrading and returned the template offline with zero calls. This checks the regrading boundary rather than relying on a stale-key miss.

### SEC-T32-02 [previous P2] — closed

`server/brief_cache.py:90` now catches JSON conversion `ValueError` and deep-decoding `RecursionError` within the decode/validation boundary. Cache path validation remains outside the handler at line 84.

The canonical regression at `tests/api/test_briefs.py:179` passed with the exact payload `'{"cache_key":' + '1' * 5000 + '}'`: direct loading returns `None`, and offline generation returns the template with zero calls. Independent in-memory probes confirmed both outcomes and equality to the expected template for that payload and for a 1,100-level nested-array JSON value. An invalid `../outside` ID still raises `ValueError` rather than being swallowed as a miss.

## Verification and nearby regression checks

Command: `& $env:GRIDLOCK_PY -m pytest tests/api/test_briefs.py tests/eval/test_grader.py -q -p no:cacheprovider`.

Result: **82 passed in 1.50s**, no failures or skips. This includes the exact repair regressions, documented valid money forms, template grading, valid cache reuse, stale/corrupt cache handling, retry/budget branches, traversal rejection and concurrent atomic publication.

Six additional direct-grader inputs were rejected without exceptions: dollar values at 64 and 65 total digits, a 5,000-digit dollar value, a 5,000-digit page value, a 5,000-digit distance value and `1,,,`. Decimal context precision was unchanged afterward. These exercise the new limits at `tests/eval/grader.py:77`, `:119` and `:130` and the caller-visible rejection result.

The repair preserves fixed generator reason codes and template labeling, valid cached output, a bounded two-attempt policy, and invalid-path rejection. Numeric precision is local to the operation. No material nearby regression was reproduced or found by the scoped review.

## Limits and verdict

This is a confirmation review, not a full gate or a complete security audit. I did not run VERIFY, browser/API integration, a real SDK/client, or a spending calibration. The brief reports the separate LEAD-owned Windows port-fixture gate failure as **343 passed, 15 setup errors**; those are not this judge's test results, and I do not claim that gate is green. Future real-client setup and production caller guards remain outside this repair's scope. No additional concern is presented as a proven defect.

Open findings in this confirmation: **P0 0 / P1 0 / P2 0 / P3 0**. Both prior P2 findings are closed. Accept the security repair; retain the separate gate blocker in the lead's delivery record.

Only this report is changed and committed.

material improvement still available: no
