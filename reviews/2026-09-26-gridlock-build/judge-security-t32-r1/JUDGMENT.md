# T3.2 independent security judgment, round 1

Reviewed 2026-09-26 at frozen commit `d416cae`, range `b077253..d416cae`, port 8785. Mode: code review and local fake-client probes. I did not build this change.

## Scope and evidence

Read all five changed files, the direct template and deterministic grader dependencies, relevant schema definitions, reference AI brief, contracts/boundaries, house patterns, and review checklists A/C/E. Searched callers in server, scripts and tests: the new generator currently has only test callers; no production route invokes it. Applied the GridLock security role and build skill.

Ran `GRIDLOCK_AI=off`, `GRIDLOCK_TEST_PORT=8785`, Python only through `& $env:GRIDLOCK_PY`:

- `-m pytest tests/api/test_briefs.py -q -p no:cacheprovider`: **15 passed in 0.79s**.
- In-memory adversarial probes described below. Cache reads were supplied with `unittest.mock.patch.object(Path, 'read_text', return_value=payload)`. The probes created no cache files and made no network calls.

I did not run the full gate, review existing web/API guards, inspect credentials or credential locations, examine sealed evaluation cases, validate SDK compatibility/pricing, or construct a real client. The builder's larger suite totals are not my verification results.

## Findings

### SEC-T32-01 [P2] Grader exceptions bypass model rejection and offline cache fallback

Locations: `server/brief_generator.py:156`, `server/brief_generator.py:177`, reached `tests/eval/grader.py:80`.

Trigger: use the committed development case `desc-p41__sertp-p107-9bc088` and its valid template. Append `" A cost is $1." + "0" * 40 + "."` to `Brief.what`. This is schema-valid text. Supply it through `FakeClient([parsed(bad), parsed(bad)])` with access enabled and a $0.48 Budget. The new generator invokes `grade_brief`, whose dollar normalization attempts `Decimal.quantize` at attacker-controlled decimal precision and raises `decimal.InvalidOperation`. That exception is outside the `client.messages.parse` handler and never becomes `grade_rejected`.

Observed output: `model numeric probe: InvalidOperation escaped after 1 fake call`.

Second caller path: put the same brief in a JSON cache envelope using the correct content key, `MODEL_ID` and `PROMPT_VERSION`. With `client=None`, `access=False`, and `budget=None`, `generate_brief -> load_cached_brief -> grade_brief` raises before the access-disabled template branch.

Observed output: `cached numeric probe: InvalidOperation escaped with access disabled`.

Impact: an invalid model completion aborts generation instead of retrying/falling back. A poisoned or malformed matching-key cache entry can also break offline retrieval repeatedly. This is an availability and rejection-boundary weakness, not demonstrated remote exploitation: T3.2 has no production route and no real-client constructor. The malformed value is rejected neither by string schema validation nor by a completed grade result.

Fix: handle expected numeric grading failures as rejection at both new grading boundaries, or make the grader total for untrusted numeric prose through a separately owned repair. Preserve a fixed reason code, no response/exception body logging, retry reservation, and template fallback. A schema change is unnecessary.

Verify: add fake-client regression tests using the exact string above; two bad responses must return the template with no cache write and no more than the allowed two reservations. The matching-key poisoned cache must become a miss; access disabled must return the template with zero calls. A valid subsequent response must still be cached.

### SEC-T32-02 [P2] Some corrupt JSON entries escape the cache-miss handler

Location: `server/brief_cache.py:86` and `server/brief_cache.py:90`, called by `server/brief_generator.py:174`.

Trigger: replace the cache read with the exact string `'{"cache_key":' + '1' * 5000 + '}'`. Python's JSON integer conversion rejects this oversized integer with `ValueError`; it is not `JSONDecodeError`, `TypeError`, or Pydantic `ValidationError`, so the enumerated exception handler does not catch it.

Observed output from a generator call with access disabled and no client/budget: `long JSON integer: ValueError escaped with access disabled`.

Impact: a roughly 5 KB malformed cache entry interrupts offline generation instead of being a cache miss. A local file mutation is required on the current application surface; no filesystem escape or code execution was demonstrated.

Fix: include JSON conversion `ValueError` in the guarded decode/validation path and keep genuine cache-path validation errors outside that handler. Consider a bounded read/decode policy if further untrusted cache formats are supported.

Verify: regression-test this exact payload through both `load_cached_brief` and offline `generate_brief`; expect `None` and the normal template, respectively. Existing valid and stale-entry checks must remain green.

Counts: **P0 0 / P1 0 / P2 2 / P3 0**.

## Strengths and coverage

- No SDK or credential resolution exists in the changed modules. `generate_brief` only accepts an injected client; `scripts/generate_briefs.py` returns refusal even when approval and a positive ceiling are supplied. AI-off construction safety is structural for this task. Future caller wiring must still honor the setting.
- `make_request` has a stable system prefix, canonical structured contract fields, a separate output schema and escaped angle brackets. The hostile closing-delimiter test passes. There is no raw PDF loader, tool execution, shell execution or outbound action in this path. Delimiting and deterministic checks do not establish semantic immunity to every prompt injection; none was claimed by this review.
- `Budget.reserve` serializes accounting with a lock and runs before each outer parse call, including retries. The tests prove no call without access, budget, or sufficient reservation, and deny a second attempt after exhaustion. The $0.24 reservation is explicitly provisional; actual SDK retry behavior, usage accounting and a real spending ceiling remain F6 work before real use.
- Cache keys bind structured pair/project/contact content, model and prompt version. Presentation status alone is excluded. Both envelope and brief hashes, overlap ID, model and version are checked; matching-hash content is regraded. Tests cover stale input, malformed JSON, altered hashes and unsupported-dollar content.
- Cache filenames have an allowlist and resolved-parent check. Writes use unique same-directory temporary files, flush/fsync, bounded Windows replacement retries, atomic replacement, and cleanup. The concurrent-writer test passed with 20 writes. No path traversal or partial-publication defect was found within the reviewed caller path. Hostile local filesystem races were not exercised.
- Refusal/truncation return an explicitly marked template immediately; ordinary parse/client/grade failures have fixed reason codes. Captured fake response and exception markers are not logged. Templates are not cached as model results.
- Existing tests cover the changed request builder, generator branches, key/path/read/write helpers and batch refusal. Important missing coverage is the two reproduced exceptional decode/grade paths above. Additional nice-to-have coverage includes concurrent budget exhaustion and filesystem write-error injection; neither is presented as a proven defect.

The separate 1,100-level nested-array JSON probe returned a template; it did not demonstrate a defect. No product or test files were changed. Only this report is committed.

## Verdict

Return the two P2 findings to the API lane for focused repairs before declaring corrupt-cache and grade-failure fallback complete. The no-spend defaults are intact; no P0/P1 security issue was demonstrated.

material improvement still available: yes
