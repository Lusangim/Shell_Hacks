# T1.6 map API security judgment

Reviewed 2026-09-26 at 11:40 EDT on frozen product commit `5c0101d68c230252355bffed73c24fafc7f2bbed`. Independent judge; no product or test changes.

## Verdict

Ready for the lead's integration gate. Findings: **P0 0 · P1 0 · P2 0 · P3 0**. No concrete security defect was found in this task's scope; no repair or finding-specific acceptance check is required.

## Scope and evidence

Read the T1.6 diff against `d5e2366`, complete changed modules and tests, application callers and security middleware, builder brief/report, role, contracts/boundaries, house patterns and the required review checklists. Confirmed frozen HEAD before review.

Judge-run command, with `GRIDLOCK_TEST_PORT=8787`, `GRIDLOCK_AI=off` and `GRIDLOCK_GOOGLE=off`, using `GRIDLOCK_PY`:

`-m pytest tests/api/test_map_assets.py tests/api/test_core.py -q --tb=short`

Result: **67 passed in 2.57s**, exit 0. The in-process TestClient cases use their existing synthetic localhost base URL and start no listener. The map suite covers exact 200/206/404/416 bodies and headers; first, middle, suffix, open-ended and end-clipped ranges; empty/missing files; huge/malformed/multiple/duplicate range headers; traversal-shaped paths and ignored path query input; Google-off read/stat traps; fake configured keys and missing/empty key fallback; foreign Origin/Fetch-Metadata rejection; localhost Host enforcement; conditional CSP/referrer policy; no CORS; no-store; and a read-only eight-byte request from the approved external PMTiles archive. Enabled-key cases use only the existing injected fake fixtures and reject socket connections during route requests.

An additional in-memory probe exercised `_chunks` with 0, 1 and 150,000 bytes, asserted exact output length, stream closure and every read bounded at 65,536 bytes. Two 20-digit range probes confirmed that overlong suffix/end values clip to the file size. All five probes passed. This probe created no file and accessed no key.

## Boundaries that hold

- `server/app.py:324` routes only the fixed archive name and passes the configured path; request text never becomes a filesystem path. `server/map_assets.py:86` opens that file once, derives its length from the same handle, rejects invalid ranges before streaming and returns fixed path-free errors. `server/map_assets.py:75` bounds reads and closes the stream after normal iteration.
- `server/settings.py:56` short-circuits before the key loader when Google is off. Key loading is confined to settings, uses a bounded file read and character validation, and suppresses key values in settings/model repr. No outbound client or logging is introduced.
- `server/app.py:285` retains the localhost/127.0.0.1 Host restriction. `server/map_assets.py:41` rejects explicit foreign browser context for config. The config response is JSON with nosniff, no-store, same-origin resource policy and no CORS permission.
- `server/app.py:293` changes CSP only when a browser key is enabled and present; its host list is explicit. Referrer policy changes only for HTML/config in that state. Off/no-key responses retain the original offline policy.
- Returning an enabled browser key to the same-origin page is the intended documented boundary. It is visible to that browser and local clients; these controls do not authenticate local processes or protect against script already executing on the app's origin. Provider API/referrer restrictions remain necessary for founder-run online use.

## Limits

This is a scoped API security review, not a full gate or a review of the separate WEB Google/PMTiles integration. The builder's reported final gate of 312 Python + 19 shell + 18 audits was read as builder evidence and was not rerun here. No real key was opened, printed or tested; no real Google request, network access, browser launch or live provider restriction validation occurred. Google host allowlist completeness and provider acceptance still need the already documented founder-run online check. Transfer cancellation or an archive modified during a transfer was not simulated; the configured archive is a trusted read-only input and the code does not convert a truncated stream into fabricated bytes.

material improvement still available: no
