# Live demo script and Q&A crib

For the judging rounds: Round 1 is a 3-minute live demo, Round 2 allows 3 to 5 minutes. Start the app with
`START`, close the tour invitation, and keep [DEMO.md](DEMO.md) open as a screenshot fallback. Everything
below runs offline.

## The 3-minute demo

| # | Do | Say | It proves | Honest limit |
| --- | --- | --- | --- | --- |
| 1 (15 s) | Show the map. | "Cities coordinate street work on shared platforms like PaverOps. Neighbouring transmission utilities publish separate PDFs, and FERC Order 1920 now asks regions to share long-term needs. GridLock lines up two public plans." | The problem is real and current. | Two plans, not every utility. |
| 2 (20 s) | Point at the colours, the border and the list header. | "230 projects from Dominion Energy SC and the Georgia utilities, 465 pairs within 40 km, ranked. Solid is exact, dashed approximate; 49 unknown locations stay in the list." | Scale, and nothing is guessed. | 139 locations are approximate. |
| 3 (25 s) | Click **Start here → Rincon** (or search "Savannah"), then open pair #1. | "New users start from the places where close pairs cluster. The top pair is right here, at McIntosh." | Real data, easy to start. | |
| 4 (30 s) | In the right pane, open **Why they appear together**, then a link under **Sources**. | "The map zooms to the pair and highlights both lines. Dominion's Okatie-McIntosh tie names McIntosh as an end; Georgia Power upgrades relays at McIntosh. Both are 2028, across the state line. Every fact links to its PDF page." | Page-cited evidence. | The plan does not say where Dominion's new Deerfield station is; shared work is unverified. |
| 5 (30 s) | Open **About the estimate** and **How this pair ranks**. | "Touching jobs could share a yard, crew moves, bulk buying and engineering: $62,000 to $264,000, an estimate from 2026 unit costs. Score 5.8 is touching 4 × same year 1 × one approximate location 0.8 × state line 1.5 × savings 1.21. Distance always counts most." | A ranking anyone can check. | Savings rates are team assumptions; the low end keeps only items with public precedent. |
| 6 (20 s) | Click **Open brief**; open "With the Claude API". | "The brief says who to call and what to settle first. With a Claude API key, an AI-drafted brief adds a plain-language note; here is the example for this pair, passed by the same evidence grader." | Ready for a planner's next step, and where AI fits safely. | The live AI feature is off in this build; names organisations, never people. |
| 7 (30 s) | Search "Savannah", **Explore this area**, then **Invoke storm** (from the southeast, Category 3). | "The area view lists everything within a radius you choose. Now a hypothetical hurricane, not a forecast: it crosses the area and lights up the lines it would damage. The right pane gives the P10 to P90 repair cost, coverage and the next step; thin evidence goes to human review." | Resilience planning on the same public data. | Hypothetical storm and illustrative damage curves; press **Skip to results** if short on time. |
| 8 (10 s) | Set the pair to "Contacted", then Export CSV or Print report. | "Planners track each pair; the status and notes carry into the CSV worksheet and the report." | Works with existing workflows. | Saved in this browser only. |

Close (10 s): "Every fact has a page, every estimate says so, and it runs offline."

## Extra for Round 2 (up to 5 minutes)

- **Data quality story:** routes along existing lines (show the Modoc-McCormick rebuild), town-only flags, and
  why 49 projects stay unknown.
- **Methodology:** the band rules (touching at 1 m or less; under 1.6, 8 and 40 km), geodesic nearest-point
  distance, and the savings tiers by distance and job type.
- **Engineering:** Pydantic contracts that reject impossible data, byte-identical rebuilds, the automated
  test suite with accessibility audits, loopback-only server with a Content Security Policy.
- **Resilience Lab:** try the storm from the Gulf (southwest) and at Category 1 versus 4, and open **Most
  exposed assets** and **Assumptions**. "Holland wind along the track, illustrative fragility by asset class,
  repair ratios on our unit costs, 1,000 seeded draws for P10 to P90. The full plan adds storm replays, flood
  layers and published curves." Plan: [RESILIENCE_LAB_PLAN.md](RESILIENCE_LAB_PLAN.md).

## Q&A crib

- **How is distance measured?** Nearest points between the two shapes in an equal-area projection, then the
  geodesic distance in km. Touching means 1 m or less.
- **Same substation vs shared endpoint?** "Same substation": both projects are work at one substation that
  both plans name. "Shared endpoint": a line in one plan ends where the other project is, and both plans name
  that place. Either way, shared work is unverified until the utilities confirm it.
- **What does "approximate" mean, and where do locations come from?** The plans give names, not coordinates.
  We match names to OpenStreetMap substations and HIFLD line ends. Approximate covers a straight line between
  two matched ends, a route along existing lines, a dot at the one end found, or a town centre ("town only").
- **Why are Georgia-only pairs marked?** They may already plan jointly through Georgia's Integrated
  Transmission System, so the pair carries that note.
- **What do the savings assume?** The team's unit-cost file: MISO's 2026 transmission cost guide (brought to
  2026 at 4% a year) plus public land, wage and rental sources, with team saving rates by distance. Only
  costs both job types need count. See `data/manual/unit_costs_2026.md`.
- **Do savings change the rank?** A little: at most +30%, less than the step between two distance bands, so
  distance always leads.
- **Why SERTP and not a utility IRP?** SERTP's regional plan lists the Georgia utilities' projects with
  pages and years in one public document. Some headers read "(CEII)", but SERTP posts it publicly, and we use
  only that document.
- **What is missing?** The challenge guide's Bluffton and Thomson-Vogtle examples are not in the loaded
  plans; we say so instead of guessing. Okatie's location is inferred and labelled.
- **How do briefs avoid invented facts?** By default a template writes them from the pair's data. A grader
  checks every number, year, page and contact against the data, and contacts are organisations only.
- **Who else does this?** Street-level tools (PaverOps, Coordinate, Accela, one.network) serve cities, and
  grid data aggregators (Our Grid Future, Interconnection.fyi) list projects. We found none that pairs two
  utilities' public transmission plans by distance and timing with page citations.
- **Why doesn't it exist already?** SERTP posts documents only, cost and model data are gated, the free
  federal line layer (HIFLD Open) was retired in 2025, and the cross-region sharing duty in Order 1920 is
  new.
- **Which plan editions?** SCRTP 2026-2030 ($2M and above) and SERTP 2025; SERTP's 2026 preliminary report
  exists and is not loaded yet.
- **What's next?** More boundary utilities, the 2026 SERTP plan, construction windows, and cost and route data
  shared with permission.
