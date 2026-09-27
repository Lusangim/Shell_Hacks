import { loadFilteredData, loadShellData } from "./api.js";
import { initializeMap, refreshMapTheme, refreshPairLabels, renderMap } from "./map.js";
import { renderList, renderUnknownLocations, restorePairSelection, selectFirstOverlapForProject } from "./list.js";
import { setupProjectDetail } from "./project-detail.js";
import { setupOverlapDetail } from "./overlap-detail.js";
import { setupSearch } from "./search.js";
import { renderStartHere } from "./start-here.js";
import { renderImpact } from "./impact.js";
import { setupFilters } from "./filters.js";
import { setupTimeline } from "./timeline.js";
import { setupExport } from "./export.js";
import { setupTour } from "./tour.js";
import { state } from "./state.js";
import { setupShell } from "./shell.js";
import { setupTracker } from "./tracker.js";

const status = document.getElementById("status");
const listState = document.getElementById("list-state");
const projectView = setupProjectDetail();
const overlapView = setupOverlapDetail(projectView);
setupTracker();
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
  if (kind === "loading") {
    // Skeleton rows keep the list's shape while the named operation runs.
    for (let index = 0; index < 3; index += 1) {
      const row = document.createElement("span");
      row.className = "skeleton-row";
      row.setAttribute("aria-hidden", "true");
      listState.append(row);
    }
  } else if (kind === "error") {
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

function renderEditions(meta) {
  const target = document.getElementById("editions");
  const documents = meta.source_documents || [];
  if (!documents.length) {
    target.textContent = "Plan editions unavailable";
    return;
  }
  // One plan per line, each exactly as the metadata names it.
  target.replaceChildren(...documents.map((source) => {
    const line = document.createElement("span");
    line.textContent = [source.doc, source.date].filter(Boolean).join(" / ");
    return line;
  }));
}

function showLoadFailure() {
  document.getElementById("editions").textContent = "Plan editions not loaded.";
  const noOverlap = document.getElementById("no-overlap");
  delete noOverlap.dataset.src;
  noOverlap.textContent = "Project counts not loaded.";
  document.getElementById("timeline-status").textContent = "In-service years not loaded.";
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
    renderEditions(meta);
    renderStartHere(meta.hotspots);
    await applyFilters({ projects, overlaps }, true);
  } catch (_error) {
    projectView.showLoadError();
    showLoadFailure();
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
  renderImpact(overlaps);
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
      ? `No matches for these filters: ${filterControl.describe()}. Clear filters to see all ranked opportunities.`
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
    icon.dataset.icon = dark ? "sun" : "moon";
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
  function setExpanded(expanded) {
    sheet.classList.toggle("expanded", expanded);
    button.setAttribute("aria-expanded", String(expanded));
    button.textContent = expanded ? "Collapse opportunities" : "Expand opportunities";
    delete status.dataset.src;
    status.textContent = expanded ? "Opportunity sheet expanded." : "Opportunity sheet collapsed.";
    state.map.invalidateSize();
    refreshPairLabels();
  }
  button.addEventListener("click", () => setExpanded(!sheet.classList.contains("expanded")));
  document.addEventListener("focusin", (event) => {
    if (matchMedia("(max-width: 700px)").matches && sheet.classList.contains("expanded")
      && event.target.closest(".map-region, .timeline")) setExpanded(false);
  });
  const searchInput = document.getElementById("search-input");
  searchInput.addEventListener("input", () => {
    document.getElementById("search-state").dataset.active = String(searchInput.value.trim().length > 0);
  });
}

// Report feedback: the status line is a live region for screen readers; after someone uses CSV or
// Print, the outcome also shows for a few seconds as a small toast under the top bar.
function setupReportStatus() {
  const message = document.getElementById("export-status");
  const toast = document.createElement("div");
  toast.className = "report-toast";
  toast.setAttribute("aria-hidden", "true");
  document.body.append(toast);
  let armed = false;
  let timer = null;
  for (const id of ["export-csv", "print-report-button"]) {
    document.getElementById(id).addEventListener("click", () => { armed = true; });
  }
  new MutationObserver(() => {
    const text = message.textContent.trim();
    if (!armed || !/^(CSV download|Could not|Report prepared|Selection changed)/.test(text)) return;
    armed = false;
    const failed = text.startsWith("Could not");
    toast.textContent = text;
    toast.classList.toggle("report-toast-error", failed);
    toast.classList.add("shown");
    clearTimeout(timer);
    timer = setTimeout(() => toast.classList.remove("shown"), failed ? 7000 : 3500);
  }).observe(message, { childList: true, characterData: true, subtree: true });
}

initializeMap();
const searchControl = setupSearch(filterControl);
delete document.documentElement.dataset.areaLayout;
setupTheme();
setupSheet();
setupReportStatus();
setupShell(overlapView);
setupTour();
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
