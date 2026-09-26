// Keep every tour word here for copy review.
export const tourWords = {
  launch: "Take the tour", invitation: "New here? Take the tour", dismiss: "Dismiss tour invitation", dismissSymbol: "×",
  label: "GridLock tour", back: "Back", next: "Next", finish: "Finish tour", skip: "Skip tour",
  count: (index, total) => `Step ${index} of ${total}`,
};

export const tourSteps = [
  { id: "purpose", target: ".title-block", title: "Public plans, shared possibilities",
    body: "Compare public transmission plans across Georgia and South Carolina. GridLock screens projects from different utilities within 40 km for possible coordination around similar timeframes." },
  { id: "map", target: "#map", title: "Read the map",
    body: "Colours identify utilities across both states; solid lines mark exact locations and dashed lines mark approximate locations. Unknown locations stay in the list." },
  { id: "ranking", target: "#opportunities-heading", prepare: "list", title: "How pairs are ranked",
    body: "The score combines distance band, timing, accuracy and a cross-state factor; savings are not in the score. Bands are touching, under 1.6 km, under 8 km and under 40 km." },
  { id: "search", target: "#search-form", title: "Find Savannah",
    body: "Search Savannah to find a place, then choose a result to move the map. You can also search project names; the tour keeps your current search." },
  { id: "pair", target: ".overlap-button", prepare: "list", title: "Open the top pair",
    body: "The first row is the highest-ranked pair in your current results. Next opens that real pair so you can inspect the evidence." },
  { id: "source", target: ".overlap-projects", prepare: "pair", title: "Check the source",
    body: "Read why these projects appear together, then check each project's source document and page. Nearby projects do not prove shared work." },
  { id: "savings", target: ".overlap-assumptions, [data-src='savings_status']", prepare: "pair", title: "Estimates and uncertainty",
    body: "Savings are screening estimates based on the stated costs or proxies and assumptions; they are not measured savings. Check location accuracy too: shared work remains unverified." },
  { id: "timeline", target: "#timeline", title: "Compare years",
    body: "Move the in-service year slider to compare project timing, or choose All years. A missing year stays unknown." },
  { id: "filters", target: "#filters-toggle", title: "Narrow the results",
    body: "Filters narrow utilities and distance bands; More filters includes voltage, project type and years. Both projects must pass your project filters." },
  { id: "area", target: "#explore-area", title: "Explore an area",
    body: "After choosing a place, Explore this area shows nearby projects and pairs. Use the radius control to change the area." },
  { id: "brief", target: "#brief-panel, #coordination-brief, [data-testid='brief-panel']", title: "Read a coordination brief",
    body: "The brief brings together public-plan evidence, possible coordination and caveats. Check whether it is labelled AI-drafted or Template, and verify it before use." },
  { id: "export", target: ".report-controls", prepare: "export", title: "Keep a copy",
    body: "Export CSV saves the current filtered results; Print report prepares a readable copy with sources. Estimates remain for discussion only." },
];
