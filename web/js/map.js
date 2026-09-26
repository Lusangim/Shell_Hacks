import { state } from "./state.js";
import { initializeBasemap, isolateMapControls } from "./basemap.js";

const utilityTokens = new Map([
  ["Dominion Energy SC", "--dominion"],
  ["Georgia Power", "--georgia-power"],
  ["MEAG Power", "--meag-power"],
  ["Georgia Transmission Corp.", "--gtc"],
  ["Dalton Utilities", "--minor"],
  ["Georgia ITS (joint)", "--minor"],
]);

function token(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

function projectProperties(feature) { return feature.properties || {}; }

function voltageWeight(properties) {
  const voltage = Math.max(0, ...(properties.voltage_kv || []).filter(Number.isFinite));
  if (voltage >= 500) return 6;
  if (voltage >= 230) return 4;
  if (voltage >= 115) return 3;
  return 2;
}

function projectWeight(properties) {
  const entering = state.timelineYear != null && properties.year === state.timelineYear;
  return voltageWeight(properties) + (entering ? 2 : 0);
}

function tooltipFor(feature) {
  const properties = projectProperties(feature);
  const wrapper = document.createElement("div");
  const title = document.createElement("span");
  title.className = "tooltip-name";
  title.dataset.src = "name";
  title.textContent = properties.name ?? "Name not stated";
  const meta = document.createElement("span");
  meta.className = "tooltip-meta";
  meta.dataset.src = "utility";
  meta.textContent = properties.utility ?? "Utility not stated";
  const accuracy = document.createElement("span");
  accuracy.className = "tooltip-meta";
  accuracy.dataset.src = "accuracy";
  accuracy.textContent = `${properties.accuracy ?? "unknown"} location`;
  const source = document.createElement("span");
  source.className = "tooltip-meta";
  source.dataset.src = "source";
  source.textContent = properties.source?.doc && properties.source?.page
    ? `${properties.source.doc}, p. ${properties.source.page}`
    : "Source page not stated";
  wrapper.append(title, meta, accuracy, source);
  return wrapper;
}

function styleForProject(feature) {
  const properties = projectProperties(feature);
  return {
    color: token(utilityTokens.get(properties.utility) || "--minor"),
    weight: projectWeight(properties),
    dashArray: properties.accuracy === "approximate" ? "8 5" : null,
    opacity: 1,
    fillOpacity: 1,
  };
}

function styleForCasing(feature) {
  const properties = projectProperties(feature);
  return {
    color: token("--map-casing"),
    weight: projectWeight(properties) + 2,
    dashArray: properties.accuracy === "approximate" ? "8 5" : null,
    opacity: 1,
    fillColor: token("--map-casing"),
    fillOpacity: 1,
  };
}

function styleForBasemap(feature) {
  const kind = feature.properties?.kind;
  return {
    color: token(kind === "county" ? "--map-county" : "--map-state"),
    weight: kind === "county" ? 1 : 2,
    dashArray: kind === "state" ? "10 5 2 5" : null,
    fillColor: token("--map-land"),
    fillOpacity: kind === "county" ? 0 : 1,
  };
}

function cityMarker(feature, latlng) {
  const label = document.createElement("span");
  label.dataset.src = "name";
  label.dataset.testid = "city-label";
  label.textContent = feature.properties?.name ?? "";
  label.setAttribute("aria-hidden", "true");
  const icon = L.divIcon({ html: label, className: "city-label-icon", iconSize: [1, 1], iconAnchor: [0, 10] });
  return L.marker(latlng, { icon, interactive: false, keyboard: false });
}

function cityPriority(feature) {
  const name = feature.properties?.name;
  if (name === "Savannah city") return 0;
  if (name === "North Augusta city") return 1;
  return 2;
}

function updateCityLabels() {
  const map = state.map;
  const size = map.getSize();
  const limit = map.getZoom() < 9 ? 14 : map.getZoom() < 11 ? 32 : 80;
  const occupied = [];
  let shown = 0;
  const center = map.getCenter();
  const candidates = [...state.cityMarkers].sort((a, b) =>
    cityPriority(a.feature) - cityPriority(b.feature)
    || a.layer.getLatLng().distanceTo(center) - b.layer.getLatLng().distanceTo(center)
    || (a.feature.properties?.name ?? "").localeCompare(b.feature.properties?.name ?? "")
  );
  for (const { feature, layer } of candidates) {
    const icon = layer.getElement();
    if (!icon) continue;
    icon.classList.remove("city-label-visible");
    if (shown >= limit) continue;
    const point = map.latLngToContainerPoint(layer.getLatLng());
    const name = feature.properties?.name ?? "";
    const width = Math.max(60, name.length * 7 + 12);
    const box = { left: point.x + 5, right: point.x + width + 5, top: point.y - 10, bottom: point.y + 10 };
    if (!name || box.left < 8 || box.right > size.x - 8 || box.top < 8 || box.bottom > size.y - 8) continue;
    if (occupied.some((used) => box.left < used.right + 8 && box.right + 8 > used.left
      && box.top < used.bottom + 8 && box.bottom + 8 > used.top)) continue;
    icon.classList.add("city-label-visible");
    occupied.push(box);
    shown += 1;
  }
}

export function initializeMap() {
  const map = L.map("map", { zoomControl: false, preferCanvas: false, renderer: L.svg(),
    scrollWheelZoom: true, minZoom: 6, maxZoom: 17, zoomSnap: 0.25 });
  L.control.zoom({ position: "topright" }).addTo(map);
  map.createPane("outlinePane").style.zIndex = 210;
  map.setView([32.75, -81.55], 6);
  state.map = map;
  state.basemapControl = initializeBasemap(map);
  map.on("moveend", updateCityLabels);
  return map;
}

function labelAndFitStates(basemap) {
  const states = (basemap.features || []).filter((feature) => ["state", "state_outline"].includes(feature.properties?.kind));
  if (state.stateLabels) state.stateLabels.clearLayers();
  state.stateLabels = L.layerGroup().addTo(state.map);
  for (const feature of states) {
    const label = document.createElement("span");
    label.textContent = feature.properties.name;
    label.dataset.src = "name";
    label.dataset.testid = "state-label";
    const bounds = L.geoJSON(feature).getBounds();
    L.marker(bounds.getCenter(), { interactive: false, keyboard: false,
      icon: L.divIcon({ html: label, className: "state-label", iconSize: [130, 24], iconAnchor: [65, 12] }),
    }).addTo(state.stateLabels);
  }
  if (!state.initialMapFitted && states.length) {
    const mobile = matchMedia("(max-width: 700px)").matches;
    const timeline = document.querySelector(".timeline").getBoundingClientRect();
    const bottom = mobile ? innerHeight - timeline.top + 12 : 140;
    const bounds = L.geoJSON({ type: "FeatureCollection", features: states }).getBounds();
    const options = { animate: false, paddingTopLeft: mobile ? [16, 16] : [456, 24],
      paddingBottomRight: [24, bottom] };
    // Small screens may need a slightly wider overview to keep both states above the sheet.
    if (mobile) state.map.setMinZoom(0);
    const available = state.map.getBoundsZoom(bounds, false, L.point(options.paddingTopLeft).add(options.paddingBottomRight));
    if (mobile) state.map.setMinZoom(Math.min(6, available));
    state.map.fitBounds(bounds, options);
    state.initialMapFitted = true;
  }
}

export function renderMap(projects, basemap) {
  const map = state.map;
  if (state.basemapLayers) state.basemapLayers.clearLayers();
  if (state.casingLayers) state.casingLayers.clearLayers();
  if (state.projectLayers) state.projectLayers.clearLayers();
  state.cityMarkers = [];
  state.basemapLayers = L.geoJSON(basemap, {
    pane: "outlinePane",
    style: styleForBasemap,
    interactive: false,
    pointToLayer: cityMarker,
    onEachFeature(feature, layer) {
      if (feature.geometry?.type === "Point") state.cityMarkers.push({ feature, layer });
      layer.on("add", () => {
        const element = layer.getElement();
        if (element) {
          element.dataset.testid = "basemap-feature";
          if (feature.geometry?.type === "Point") element.setAttribute("aria-hidden", "true");
        }
      });
    },
  }).addTo(map);
  labelAndFitStates(basemap);
  updateCityLabels();
  state.casingLayers = L.geoJSON(projects, {
    renderer: L.svg(),
    style: styleForCasing,
    interactive: false,
    pointToLayer(feature, latlng) {
      return L.circleMarker(latlng, { radius: Math.max(5, voltageWeight(projectProperties(feature)) + 2) + 1, ...styleForCasing(feature), interactive: false });
    },
    onEachFeature(_feature, layer) {
      layer.on("add", () => {
        const element = layer.getElement();
        if (element) element.dataset.testid = "project-casing";
      });
    },
  }).addTo(map);
  state.projectLayers = L.geoJSON(projects, {
    renderer: L.svg(),
    style: styleForProject,
    pointToLayer(feature, latlng) {
      return L.circleMarker(latlng, { radius: Math.max(5, voltageWeight(projectProperties(feature)) + 2), ...styleForProject(feature) });
    },
    onEachFeature(feature, layer) {
      layer.bindTooltip(tooltipFor(feature), { direction: "top", opacity: 1 });
      layer.on("click", () => document.dispatchEvent(new CustomEvent("gridlock:project-click", {
        detail: { projectId: feature.properties.id },
      })));
      layer.on("add", () => {
        const element = layer.getElement();
        if (element) {
          element.dataset.testid = "project-feature";
          element.dataset.projectId = feature.properties.id;
          element.setAttribute("tabindex", "-1");
        }
      });
    },
  }).addTo(map);
  isolateMapControls();
}

export function fitPairBounds(bounds) {
  const mobile = matchMedia("(max-width: 700px)").matches;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  state.map[reduced ? "fitBounds" : "flyToBounds"](bounds.pad(0.2), {
    animate: !reduced,
    duration: 0.6,
    maxZoom: 11,
    paddingTopLeft: mobile ? [16, 16] : [440, 20],
    paddingBottomRight: mobile ? [16, Math.min(window.innerHeight * 0.6 + 16, 530)] : [20, 20],
  });
}

export function highlightPair(overlap) {
  if (!state.projectLayers) return;
  const selectedIds = new Set(overlap ? [overlap.a, overlap.b] : []);
  state.projectLayers.eachLayer((layer) => {
    const selected = selectedIds.has(layer.feature?.properties?.id);
    const style = styleForProject(layer.feature);
    layer.setStyle({ ...style, weight: style.weight + (selected ? 2 : 0) });
    const element = layer.getElement();
    if (element) element.dataset.selected = String(selected);
    if (selected) { layer.bringToFront(); layer.openTooltip(); }
    else layer.closeTooltip();
  });
  state.casingLayers?.eachLayer((layer) => {
    const selected = selectedIds.has(layer.feature?.properties?.id);
    const style = styleForCasing(layer.feature);
    layer.setStyle({ ...style, weight: style.weight + (selected ? 2 : 0) });
  });
}

export function refreshMapTheme() {
  state.basemapControl?.refreshTheme();
  if (state.basemapLayers) state.basemapLayers.setStyle(styleForBasemap);
  if (state.casingLayers) state.casingLayers.setStyle(styleForCasing);
  refreshProjectStyles();
}

export function refreshProjectStyles() {
  if (state.projectLayers) {
    state.projectLayers.setStyle(styleForProject);
    highlightPair(state.overlaps.find((overlap) => overlap.id === state.selectedOverlapId));
  }
}
