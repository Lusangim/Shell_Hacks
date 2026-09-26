# DIRECTION v2 — modern map (founder, 2026-09-26 ~10:30 EDT) — replaces DIRECTION.md's visual style

## The founder's words
- "why is it only showing georgia and the map itself isnt that interactive to zoom in and out what about
  SC I dont like the map style either lets go more modern style the map looks very outdated"
- "Is google maps possible?" → chose **Both**: a Google-style offline map as the default, plus a
  "Google Maps / Satellite" switch when a key and Wi-Fi are available.
- Map file: "Street detail — 221 MB".

## THESIS
A modern, Google-Maps-like interactive map of Georgia and South Carolina where two utilities' planned
lines stand out clearly. The map is the product: it fills the screen, zooms smoothly from both states down
to street level, and the panels float over it as clean cards.

## What changes from DIRECTION.md (the System Wall Map / Plan Sheet look is retired)
- **Base map:** an offline OpenStreetMap vector map (Protomaps basemap v4, extract of GA + SC at zoom ≤ 13,
  file `C:\Users\lucia\dev\gridlock-assets\gasc-z13.pmtiles`, 221 MB), drawn with **protomaps-leaflet 5.1.0**
  under our Leaflet SVG layers: roads, highways, rivers, lakes, parks, towns and state names at every zoom.
  Light theme = Protomaps "light" flavour (Google-like); dark theme = "dark" flavour. Attribution:
  "© OpenStreetMap contributors · Protomaps".
- **Optional Google layers:** "Google Maps" (roadmap) and "Satellite" (hybrid) via **Leaflet.GoogleMutant
  0.16.0** (Beerware licence), which loads Google's official Maps JavaScript API. Shown in a basemap switch
  **only** when a Google Maps browser key is configured and the browser is online; otherwise the switch is
  hidden and the offline map is used. Google's logo and attribution stay visible (the plugin keeps them).
- **Both states, always:** the first view fits all of Georgia and South Carolina (not a border close-up);
  state names visible; SC must read as clearly as GA. The border region stays one click away.
- **Real zoom:** mouse-wheel zoom ON, double-click zoom, pinch zoom, keyboard +/−, smooth zoom animation;
  zoom range 6–17 (vector data overzooms beyond 13). Selecting a pair or a search result flies to it
  (instant under reduced motion). Wheel or trackpad scrolling inside a panel scrolls the panel only — it
  never zooms or pans the map (Leaflet `L.DomEvent.disableScrollPropagation` / `disableClickPropagation`
  on every panel and control).
- **Modern chrome:** panels are floating cards (12 px radius, soft shadow, 16 px margins) over the full-bleed
  map; system font (`system-ui, -apple-system, "Segoe UI", sans-serif`) with no small caps; clear hierarchy
  (20–24 px titles, 14–16 px body); pill-shaped chips for bands and accuracy; icons from `web/icons/`;
  hover and focus states on every row and control; the ranked list stays the primary panel.
- **Lines on the new map:** keep the validated utility palette (DIRECTION.md § OWN-WORLD) and the rules:
  line weight by voltage; solid = exact, dashed = approximate; unknown never drawn. Every project line
  gets a white (light) / near-black (dark) casing 2 px wider than the line so it separates from basemap
  roads. The selected pair gets a thicker line, a soft glow halo and floating labels. The scripted audit
  re-measures each utility colour's contrast against the new basemap's land colour in both themes (≥ 3:1)
  and adjusts only the token values if one fails.
- **Unchanged:** every data and honesty rule (verbatim data, source document + page, accuracy labels,
  savings as estimates), the glossary, accessibility (the ranked list is a complete keyboard path without
  the map; bands never by colour alone), light default for the projector, designed dark theme.

## FIRST VIEWPORT
**1440 px:** full-bleed modern map fitting GA + SC; a floating left card (≈ 400 px) with the title,
the plan editions, "N of M projects have no overlap within 40 km", the status line, search + Filters, and
the ranked list; a small floating basemap switch (top right: Map · Google Maps · Satellite, the last two
only with a key and online); zoom buttons; the timeline as a floating bar at the bottom.
**390 px:** full-screen map; the card becomes a bottom sheet (peek: title, status, first two rows);
basemap switch and zoom buttons stay reachable; targets ≥ 44 px.

