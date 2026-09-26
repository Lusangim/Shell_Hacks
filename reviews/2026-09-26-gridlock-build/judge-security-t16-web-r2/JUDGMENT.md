# T1.6 browser map security confirmation, round 2

Reviewed 2026-09-26 12:16–12:20 EDT on frozen commit `8efe815862c6e5412e51156532b3a58551953b4e`, port 8789. Independent reviewer; no product or test edits.

Scope: T16-WEB-SEC-01 and repairs `de0ce42` and `22e9a55`, the complete `web/js/basemap.js`, its map initializer, canonical focused tests and their server/browser guards. This is a focused confirmation, not an integrated gate or a new full security audit.

## Verdict

P0: 0 · P1: 0 · P2: 0 · P3: 0 new or remaining findings in this scope.

**T16-WEB-SEC-01 is closed.** The shared initializer checks current Google intent and online state before API insertion (`web/js/basemap.js:113`); each selection retains its own request token for applying layers and status (`:129`, `:141`). A rejected initializer clears readiness only when its promise is still cached (`:125–126`). An obsolete layer's failure cannot clear current readiness or force offline selection (`:145–148`). The repair adds no new key, URL or DOM interpretation boundary; those unchanged boundaries did not require another key-string probe.

## Runtime evidence

Canonical command, AI and Google off, port 8789:

`& $env:GRIDLOCK_PY -m pytest tests/e2e/test_modern_map.py -k 'google or stale_layer' -q --tb=short`

- Initial run: **7 passed, 10 deselected in 12.42s**.
- Confirmation with `GRIDLOCK_TEST_ROOT` explicitly set to this frozen worktree: **7 passed, 10 deselected in 11.62s**. This removes any ambiguity from the fixture's optional server-root override.
- Delayed plugin, Google Maps → Satellite: Satellite becomes selected and reports `Satellite map`, using the hybrid layer without fallback or another click.
- Delayed plugin, Google Maps → Map, both successful and failed release: offline status persists; no Google API request starts. A subsequent Google Maps selection succeeds.
- Going offline while the plugin is held: the switch becomes unavailable and offline selection persists after release, without an external request.
- First layer pending, Satellite succeeds, first layer emits `tileerror`: Satellite status and pressed state persist. Returning to Google Maps succeeds with **one** plugin load, proving the old failure did not discard shared readiness.
- Existing lazy failure and ordinary roadmap/satellite/offline switching checks also pass.

Independent local probe covered cancellation later in initialization, after plugin completion while the synthetic API script was pending. The probe intercepted `document.head.append` before a Google script could enter the document; it used the fixed fake configuration from the test helper and fulfilled the local plugin with a fake Leaflet layer.

For both API success and API failure, Google Maps → Satellite → Map followed by release preserved the offline status and Map pressed state. A later Satellite click succeeded. The success case reused the single plugin initialization; the failure case retried successfully with a second initialization. Both cases had zero page errors and only assigned-loopback requests. The first probe attempt installed its interceptor before the document head existed and timed out; moving the probe installation after page readiness resolved this harness error. No product change was involved.

## Limits and cleanup

- Real Google service loading, provider attribution rendering and browser-key restrictions remain the founder's online compatibility check. No real credential was opened or tested, and no actual Google response was used.
- Script timeout duration was reviewed in code; the independent probe exercised success/failure completion, not a ten-second timeout. Canonical stale-layer failure and cancellation checks exercise the relevant token/cache guards.
- No full quick gate or VERIFY was run by this reviewer. The lead owns that integrated check.
- Browser routes rejected nonlocal requests; the server used the existing outbound guard. All test and probe servers/browsers closed, and the port ownership check confirmed **port 8789 free**.
- `git diff --check` passed. Only this judgment is committed.

material improvement still available: no
