import { state } from "./state.js";
import { createStormController } from "./storm.js";

const BAND_LABELS = { touching: "Touching / crossing", lt_1_6km: "Under 1.6 km", lt_8km: "Under 8 km", lt_40km: "Under 40 km" };

function token(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function text(tag, value, source) {
  const element = document.createElement(tag);
  element.textContent = value;
  if (source) element.dataset.src = source;
  return element;
}

function renderCounts(id, counts, labels = {}) {
  const target = document.getElementById(id);
  target.replaceChildren();
  for (const [key, count] of Object.entries(counts)) {
    const row = document.createElement("div");
    row.dataset.countKey = key;
    row.append(text("dt", labels[key] ?? key, "count_label"), text("dd", count, "count"));
    target.append(row);
  }
}

function renderRecords(payload) {
  const projects = document.getElementById("area-projects");
  projects.replaceChildren();
  for (const feature of payload.projects) {
    const project = feature.properties;
    const row = document.createElement("li");
    row.append(text("strong", project.name, "name"), text("p", project.utility, "utility"),
      text("p", `${project.accuracy} location`, "accuracy"),
      text("p", `${project.source.doc}, p. ${project.source.page}`, "source"));
    projects.append(row);
  }
  const overlaps = document.getElementById("area-overlaps");
  overlaps.replaceChildren();
  for (const pair of payload.overlaps) {
    const row = document.createElement("li");
    const link = text("a", `#${pair.rank}: ${pair.band_label}, ${pair.distance_km.toLocaleString()} km`, "overlap");
    link.href = `#overlap=${encodeURIComponent(pair.id)}`;
    row.append(link);
    overlaps.append(row);
  }
}

export function createAreaController(map, announce, setAreaURL) {
  const output = document.getElementById("area-selection");
  const panel = document.getElementById("area-panel");
  const message = document.getElementById("area-state");
  const results = document.getElementById("area-results");
  const retry = document.getElementById("area-retry");
  const radiusInput = document.getElementById("area-radius");
  let circle = null;
  let marker = null;
  let selected = null;
  let entry = document.getElementById("search-input");
  let requestNumber = 0;
  let controller = null;
  let areaMode = false;
  const storm = createStormController(map, () => selected);
  // On phones the year slider sits under the top-right controls, so the button uses the free top-left corner.
  const phoneLayout = matchMedia("(max-width: 700px)");
  const areaControl = L.control({ position: phoneLayout.matches ? "topleft" : "topright" });
  phoneLayout.addEventListener?.("change", (event) => areaControl.setPosition(event.matches ? "topleft" : "topright"));
  areaControl.onAdd = () => {
    const container = L.DomUtil.create("div", "leaflet-control-area");
    const button = L.DomUtil.create("button", "", container);
    button.id = "area-mode-toggle";
    button.type = "button";
    button.textContent = "Explore an area";
    button.title = "Choose the centre of a 40 km area on the map";
    button.setAttribute("aria-pressed", "false");
    L.DomEvent.disableClickPropagation(container);
    L.DomEvent.disableScrollPropagation(container);
    return container;
  };
  areaControl.addTo(map);
  const areaModeButton = document.getElementById("area-mode-toggle");

  function setAreaMode(active, announceChange = true) {
    areaMode = active;
    areaModeButton.setAttribute("aria-pressed", String(active));
    map.getContainer().classList.toggle("area-mode-active", active);
    if (announceChange) announce(active
      ? "Click the map to choose the centre of a 40 km area. Esc cancels."
      : "Area selection cancelled.");
  }

  areaModeButton.addEventListener("click", () => setAreaMode(!areaMode));

  function removeLayers() {
    if (circle) map.removeLayer(circle);
    if (marker) map.removeLayer(marker);
    circle = marker = null;
  }

  function clear({ write = true, focus = false } = {}) {
    const hadArea = selected !== null;
    ++requestNumber;
    controller?.abort();
    storm.clear();
    selected = null;
    removeLayers();
    output.hidden = panel.hidden = true;
    output.replaceChildren();
    if (write && hadArea) setAreaURL(null);
    if (focus) {
      (entry.isConnected && !entry.hidden ? entry : document.getElementById("search-input")).focus();
      announce("Area cleared.");
    }
  }

  function draw() {
    removeLayers();
    const { lat, lon, radius, label } = selected;
    circle = L.circle([lat, lon], { radius: radius * 1000, color: token("--ink"), weight: 2,
      dashArray: "8 5", fillColor: token("--map-state"), fillOpacity: 0.08, interactive: false }).addTo(map);
    marker = L.circleMarker([lat, lon], { radius: 5, color: token("--ink"), weight: 2,
      fillColor: token("--panel"), fillOpacity: 1, interactive: false }).addTo(map);
    for (const [layer, testid] of [[circle, "area-circle"], [marker, "area-center"]]) {
      const path = layer.getElement();
      path.dataset.testid = testid;
      path.setAttribute("aria-hidden", "true");
      path.setAttribute("tabindex", "-1");
    }
    circle.getElement().dataset.radiusM = String(radius * 1000);
    output.replaceChildren(document.createTextNode(`${radius} km around `), text("span", label ?? `${lat.toFixed(5)}, ${lon.toFixed(5)}`, "label"));
    document.getElementById("area-center-label").textContent = `Centre: ${lat.toFixed(5)}, ${lon.toFixed(5)}`;
    radiusInput.value = String(radius);
    radiusInput.setAttribute("aria-valuetext", `${radius} km`);
    document.getElementById("area-radius-output").textContent = `${radius} km`;
    output.hidden = panel.hidden = false;
  }

  async function load() {
    const ownRequest = ++requestNumber;
    controller?.abort();
    controller = new AbortController();
    const { lat, lon, radius } = selected;
    results.hidden = true;
    retry.hidden = true;
    message.textContent = "Loading projects and overlaps in this area.";
    try {
      const params = new URLSearchParams({ lat, lon, radius_km: radius });
      const response = await fetch(`/api/area?${params}`, { signal: controller.signal });
      if (!response.ok) throw new Error("Area request failed");
      const payload = await response.json();
      if (ownRequest !== requestNumber) return;
      if (!Array.isArray(payload.projects) || !Array.isArray(payload.overlaps)
        || !payload.counts_by_utility || !payload.counts_by_band) throw new Error("Invalid area response");
      renderCounts("area-utilities", payload.counts_by_utility, Object.create(null));
      renderCounts("area-bands", payload.counts_by_band, BAND_LABELS);
      renderRecords(payload);
      message.textContent = `${payload.projects.length} projects in area; ${payload.overlaps.length} overlaps with at least one project in area.`;
      results.hidden = false;
    } catch (error) {
      if (ownRequest !== requestNumber || error.name === "AbortError") return;
      message.textContent = "Could not load this area. Check the local server, adjust the radius or select another centre, then retry.";
      retry.hidden = false;
    }
  }

  function explore(result, { entry: origin = document.getElementById("map"), radius = 40, write = true } = {}) {
    storm.clear();
    selected = { lat: result.lat, lon: result.lon, label: result.label, radius };
    entry = origin;
    draw();
    announce(`${radius} km area selected.`);
    if (write) setAreaURL(selected, radius);
    const sheet = document.getElementById("sheet-toggle");
    if (matchMedia("(max-width: 700px)").matches && sheet.getAttribute("aria-expanded") === "false") {
      document.querySelector(".panel").classList.add("expanded");
      sheet.setAttribute("aria-expanded", "true");
      sheet.textContent = "Collapse opportunities";
    }
    panel.scrollIntoView({ block: "nearest" });
    void load();
  }

  function restore() {
    const params = new URLSearchParams(location.search);
    const raw = params.get("area");
    if (!raw) { clear({ write: false }); return; }
    const parts = raw.split(",");
    const [lat, lon] = parts.map(Number);
    const radius = Number(params.get("radius_km") ?? 40);
    if (parts.length !== 2 || parts.some((part) => !/^-?\d+(?:\.\d+)?$/.test(part))
      || Math.abs(lat) > 90 || Math.abs(lon) > 180 || !Number.isFinite(radius) || radius < 1 || radius > 80) {
      clear({ write: false });
      return;
    }
    if (selected?.lat === lat && selected?.lon === lon && selected?.radius === radius) return;
    state.initialMapFitted = true;
    map.setView([lat, lon], 9, { animate: false });
    explore({ lat, lon }, { radius, write: false, entry: document.getElementById("search-input") });
  }

  map.on("click", (event) => {
    if (!areaMode || event.originalEvent?.target.closest(".leaflet-interactive")) return;
    setAreaMode(false, false);
    explore({ lat: event.latlng.lat, lon: event.latlng.lng });
  });
  radiusInput.addEventListener("input", () => {
    if (selected) explore(selected, { entry, radius: Number(radiusInput.value) });
  });
  retry.addEventListener("click", () => { if (selected) void load(); });
  document.getElementById("area-clear").addEventListener("click", () => clear({ focus: true }));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && areaMode) {
      event.preventDefault();
      setAreaMode(false);
      return;
    }
    if (event.key === "Escape" && selected && !event.target.closest(".tour-card")) {
      event.preventDefault();
      clear({ focus: true });
    }
  });
  window.addEventListener("popstate", restore);
  restore();

  function refreshTheme() {
    circle?.setStyle({ color: token("--ink"), fillColor: token("--map-state") });
    marker?.setStyle({ color: token("--ink"), fillColor: token("--panel") });
    storm.refreshTheme();
  }

  return { clear, explore, refreshTheme };
}
