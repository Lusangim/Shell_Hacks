# T2.9 scoped security judgment

Date: 2026-09-26. Frozen product HEAD: `3057075`; reviewed change: `c3e32bb..3057075`. Independent security judge; no product or test edits. Local test port: 8786; AI and Google off.

Verdict: ready for the scoped CSV download and print-rendering security requirement. Findings: **P0 0 / P1 0 / P2 0 / P3 0**. No security correction or acceptance check remains open in this scope.

## Evidence and strengths

- `web/js/app.js:113` disables export during filter loading and enables it only after the current response is rendered. `web/js/export.js:165` captures `filterControl.query()`; `web/js/filters.js:20` constructs those parameters with `URLSearchParams`. Export fetches a fixed local endpoint at `export.js:178`. The three browser parity cases matched visible rows, the list API and downloaded CSV, including a nonempty combined filter and an empty result.
- `web/js/export.js:180` consumes the response as a Blob and downloads those bytes unchanged. No browser CSV serializer exists. The fixed server filename and BOM are preserved. `server/app.py:241` guards formula/control prefixes for text cells while `_csv_row` retains numeric cells as numbers. The server formula tests and browser byte-preservation tests passed.
- `web/js/export.js:181` rejects filenames containing slash/backslash and requires a CSV response type. Download navigation uses an object URL at lines 184–189. Local probes rejected `../escape.csv`, `folder\\escape.csv`, a missing filename, and an empty filename with a visible failure message.
- All rendered report values flow through `textContent` (`web/js/export.js:9`), including names, utility labels, evidence, numeric text, assumptions, filter text, source editions, and attribution. `project-detail.js:24` permits citation links only for its local document allowlist and a positive integer page; it does not use the supplied source URL.
- A local Chromium probe replaced selected and ranked fields with HTML/script/event-handler strings and a formula-like suffix; it also supplied hostile source document/page/URL, assumption ID, source date and attribution. The report retained text without creating images, scripts, frames, objects, embeds, SVGs or event-handler attributes. Invalid source citations produced no links. There were zero page errors and zero external requests. Non-numeric distance input displayed the existing unavailable value rather than becoming executable content.
- Planner Coordination status remains genuinely blank: the probe found two empty fields (selected pair and ranked row) and verified each had at least 32 px height in print media. No prefilled coordination claim appeared.
- Existing failure and selection-race tests passed: failures remain visible, controls recover, failed filters disable export/print, and a changed selection cancels pending printing.

## Checks actually run

Environment for both commands: `GRIDLOCK_TEST_PORT=8786`, `GRIDLOCK_AI=off`, `GRIDLOCK_GOOGLE=off`, installed local `PLAYWRIGHT_BROWSERS_PATH`; Python invoked only through `$env:GRIDLOCK_PY`.

1. `& $env:GRIDLOCK_PY -m pytest tests/e2e/test_export.py tests/api/test_detail_export.py -q -k 'not letter_print' -p no:cacheprovider` — **26 passed, 2 deselected in 21.54s**. The two Letter screenshot/PDF cases were deliberately excluded to avoid overwriting the builder's artifacts; this is a focused run, not a full gate.
2. Ephemeral stdin Python/Playwright probe using the repository's fixture-owned loopback server — **PASS** for hostile selected/ranked/source/attribution values, invalid citation links, blank visible planner fields, four malformed filenames, zero page errors and zero external requests. The fixture closed its server and the probe closed its browser. No probe source file or product edit was written.

## Limits

The scoped review covered the changed export module, print CSS, page/bootstrap hooks, tests, and relevant filter, citation and server-export callers. It did not re-review AI spending guards, credential storage, pipeline prompt handling, or unrelated service routes as a full security audit. No credentials were read or tested, and no third-party service was contacted.

Raw project descriptions are **not rendered** by `web/js/export.js:42`–55: its project block includes name, utility, in-service text, year, accuracy and citation. Hostile description input therefore has no print sink to exercise. This is a content/coverage limit for the lead's acceptance review, not a security defect or proof of description-rendering correctness.

The builder's reported 277 Python + 18 shell + 18 audit results remain builder evidence. This judge did not run that gate, inspect physical printer output, or open the CSV in spreadsheet software. Formula handling was verified through the local API and browser download bytes.

2026-09-26 — Review printable attribution and citation construction along with project names; the same text-node boundary protects every rendered data field.

material improvement still available: no
