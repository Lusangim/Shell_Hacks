import { state } from "./state.js";
import { fitPairBounds, highlightPair } from "./map.js";
import { citation, projectAbsenceMessage, utilityLabel } from "./project-detail.js";
import { bandGlyph, coordinateTag, swatchFor } from "./look.js";

function field(tag, value, source, className = "") {
  const element = document.createElement(tag);
  if (source) element.dataset.src = source;
  if (className) element.className = className;
  element.textContent = value ?? "not stated";
  return element;
}

function separator(text, className = "sep") {
  const element = document.createElement("span");
  element.className = className;
  element.textContent = text;
  return element;
}

// One line per project: its line sample, utility and verbatim name. A long name is cut with an
// ellipsis on screen only; the full text stays in the row, its accessible name and the title.
function projectLine(project) {
  const line = document.createElement("span");
  line.className = "row-project";
  const name = field("span", project?.properties?.name, "name", "row-name");
  name.title = name.textContent;
  line.append(swatchFor(project?.properties), field("span", utilityLabel(project?.properties), "utility", "row-utility"),
    separator(": "), name);
  return line;
}

// A short location marker beside the numbers; the pair detail explains it in full.
function accuracyMarker(overlap, a, b) {
  const town = a?.properties?.town_only === true || b?.properties?.town_only === true;
  const text = town ? "Town-level" : { approximate: "Approx.", exact: "Exact" }[overlap.accuracy_pair] ?? "Unknown";
  return field("span", text, town ? "town_only" : "accuracy", "row-accuracy");
}

function overlapProjects(overlap, byId) {
  return [byId.get(overlap.a), byId.get(overlap.b)];
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
  status.textContent = `Selected overlap ${overlap.rank}: ${utilityLabel(a?.properties)} and ${utilityLabel(b?.properties)}.`;
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
    // Then the numbers: how close and how sure, then when. Each group wraps as a unit.
    const metric = document.createElement("span");
    metric.className = "row-metric";
    const place = document.createElement("span");
    place.className = "metric-group metric-place";
    // The chip's text sits in its own span so the phone peek can show just the glyph and distance.
    const band = field("span", "", "band_label", "row-band");
    band.replaceChildren(bandGlyph(overlap.band), field("span", overlap.band_label ?? "Distance not stated", "", "band-text"));
    // Spaces between the flex items are not drawn, but keep the row's spoken name readable.
    place.append(band, " ",
      field("span", Number.isFinite(overlap.distance_km) ? `${overlap.distance_km.toFixed(1)} km` : "Distance not stated", "distance_km"),
      " ", accuracyMarker(overlap, a, b));
    const time = document.createElement("span");
    time.className = "metric-group metric-time";
    time.append(field("span", `${overlap.a_year ?? "unknown"} / ${overlap.b_year ?? "unknown"}`, "year"));
    const coordinate = coordinateTag(overlap.a_year, overlap.b_year);
    if (coordinate) time.append(" ", coordinate);
    metric.append(place, " ", time);
    if (overlap.town_capped === true) metric.append(" ", field("span", "Counted as under 40 km", "town_capped", "row-flag"));
    main.append(projectLine(a), " ", projectLine(b), " ", metric);
    button.append(rank, " ", main);
    button.addEventListener("click", () => selectOverlap(overlap, button, byId));
    row.append(button);
    list.append(row);
  }
  document.getElementById("overlap-count").textContent = `${overlaps.length} pairs`;
  document.dispatchEvent(new Event("gridlock:list-rendered"));
}

export function selectFirstOverlapForProject(projectId, hasFilters = false) {
  const overlap = state.overlaps.find((pair) => pair.a === projectId || pair.b === projectId);
  if (!overlap) {
    const feature = state.projects.find((project) => project.properties.id === projectId);
    state.selectedOverlapId = null;
    highlightPair(null);
    document.querySelectorAll(".overlap-button[aria-pressed]").forEach((button) => button.setAttribute("aria-pressed", "false"));
    document.getElementById("map-pair-open").hidden = true;
    document.getElementById("status").textContent = projectAbsenceMessage(feature, hasFilters);
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
