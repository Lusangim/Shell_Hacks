# Codex task: a coordination tracker for each pair (founder request, 2026-09-27)

First, create your own worktree so your commits work. From this working copy, run:
`git worktree add C:\Users\lucia\dev\gridlock-wt\web-tracker -b codex/tracker claude/integrate`. Do all the work
inside `C:\Users\lucia\dev\gridlock-wt\web-tracker`, and leave this working copy's files and branches alone.
`claude/integrate` is Claude's integration branch, with the UI pass so far, the savings work, the new brief
panel, the tailored CSV and print report, the area button, and Start here plus the impact summary.

Build the tracker below, commit on `codex/tracker` and stop. Don't push. Run tests on port 8778
(`GRIDLOCK_TEST_PORT=8778`), never 8765. Set `PLAYWRIGHT_BROWSERS_PATH=%USERPROFILE%\dev\ms-playwright`,
`GRIDLOCK_AI=off` and `GRIDLOCK_GOOGLE=off`. Don't rebuild `data/build`: none of this task changes the pipeline.

## Why

GridLock finds and ranks pairs; the tracker shows what a planner does next. For each pair they can record
where the coordination stands and a short note. It is saved only in this browser, with no server, account or
message sending. The status then appears in the ranked list, the print report and the CSV, whose
"Coordination status" and "Notes" columns the server leaves blank on purpose.

## What to build

1. **Storage (`web/js/tracker.js`, new).**
   - Use localStorage key `gridlock-tracker-v1`, holding `{ [pairId]: { status, note, updated } }`.
   - Status is one of "Not started" (the default, stored as absent), "Contacted", "Meeting set",
     "Coordinating" or "Not relevant".
   - The note is plain text, at most 300 characters.
   - Wrap every storage read and write in try/catch. When storage is unavailable, the widget says "Tracking
     needs browser storage, which is off in this browser" and nothing else breaks.
   - Only keep entries whose key matches the pair ID pattern the app already uses (`PAIR_ID` in
     `web/js/overlap-detail.js`), and validate the status against the list above.
2. **Pair widget.**
   - Add a container `<section id="pair-tracker">` inside `#overlap-detail`, directly above `#brief-panel` in
     `web/index.html`.
   - It holds a heading "Your coordination status", a labelled select with the five statuses, a labelled
     notes textarea (maxlength 300), and a hint: "Saved in this browser only. It is included when you print
     or export."
   - It saves on change, and on input with a short debounce, and announces "Saved" politely.
   - It renders for the pair that is open. Take the pair ID from the page state
     (`state.selectedOverlapId` in `web/js/state.js`) and listen for the open and close of pairs; the
     `hashchange` and the existing detail flow are enough. Don't restructure `overlap-detail.js`.
3. **Ranked list chip.**
   - Tracked pairs, meaning any status except "Not started", show a small status chip in their list row.
   - Add the chip from tracker.js after the list renders: dispatch a `gridlock:list-rendered` event at the
     end of the render function in `web/js/list.js` (one line), and decorate rows by
     `[data-overlap-id]`. Don't change the row layout otherwise. Another agent is restyling rows.
4. **Print report.** In `web/js/export.js`, the "Coordination status" cells and the selected pair's
   coordination field are rendered empty today. Fill them with the tracked status and note through a
   function exported by tracker.js, as a two-line hook in export.js. Keep the class `coordination-status`.
   Untracked pairs stay empty so they can be filled in by hand.
5. **CSV.**
   - Export CSV downloads the server bytes. When any pair in the export is tracked, fill that row's
     "Coordination status" and "Notes" cells in the browser before saving.
   - Use a small, correct RFC 4180 parser and writer in tracker.js: quoted fields, doubled quotes, CR/LF
     inside quotes, the UTF-8 BOM and CRLF line ends. Find the columns by header name, never by position.
   - Escape a note that starts with `=`, `+`, `-`, `@`, a tab, CR or LF by prefixing a single quote, the same
     rule as the server's `_csv_text`.
   - When nothing is tracked, the downloaded bytes must equal the server's bytes exactly; existing tests
     check this.
6. **Styles:** add a new `web/css/tracker.css`, linked from index.html. Use the existing tokens, light and
   dark, give controls 44 px targets on phones, and make focus visible.

## Tests (write them first; new file `tests/e2e/test_tracker.py`)

- Set "Contacted" plus a note on pair #1, reload, and both persist; the list row shows the chip.
- Change the status back to "Not started": the chip disappears and the entry is removed.
- Print report: pair #1's row and the selected-pair field show "Contacted" and the note.
- CSV:
  - With pair #1 tracked, the downloaded row for pair #1 has "Contacted" and the note, and every other
    cell of every row equals the server CSV.
  - A note "=SUM(1,1)" exports as "'=SUM(1,1)".
  - With nothing tracked, the download bytes equal the server bytes.
- Storage disabled (make localStorage throw in an init script): the widget shows the message, the page
  still works and there are no console errors.
- The widget passes axe (wcag2a/aa, 21a/aa) in light and dark at 1440x900 and 390x844, and keyboard alone can
  set a status.
- Run your new file, `tests/e2e/test_export.py`, `tests/e2e/test_overlap_detail.py`, `tests/e2e/test_shell.py` and
  `python -m pytest tests/api -q`.

## Don't touch

Other agents own these right now, so keep to the hooks described above:
- the rest of `list.js`, `overlap-detail.js`, `brief.js`, `tour-content.js`, `map.js` and `area.js`;
- the panel layout in `app.css`;
- `server/app.py`, because the CSV stays server-generated.

## Done means

All the tests above pass, and there is one commit, `WEB: coordination tracker saved in the browser, shown in list,
print and CSV (founder request)`, on `codex/tracker`. Your final message lists the files changed, the tests run
with their totals, and any hook added outside tracker.js.
