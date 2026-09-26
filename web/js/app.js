import { loadFilteredData, loadShellData } from "./api.js";
import { initializeMap, refreshMapTheme, renderMap } from "./map.js";
import { renderList, renderUnknownLocations, restorePairSelection, selectFirstOverlapForProject } from "./list.js";
import { setupProjectDetail } from "./project-detail.js";
import { setupOverlapDetail } from "./overlap-detail.js";
import { setupSearch } from "./search.js";
import { setupFilters } from "./filters.js";
import { setupTimeline } from "./timeline.js";
import { setupExport } from "./export.js";
import { state } from "./state.js";

const status = document.getElementById("status");
const listState = document.getElementById("list-state");
const projectView = setupProjectDetail();
const overlapView = setupOverlapDetail(projectView);
const mapPairOpen = document.getElementById("map-pair-open");
const filterControl = setupFilters(() => { void applyFilters(); });
const timeline = setupTimeline(filterControl);
const exportControl = setupExport(filterControl);

function showState(message, kind, retryAction = load) {
  listState.replaceChildren();
  listState.hidden = false;
  listState.className = `list-state ${kind}`;
  listState.dataset.testid = `${kind}-state`;
  listState.append(document.createTextNode(message));
  if (kind === "error") {
    const retry = document.createElement("button");
    retry.type = "button";
    retry.textContent = "Try again";
    retry.addEventListener("click", retryAction);
    listState.append(retry);
  } else if (kind === "empty" && filterControl.hasActive()) {
    const clear = document.createElement("button");
    clear.type = "button";
    clear.textContent = "Clear filters";
    clear.addEventListener("click", filterControl.clear);
    listState.append(clear);
  }
}

function editionText(meta) {
  const documents = meta.source_documents || [];
  if (!documents.length) return "Plan editions unavailable";
  return documents.map((document) => [document.doc, document.date].filter(Boolean).join(" / ")).join(" · ");
}

async function load() {
  exportControl.setReady(false);
  showState("Loading ranked opportunities", "loading");
  delete status.dataset.src;
  status.textContent = "Loading public plans.";
  try {
    const { projects, overlaps, meta, basemap } = await loadShellData();
    if (!Array.isArray(projects.features) || !Array.isArray(overlaps)) throw new Error("Invalid data shape");
    state.basemap = basemap;
    state.meta = meta;
    filterControl.hydrate(projects.features);
    timeline.hydrate(projects.features);
    document.getElementById("editions").textContent = editionText(meta);
    await applyFilters({ projects, overlaps }, true);
  } catch (_error) {
    projectView.showLoadError();
    showState("Could not load public plan data. Check the local server and try again.", "error");
    delete status.dataset.src;
    status.textContent = "Public plan data could not be loaded.";
  }
}

function hashOverlapId() {
  if (!location.hash.startsWith("#overlap=")) return null;
  try { return decodeURIComponent(location.hash.slice(9)); }
  catch (_error) { return null; }
}

function renderFiltered(projects, overlaps, initial) {
  state.projects = projects.features;
  state.overlaps = overlaps;
  renderMap(projects, state.basemap);
  renderList(overlaps, projects);
  renderUnknownLocations(projects);
  projectView.renderProjects(projects.features, overlaps, filterControl.hasActive());
  const selectedId = state.selectedOverlapId ?? hashOverlapId();
  const selectedVisible = selectedId ? restorePairSelection(selectedId) : false;
  mapPairOpen.hidden = !selectedVisible;
  if (initial && location.hash.startsWith("#overlap=")) overlapView.restoreFromHash();
  else overlapView.refreshFilterState();
  const noOverlap = document.getElementById("no-overlap");
  if (filterControl.hasActive()) {
    const paired = new Set(overlaps.flatMap((pair) => [pair.a, pair.b]));
    const unpaired = projects.features.filter((feature) => !paired.has(feature.properties.id)).length;
    delete noOverlap.dataset.src;
    noOverlap.textContent = `${unpaired} of ${projects.features.length} filtered projects are not in shown pairs`;
  } else {
    noOverlap.dataset.src = "no_overlap_count";
    const count = state.meta.stage_counts?.kept ?? projects.features.length;
    noOverlap.textContent = Number.isInteger(state.meta.no_overlap_count)
      ? `${state.meta.no_overlap_count} of ${count} projects are not in computed pairs; ${projects.features.filter((feature) => !feature.geometry).length} locations unknown`
      : "No-overlap count unavailable";
  }
  if (overlaps.length === 0) {
    showState(filterControl.hasActive()
      ? "No matches for these filters. Clear filters to see all ranked opportunities."
      : "No overlaps in the loaded plans. Try again after checking the source data.", "empty");
  } else listState.hidden = true;
  status.dataset.src = "count";
  status.textContent = filterControl.hasActive()
    ? `${overlaps.length} ranked opportunities match filters. ${projects.features.length} projects shown.${selectedId && !selectedVisible ? " Selected pair is outside current filters." : ""}`
    : `${overlaps.length} ranked opportunities loaded.`;
  timeline.refresh();
  exportControl.setReady(true);
}

