// Keep every tour word here for copy review.
export const tourWords = {
  launch: "Take the tour", invitation: "New here? Take the tour", dismiss: "Dismiss tour invitation", dismissSymbol: "×",
  label: "GridLock tour", back: "Back", next: "Next", finish: "Finish tour", skip: "Skip tour",
  count: (index, total) => `Step ${index} of ${total}`,
};

// Written for a first-time judge: what each feature does, how to read it, and the numbers behind it.
export const tourSteps = [
  { id: "purpose", target: ".title-block", title: "What GridLock does",
    body: "The challenge: find where neighbouring utilities' planned work overlaps in place or time. GridLock compares two public plans (Dominion Energy SC and the Georgia utilities in SERTP), ranks every pair within 40 km, and shows the source page behind each fact." },
  { id: "map", target: "#map", title: "Read the map",
    body: "Each colour is a utility. Solid lines and filled dots are exact; dashed lines and rings are approximate. Dotted lines or dashed rings are town-level: placed at a town centre because the substation is not mapped. Unknown locations stay in the list, never guessed." },
  { id: "ranking", target: "#opportunities-heading", prepare: "list", title: "How pairs are ranked",
    body: "Score = closeness × timing × location × state line × savings. Closeness: touching 4, under 1.6 km 3, under 8 km 2, under 40 km 1. Timing: same year 1.0, 1 year apart 0.7, 2 years 0.4. Exact 1.0, approximate 0.8. Crossing SC-GA 1.5. Savings add at most 30%, so distance leads." },
  { id: "search", target: "#search-form", title: "Find Savannah",
    body: "Planners start from a place. Search Savannah and choose the result to move the map; project names work too. Savannah holds the top pairs: Dominion's Okatie–McIntosh tie meets Georgia Power work at McIntosh." },
  { id: "pair", target: ".overlap-button", prepare: "list", title: "Open the top pair",
    body: "The first row is the top pair in your current results. With no filters, #1 scores 5.8: touching (4) × same year (1.0) × one approximate location (0.8) × crosses SC-GA (1.5) × savings (1.21). Next opens it; every pair's detail ends with its own score, part by part." },
  { id: "source", target: ".overlap-projects", prepare: "pair", title: "Check the source",
    body: "Every project shows its plan document and PDF page, with names copied word for word. The reason the two appear together (same substation, shared endpoint, or simply nearby) is stated. Nearby is a lead to check, not proof of shared work." },
  { id: "savings", target: ".overlap-assumptions, [data-src='savings_status']", prepare: "pair", title: "How savings are estimated",
    body: "From the team's unit costs by job type (MISO prices, 2026). Closer projects can share more: touching - outages and crossings; under 1.6 km - land and access roads; under 8 km - laydown yards; under 40 km - crews and equipment. Only costs both jobs need count. Estimates, not measured savings." },
  { id: "timeline", target: "#timeline", title: "Compare years",
    body: "Timing is the second signal. Slide the in-service year to see what enters service together. Same year scores 1.0, one year apart 0.7, two years 0.4; beyond two years there is no savings estimate. A missing year stays unknown." },
  { id: "filters", target: "#filters-toggle", title: "Narrow the results",
    body: "Filter by utility and distance band; More filters adds voltage, project type and years. A pair stays only when both of its projects pass your filters." },
  { id: "area", target: "#search-form", title: "Explore an area",
    body: "Search for a place, choose a result and press Enter, then select Explore this area. It lists every project and pair within 40 km, and its radius control changes the circle from 1 to 80 km." },
  { id: "brief", target: "#brief-panel:has(#brief-copy:enabled)", prepare: "pair", title: "Read a coordination brief",
    body: "A one-page note for the pair: what, where, when, what could be shared, the savings range, which organisations to contact, and caveats, all from the plans. It is labelled Template or AI-drafted; verify it before use." },
  { id: "export", target: ".report-controls", prepare: "export", title: "Keep a copy",
    body: "Export CSV saves the ranked list you are looking at, laid out like a utility conflict matrix; Print report gives a readable copy with sources. Estimates stay labelled as estimates." },
];
