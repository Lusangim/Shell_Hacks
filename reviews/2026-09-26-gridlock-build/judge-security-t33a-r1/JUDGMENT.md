# T3.3a route security judgment

2026-09-26 11:54 EDT · independent security judge · frozen `311e2dd3d9012017d5e2dc37a567af9592d4a483` · assigned port 8788.

**Verdict: ready for the scoped security gate. P0: 0 · P1: 0 · P2: 0 · P3: 0.** No concrete security defect was found in the T3.3a diff. No fixes or new acceptance requirements are requested by this review. The integrated lane gate remains the lead's separate requirement.

## Scope and method

Applied the repository `gridlock-build` judge rules, `gridlock-security` role, and review checklists A/C/E. Read the complete T3.3a changed product and test files, diff `adf3846^..adf3846`, the T3.1–T3.3a reports, and relevant cache, generator, grader, settings, app middleware, launch path, and tests. Assessed canonical IDs, cache freshness and grading, atomic publication, structured prompt boundaries, local Host and same-origin guards, forwarded headers, concurrency, cap, budget reservations, and fixed failures.

All test/probe commands set `GRIDLOCK_TEST_PORT=8788`, `GRIDLOCK_AI=off`, and `GRIDLOCK_GOOGLE=off`. In-process applications used explicit synthetic settings and fake client injection only. Temporary cache files were confined to test/run directories. No real client, credential, external service, browser, or persistent server was used. Only this report was written in the frozen worktree.

## Runtime evidence

- `& $env:GRIDLOCK_PY -m pytest tests/api/test_brief_routes.py tests/api/test_briefs.py tests/eval/test_grader.py -q --tb=short`: **107 passed in 6.51s**. This covers fresh/stale/corrupt cache, re-grading, template responses, malformed origin/host/custom header, AI off, absent client and ceiling, insufficient retry budget, simultaneous POST rejection, on-demand cap, refusal/truncation/client error/grade failure, prompt delimiter injection, and atomic concurrent cache publication.
- Additional in-process probes with `socket.socket.connect` trapped after TestClient startup: **5 malformed/forwarded-header probes**, **8 canonical-ID/path probes**, denied cross-origin preflight, and a matching-hash cache whose prose was tampered with. All passed; **zero fake-client calls and zero socket connects**. Inputs included an evil origin with a forged `Forwarded` header, comma-separated custom-header/origin values, trailing origin path, trailing-dot Host, encoded backslashes, double-encoded traversal, NUL suffix, and an extra path segment. Rejections used the fixed typed 400/403/404 errors. OPTIONS returned 405 without CORS authorization. The tampered cache returned a valid template with no injected dollar text, and meta did not miscount it as stale.
- `git diff adf3846^ adf3846 --check`: clean.
- One initial pytest invocation used the nonexistent filename `tests/api/test_brief_generator.py`; collection ran **no tests**. It was corrected to the actual `tests/api/test_briefs.py` for the successful 107-test run above. No product or test change was made.

## Controls that held

- `server/brief_routes.py:45` resolves only IDs in validated loaded artifacts before cache access; `server/brief_cache.py:64` also validates the cache filename and resolved parent. Traversal and noncanonical IDs reached neither a cache file nor the fake client.
- `server/brief_routes.py:54` verifies the current input key and re-grades cache hits; corrupt or ungraded text falls back. Stale metadata is counted without serving stale model prose. `server/brief_cache.py:101` publishes a validated model brief through a private temporary file and atomic replacement.
- `server/app.py:285` restricts Host to loopback names. `server/brief_routes.py:79` compares the complete origin to the Host and ignores forwarded-host/proto claims. The custom request header is required, and the app does not authorize cross-origin preflight.
- `server/brief_routes.py:35` leaves the real client unwired. The route checks explicit AI enablement, client, positive ceiling, nonblocking lock, cap, and available reservation before generation (`server/brief_routes.py:142`). `server/brief_generator.py:87` reserves under a lock before every outer attempt, including retry. The concurrent route check rejected a second POST without queuing a spend.
- `server/brief_generator.py:104` passes structured fields in an escaped delimiter block with fixed rules. Generated prose is graded before publication. Client exceptions are reduced to fixed fallback reasons (`server/brief_generator.py:197`), and unexpected API failures have a fixed body (`server/app.py:306`). The tested failure paths exposed no fake response text.

## Limits

This is a scoped review of T3.3a and its direct callers, not a full-repository sanitizer, browser audit, or integrated quick gate. I did not inspect credentials, unrelated git history, source PDFs, or founder files. Model behavior, real SDK compatibility, measured spend, and arbitrary model prompt-injection resistance were not tested; the real client remains disabled pending the founder-approved F6 work. The existing numeric reservation is an offline estimate, as documented by T3.2, and this review does not approve real spend. Browser hydration repairs and the new map routes are outside this frozen review.

material improvement still available: no