async function applyFilters(full = null, initial = false) {
  exportControl.setReady(false);
  const ownRequest = ++state.filterRequest;
  state.filterAbort?.abort();
  state.filterAbort = new AbortController();
  showState("Loading projects and ranked opportunities", "loading");
  try {
    const result = full && !filterControl.hasActive()
      ? full : await loadFilteredData(filterControl.query(), state.filterAbort.signal);
    if (ownRequest !== state.filterRequest) return;
    if (!Array.isArray(result.projects.features) || !Array.isArray(result.overlaps)) throw new Error("Invalid filtered data shape");
    renderFiltered(result.projects, result.overlaps, initial);
  } catch (error) {
    if (ownRequest !== state.filterRequest || error.name === "AbortError") return;
    showState("Could not load filtered public plan data. Check the local server and try again.", "error", () => applyFilters());
    delete status.dataset.src;
    status.textContent = "Filtered public plan data could not be loaded.";
  }
}

function setupTheme() {
  const button = document.getElementById("theme-toggle");
  const icon = document.getElementById("theme-icon");
  const update = () => {
    const dark = document.documentElement.dataset.theme === "dark";
    button.setAttribute("aria-label", `Switch to ${dark ? "light" : "dark"} theme`);
    icon.src = `/web/icons/${dark ? "sun" : "moon"}.svg`;
  };
  update();
  button.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    delete status.dataset.src;
    try {
      localStorage.setItem("gridlock-theme", next);
      status.textContent = `${next === "dark" ? "Dark" : "Light"} theme on.`;
    } catch (_error) {
      status.textContent = "Theme preference will reset on reload.";
    }
    update();
    refreshMapTheme();
    searchControl.refreshTheme();
  });
}

function setupSheet() {
  const button = document.getElementById("sheet-toggle");
  const sheet = document.querySelector(".panel");
  button.addEventListener("click", () => {
    const expanded = sheet.classList.toggle("expanded");
    button.setAttribute("aria-expanded", String(expanded));
    button.textContent = expanded ? "Collapse opportunities" : "Expand opportunities";
    delete status.dataset.src;
    status.textContent = expanded ? "Opportunity sheet expanded." : "Opportunity sheet collapsed.";
    state.map.invalidateSize();
  });
}

initializeMap();
const searchControl = setupSearch();
setupTheme();
setupSheet();
document.addEventListener("gridlock:project-click", (event) => {
  overlapView.close();
  selectFirstOverlapForProject(event.detail.projectId, filterControl.hasActive());
  projectView.openProject(event.detail.projectId, "overlaps");
});
document.addEventListener("gridlock:pair-highlighted", () => { mapPairOpen.hidden = false; });
document.addEventListener("gridlock:pair-open-request", (event) => {
  overlapView.open(event.detail.overlapId, { push: true });
});
mapPairOpen.addEventListener("click", () => {
  if (state.selectedOverlapId) overlapView.open(state.selectedOverlapId, { push: true });
});
load();