## Readable text (founder, ~10:45: "these big text blocks … feel messy and hard to understand; make it easier for the reader to follow")
Every detail block follows one pattern: **answer first, then at most three short bullets, then the raw
detail behind a disclosure** ("How we estimated this ▸", "Location sources ▸", "Source text ▸").
- Plain language; sentences ≤ ~20 words; one idea per bullet; glossary terms only.
- **Never on screen:** internal IDs (`desc-p41`, `sertp-p107-…`), raw enum values (`shared_endpoint`,
  `range`), file paths (`data/raw/…`), dataset feature codes outside a sources disclosure, or code-like
  strings. Say "the Dominion project", "shared endpoint", "HIFLD transmission lines".
- Numbers: thousands separators, currency rounded to the assumptions' precision, ranges as "$54,000 to
  $161,000", units spelled plainly ("km", "kV"), the word **estimate** on every estimate.
- Honesty stays visible: the "estimate" label, the assumption and its source/date, "not verified" where
  the plans do not prove sharing, accuracy, and document + page for every fact. The disclosure holds the
  full verbatim evidence.
- **Illustration only — every sentence must come from the record's own fields, never invented.** For
  the savings block now reading "Estimated coordination saving on printed plan cost; partner cost not stated
  for desc-p41 ($5,376,418); team-assumed 1%-3% of this known scope only; shared savings unverified":
  > **Possible saving (estimate): $54,000 to $161,000**
  > - Based on the Dominion project's plan cost: $5,376,418. The Georgia Power project's plan gives no cost.
  > - Assumes coordination saves 1% to 3% of that cost (our screening assumption).
  > - Not verified: the plans do not show the projects sharing work.
  > How we estimated this ▸
  For the location block: "**Location: approximate** · Drawn between its two endpoints · Okatie's position
  is inferred from the plan (to confirm on Dominion's route map) · Location sources ▸". For why they touch:
  "**They share an endpoint: McIntosh**" + one evidence line with document and page + "Source text ▸".
- If a readable layout needs structured fields the contracts lack, add them through a recorded contract
  change (reason, type review, fixtures re-validated) — never by parsing prose in the browser.

## Guided walkthrough (founder: "a walkthrough feature that explains everything about the demo we are building")
- A **"Take the tour"** button in the title card, plus a one-time, dismissible "New here? Take the tour"
  prompt on first visit (remembered in localStorage, wrapped in try/catch).
- 8–12 short steps anchored to the real interface, each a floating card with a title, 1–2 plain sentences,
  a step count, Back / Next / Skip tour. The tour follows the demo path with real data: what GridLock does
  and why (two utilities' public plans, 40 km, same timeframe) → the map (both states, colours = utilities,
  solid = exact, dashed = approximate) → the ranked list and how the score works (savings are not in the
  score) → distance bands → search "Savannah" → open the top pair → why they appear together + source
  document and page → the savings estimate and what it assumes → accuracy and what is unverified →
  timeline slider → filters → area explorer → coordination brief (AI-drafted or Template) → export.
  Steps for features not built yet are skipped automatically.
- Accessible: focus moves into the step card and back on exit; Esc closes; keyboard Back/Next; the target
  gets a visible highlight ring (not colour alone); the step text is announced; reduced motion honoured;
  works at 1440 and 390 px; never blocks the app if a target is missing.
- All tour text lives in one content file (e.g. `web/js/tour-content.js`) so every word can be reviewed;
  the change-reviewer judge reads it; no external library.

## What the WEB lane must not miss
- No network in tests: the offline map must work with non-local requests blocked; tests never contact
  Google. With no key configured, the Google switch is absent and no Google request is ever made.
- The Google key is never logged, printed, committed or stored in the repo (see MISSION amendment 2).
- CSP stays `default-src 'self'` unless a key is configured; only then are Google's documented hosts
  added.
- Keep map features in the DOM (Leaflet SVG) for our project lines; only the base map is canvas.
