import { loadShellData } from "./api.js";
import { initializeMap, refreshMapTheme, renderMap } from "./map.js";
import { renderList, renderUnknownLocations, selectFirstOverlapForProject } from "./list.js";
import { state } from "./state.js";

const status = document.getElementById("status");
const listState = document.getElementById("list-state");

function showState(message, kind) {
  listState.replaceChildren();
  listState.hidden = false;
  listState.className = `list-state ${kind}`;
  listState.dataset.testid = `${kind}-state`;
  listState.append(document.createTextNode(message));
  if (kind === "error") {
    const retry = document.createElement("button");
    retry.type = "button";
    retry.textContent = "Try again";
    retry.addEventListener("click", load);
    listState.append(retry);
  }
}

function editionText(meta) {
  const documents = meta.source_documents || [];
  if (!documents.length) return "Plan editions unavailable";
  return documents.map((document) => [document.doc, document.date].filter(Boolean).join(" / ")).join(" · ");
}

async function load() {
  showState("Loading ranked opportunities", "loading");
  delete status.dataset.src;
  status.textContent = "Loading public plans.";
  try {
    const { projects, overlaps, meta, basemap } = await loadShellData();
    if (!Array.isArray(projects.features) || !Array.isArray(overlaps)) throw new Error("Invalid data shape");
    state.projects = projects.features;
    state.overlaps = overlaps;
    renderMap(projects, basemap);
    renderList(overlaps, projects);
    renderUnknownLocations(projects);
    document.getElementById("editions").textContent = editionText(meta);
    const count = meta.stage_counts?.kept ?? projects.features.length;
    const noOverlap = meta.no_overlap_count;
    document.getElementById("no-overlap").textContent = Number.isInteger(noOverlap)
      ? `${noOverlap} of ${count} projects have no overlap within 40 km`
      : "No-overlap count unavailable";
    if (overlaps.length === 0) {
      showState("No overlaps in the loaded plans. Try again after checking the source data.", "empty");
      status.textContent = "No ranked opportunities in the loaded plans.";
    } else {
      listState.hidden = true;
      status.dataset.src = "count";
      status.textContent = `${overlaps.length} ranked opportunities loaded.`;
    }
  } catch (_error) {
    showState("Could not load public plan data. Check the local server and try again.", "error");
    delete status.dataset.src;
    status.textContent = "Public plan data could not be loaded.";
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
setupTheme();
setupSheet();
document.addEventListener("gridlock:project-click", (event) => selectFirstOverlapForProject(event.detail.projectId));
load();
