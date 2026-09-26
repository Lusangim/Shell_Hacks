import { state } from "./state.js";

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
    weight: voltageWeight(properties),
    dashArray: properties.accuracy === "approximate" ? "8 5" : null,
    opacity: 1,
    fillOpacity: 1,
  };
}

function styleForCasing(feature) {
  const properties = projectProperties(feature);
  return {
    color: token("--canvas"),
    weight: voltageWeight(properties) + 2,
    dashArray: properties.accuracy === "approximate" ? "8 5" : null,
    opacity: 1,
    fillColor: token("--canvas"),
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
  const map = L.map("map", { zoomControl: false, preferCanvas: false, renderer: L.svg(), scrollWheelZoom: false });
  L.control.zoom({ position: "topright" }).addTo(map);
  map.setView([32.75, -81.55], 8);
  state.map = map;
  map.on("moveend", updateCityLabels);
  return map;
}

export function renderMap(projects, basemap) {
  const map = state.map;
  if (state.basemapLayers) state.basemapLayers.clearLayers();
  if (state.casingLayers) state.casingLayers.clearLayers();
  if (state.projectLayers) state.projectLayers.clearLayers();
  state.cityMarkers = [];
  state.basemapLayers = L.geoJSON(basemap, {
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
}

export function fitPairBounds(bounds) {
  const mobile = matchMedia("(max-width: 700px)").matches;
  state.map.fitBounds(bounds.pad(0.2), {
    animate: !matchMedia("(prefers-reduced-motion: reduce)").matches,
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
    if (selected) layer.bringToFront();
  });
}

export function refreshMapTheme() {
  if (state.basemapLayers) state.basemapLayers.setStyle(styleForBasemap);
  if (state.casingLayers) state.casingLayers.setStyle(styleForCasing);
  if (state.projectLayers) {
    state.projectLayers.setStyle(styleForProject);
    highlightPair(state.overlaps.find((overlap) => overlap.id === state.selectedOverlapId));
  }
}
