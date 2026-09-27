import { refreshProjectStyles } from "./map.js";
import { state } from "./state.js";

const STEP_MS = 400;

export function setupTimeline(filters) {
  const range = document.getElementById("timeline-year");
  const output = document.getElementById("timeline-output");
  const all = document.getElementById("timeline-all");
  const play = document.getElementById("timeline-play");
  const status = document.getElementById("timeline-status");
  let first = null;
  let last = null;
  let timer = null;
  let outsideLink = false;

  function stop() {
    if (timer !== null) clearInterval(timer);
    timer = null;
    play.textContent = "Play years";
    play.setAttribute("aria-pressed", "false");
  }

  function refresh() {
    if (first === null) return;
    const year = state.timelineYear;
    const entering = state.projects.filter((feature) => feature.properties.year === year).length;
    const unknown = state.projects.filter((feature) => feature.properties.year == null).length;
    let lit = 0;
    const rows = new Map(Array.from(document.querySelectorAll('[data-testid="overlap-row"]'),
      (item) => [item.dataset.overlapId, item]));
    for (const pair of state.overlaps) {
      const hasYears = Number.isInteger(pair.a_year) && Number.isInteger(pair.b_year);
      const inWindow = year != null && hasYears && Math.abs(pair.a_year - year) <= 1 && Math.abs(pair.b_year - year) <= 1;
      const row = rows.get(pair.id);
      if (row) row.dataset.timeline = year == null ? "all" : inWindow ? "lit" : hasYears ? "outside" : "unknown";
      if (inWindow) lit += 1;
    }
    const byId = new Map(state.projects.map((feature) => [feature.properties.id, feature.properties.year]));
    const mark = (element, id) => {
      const projectYear = byId.get(id);
      element.dataset.timeline = year == null ? "all" : projectYear == null ? "unknown" : projectYear === year ? "entering" : "other";
    };
    document.querySelectorAll('[data-testid="project-feature"]').forEach((element) => mark(element, element.dataset.projectId));
    document.querySelectorAll('[data-testid="project-row"]').forEach((element) => mark(element, element.dataset.projectRef));
    range.value = String(year ?? first);
    output.textContent = year == null ? "All years" : String(year);
    range.setAttribute("aria-valuetext", year == null ? "All years"
      : `${year}: ${entering} projects entering service, ${lit} pairs in the year window`);
    all.setAttribute("aria-pressed", String(year == null));
    if (year == null) {
      status.textContent = outsideLink
        ? `Linked year is outside the loaded plan years (${first} to ${last}). Showing all years.`
        : `Showing all ${state.overlaps.length} ranked pairs. ${unknown} projects with unknown in-service year.`;
    } else if (lit === 0) {
      status.textContent = `No ranked pairs meet the ${year} year window under current filters. ${entering} projects enter service; ${unknown} projects with unknown in-service year.`;
    } else {
      status.textContent = `${lit} pairs in the ${year} year window; ${entering} projects enter service. ${unknown} projects with unknown in-service year.`;
    }
    refreshProjectStyles();
  }

  function choose(year, { write = true, keepPlaying = false } = {}) {
    if (!keepPlaying) stop();
    if (year != null && (year < first || year > last || !Number.isInteger(year))) return;
    state.timelineYear = year;
    outsideLink = false;
    if (write) filters.setYear(year);
    refresh();
  }

  function fromURL() {
    if (first === null) return;
    stop();
    const raw = filters.year();
    const year = raw ? Number(raw) : null;
    if (year != null && (year < first || year > last)) {
      state.timelineYear = null;
      outsideLink = true;
      filters.setYear(null, true);
    } else {
      state.timelineYear = year;
      outsideLink = false;
    }
    refresh();
  }

  function hydrate(projects) {
    const years = projects.map((feature) => feature.properties.year).filter(Number.isInteger);
    if (years.length === 0) {
      status.textContent = "No in-service years stated in the loaded plans.";
      return;
    }
    first = Math.min(...years);
    last = Math.max(...years);
    range.min = String(first);
    range.max = String(last);
    range.disabled = first === last;
    play.disabled = first === last;
    fromURL();
  }

  range.addEventListener("input", () => choose(Number(range.value)));
  all.addEventListener("click", () => choose(null));
  play.addEventListener("click", () => {
    if (timer !== null) { stop(); return; }
    if (state.timelineYear == null || state.timelineYear >= last) choose(first);
    play.textContent = "Pause years";
    play.setAttribute("aria-pressed", "true");
    timer = setInterval(() => {
      if (state.timelineYear >= last) { stop(); return; }
      choose(state.timelineYear + 1, { keepPlaying: true });
      if (state.timelineYear >= last) stop();
    }, STEP_MS);
  });
  window.addEventListener("popstate", fromURL);
  return { hydrate, refresh };
}
