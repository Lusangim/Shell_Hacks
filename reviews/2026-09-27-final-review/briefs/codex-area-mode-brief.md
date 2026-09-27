# Codex task: "Explore an area" becomes a tool you switch on (founder request, 2026-09-27)

You are working in a git worktree of GridLock on branch `codex/area-mode`. It was cut from Claude's
integration branch, which includes the UI pass and the savings work. Work only on this task, commit on this
branch, and stop. Don't push. Run tests on port 8776 (`GRIDLOCK_TEST_PORT=8776`), never 8765.

## Why

Today any click on empty map space drops a 40 km area circle and opens the area panel (`web/js/area.js`,
`map.on("click", ...)`). New users click the map to pan or deselect and get a circle they did not ask for.
The founder wants the area tool to happen only after the user turns it on with a clear button.

## What to build

1. **A map button "Explore an area"** with an icon from `web/icons/` (map-pin.svg), placed with the map's
   own controls (near the zoom buttons or the Map / Google Maps / Satellite group). Match their look: use
   the existing tokens and button styles in `web/css/app.css`, and put new rules in a new file
   `web/css/area-mode.css` linked from `web/index.html`. It is a toggle with `aria-pressed`, a visible
   focus ring, a 44 px target on phones, and a tooltip or hint text.
2. **Area mode.**
   - When the button is on, the map cursor becomes a crosshair and a short status line says "Click the map
     to choose the centre of a 40 km area. Esc cancels."
   - The next click on empty map space calls the existing `explore({lat, lon})`, then switches the mode off.
   - Clicking the button again, or pressing Esc, cancels the mode without opening anything.
   - Clicking a project line or dot while the mode is on keeps its normal project behaviour.
3. **Without area mode, a map click does nothing to the area.** Remove the unconditional `map.on("click")`
   explore. Keep everything else as it is: search, then "Explore this area"; the radius slider; Clear; Esc
   to clear an open area; and restoring `?area=lat,lon&radius_km=` from the URL.
4. **Screen readers:** the button's accessible name is "Explore an area", and the status line is announced
   (reuse the page's existing polite status region if there is one).

## Tests (write them first; keep them honest)

In `tests/e2e/test_area.py`, and a new file if that is cleaner:
- With the mode off, a click on empty map space opens no area panel and draws no circle.
- Mode on, then a click opens the area panel for that point and turns the mode off (`aria-pressed="false"`).
- Pressing the button again, or Esc, cancels the mode with nothing drawn.
- The button can be reached by Tab, has a visible focus outline, and passes axe (wcag2a/aa, 21a/aa), in light
  and dark, at 1440x900 and 390x844.
- An existing test that created an area by clicking the map must switch the mode on first. Don't delete any
  assertion.

Run `tests/e2e/test_area.py` plus any test file you changed, and `python -m pytest tests/api -q`. Set
`PLAYWRIGHT_BROWSERS_PATH=%USERPROFILE%\dev\ms-playwright`, `GRIDLOCK_AI=off` and `GRIDLOCK_GOOGLE=off`.

## Don't touch

Other agents are editing these files right now: `web/js/brief.js`, `web/js/overlap-detail.js`,
`web/js/list.js`, `web/js/tour-content.js`, `web/js/map.js` (labels), and the panel layout in `web/css/app.css`.
If you need a hook in one of them, keep it to a few lines and say so in your report.

## Done means

All the tests above pass, and there is one commit, `WEB: area tool is switched on by a map button (founder request)`,
on `codex/area-mode`. Your final message lists the files changed, the tests run with their totals, and anything
you could not finish.
