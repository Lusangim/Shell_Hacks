import { state } from "./state.js";
import { fitPairBounds, highlightPair } from "./map.js";
import { citation } from "./project-detail.js";

function field(tag, value, source, className = "") {
  const element = document.createElement(tag);
  if (source) element.dataset.src = source;
  if (className) element.className = className;
  element.textContent = value ?? "not stated";
  return element;
}

function overlapProjects(overlap, byId) {
  return [byId.get(overlap.a), byId.get(overlap.b)];
}

function sourceText(project) {
  const source = project?.properties?.source;
  return source?.doc && source?.page ? `${source.doc}, p. ${source.page}` : "Source page not stated";
}

function selectOverlap(overlap, button, byId, openDetail = true) {
  document.querySelectorAll(".overlap-button[aria-pressed]").forEach((item) => item.setAttribute("aria-pressed", "false"));
  button.setAttribute("aria-pressed", "true");
  state.selectedOverlapId = overlap.id;
  highlightPair(overlap);
  document.dispatchEvent(new CustomEvent("gridlock:pair-highlighted", { detail: { overlapId: overlap.id } }));
  const [a, b] = overlapProjects(overlap, byId);
  const status = document.getElementById("status");
  status.dataset.src = "utility";
  status.textContent = `Selected overlap ${overlap.rank}: ${a?.properties?.utility ?? "utility not stated"} and ${b?.properties?.utility ?? "utility not stated"}.`;
  const layers = state.projectLayers;
  if (layers) {
    const bounds = L.latLngBounds([]);
    layers.eachLayer((layer) => {
      if (layer.feature?.properties?.id === overlap.a || layer.feature?.properties?.id === overlap.b) {
        if (layer.getBounds) bounds.extend(layer.getBounds());
        else if (layer.getLatLng) bounds.extend(layer.getLatLng());
      }
    });
    if (bounds.isValid()) fitPairBounds(bounds);
  }
  if (openDetail) document.dispatchEvent(new CustomEvent("gridlock:pair-open-request", { detail: { overlapId: overlap.id } }));
}

export function renderList(overlaps, projects) {
  const list = document.getElementById("overlap-list");
  list.replaceChildren();
  const byId = new Map(projects.features.map((feature) => [feature.properties.id, feature]));
  for (const overlap of overlaps) {
    const [a, b] = overlapProjects(overlap, byId);
    const row = document.createElement("li");
    row.className = "overlap-row";
    row.dataset.testid = "overlap-row";
    row.dataset.overlapId = overlap.id;
    const button = document.createElement("button");
    button.className = "overlap-button";
    button.type = "button";
    button.setAttribute("aria-pressed", "false");
    const rank = field("span", String(overlap.rank), "rank", "row-rank");
    const main = document.createElement("span");
    main.className = "row-main";
    const utilities = document.createElement("strong");
    utilities.append(field("span", a?.properties?.utility, "utility"), document.createTextNode(" / "), field("span", b?.properties?.utility, "utility"));
    const names = document.createElement("span");
    names.className = "row-name";
    names.append(field("span", a?.properties?.name, "name"), document.createTextNode(" / "), field("span", b?.properties?.name, "name"));
    const sources = document.createElement("span");
    sources.className = "row-name";
    sources.append(field("span", sourceText(a), "source"), document.createTextNode(" / "), field("span", sourceText(b), "source"));
    main.append(utilities, names, sources, field("span", `${overlap.accuracy_pair ?? "unknown"} location`, "accuracy", "row-accuracy"));
    const metric = document.createElement("span");
    metric.className = "row-metric";
    const glyph = { touching: "●", lt_1_6km: "▦", lt_8km: "▥", lt_40km: "▧" }[overlap.band] || "";
    metric.append(field("span", `${glyph} ${overlap.band_label ?? "Distance not stated"}`, "band_label", "row-band"));
    metric.append(field("span", Number.isFinite(overlap.distance_km) ? `${overlap.distance_km.toFixed(1)} km` : "Distance not stated", "distance_km"));
    metric.append(field("span", `${overlap.a_year ?? "unknown"} / ${overlap.b_year ?? "unknown"}`, "year"));
    button.append(rank, main, metric);
    button.addEventListener("click", () => selectOverlap(overlap, button, byId));
    row.append(button);
    list.append(row);
  }
  document.getElementById("overlap-count").textContent = `${overlaps.length} pairs`;
}

export function selectFirstOverlapForProject(projectId) {
  const overlap = state.overlaps.find((pair) => pair.a === projectId || pair.b === projectId);
  if (!overlap) {
    document.getElementById("status").textContent = "This project has no overlap within 40 km.";
    return;
  }
  const row = Array.from(document.querySelectorAll(".overlap-row")).find((item) => item.dataset.overlapId === overlap.id);
  const button = row?.querySelector("button");
  if (button) selectOverlap(overlap, button, new Map(state.projects.map((feature) => [feature.properties.id, feature])), false);
}

export function restorePairSelection(overlapId) {
  const pair = state.overlaps.find((overlap) => overlap.id === overlapId);
  highlightPair(pair ?? null);
  if (!pair) return false;
  const row = Array.from(document.querySelectorAll(".overlap-row")).find((item) => item.dataset.overlapId === overlapId);
  row?.querySelector("button")?.setAttribute("aria-pressed", "true");
  state.selectedOverlapId = overlapId;
  return true;
}

export function renderUnknownLocations(projects) {
  const unknown = projects.features.filter((feature) => !feature.geometry);
  const details = document.getElementById("unknown-locations");
  details.hidden = unknown.length === 0;
  document.getElementById("unknown-heading").textContent = `Location unknown (${unknown.length})`;
  const list = document.getElementById("unknown-list");
  list.replaceChildren();
  for (const feature of unknown) {
    const item = document.createElement("li");
    item.append(field("span", feature.properties?.name, "name"));
    item.append(document.createTextNode(" / "));
    item.append(field("span", feature.properties?.location_source ?? "Location not stated in source", "location_source"));
    item.append(document.createTextNode(" / "), citation(feature.properties?.source));
    list.append(item);
  }
}
