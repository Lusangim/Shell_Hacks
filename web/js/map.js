import { nearestGeometryMidpoint } from "./nearest-geometry.js";
import { state } from "./state.js";
import { initializeBasemap, isolateMapControls } from "./basemap.js";
import { utilityLabel } from "./project-detail.js";
import { accuracyText, locationLook, swatchFor, utilityToken } from "./look.js";

function token(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

function projectProperties(feature) { return feature.properties || {}; }

function isPoint(feature) { return feature?.geometry?.type === "Point"; }

function voltageWeight(properties) {
  const voltage = Math.max(0, ...(properties.voltage_kv || []).filter(Number.isFinite));
  if (voltage >= 500) return 6;
  if (voltage >= 230) return 4;
  if (voltage >= 115) return 3;
  return 2;
}

function entering(properties) {
  return state.timelineYear != null && properties.year === state.timelineYear;
}

function projectWeight(properties) {
  return voltageWeight(properties) + (entering(properties) ? 2 : 0);
}

// Exact: solid line, filled dot. Approximate: dashed line, hollow ring.
// Town centre only: dotted line, dashed hollow ring. Colour never carries accuracy alone.
function styleForProject(feature, palette = null) {
  const properties = projectProperties(feature);
  const look = locationLook(properties);
  const color = palette?.get(utilityToken(properties)) ?? token(utilityToken(properties));
  if (isPoint(feature)) {
    const hollow = look !== "exact";
    return {
      color, fillColor: color, opacity: 1, fillOpacity: hollow ? 0 : 1, lineCap: "round",
      weight: hollow ? 2.5 + (entering(properties) ? 2 : 0) : projectWeight(properties),
      dashArray: look === "town" ? "3 3" : null,
    };
  }
  if (look === "town") {
    return { color, opacity: 1, fillOpacity: 1, weight: Math.max(3, projectWeight(properties)), dashArray: "1 7", lineCap: "round" };
  }
  return {
    color, opacity: 1, fillOpacity: 1, weight: projectWeight(properties),
    dashArray: look === "approximate" ? "8 5" : null, lineCap: look === "approximate" ? "butt" : "round",
  };
}

function styleForCasing(feature, palette = null) {
  const style = styleForProject(feature, palette);
  const casing = palette?.get("--map-casing") ?? token("--map-casing");
  return {
    color: casing, weight: style.weight + 2, opacity: 1,
    dashArray: isPoint(feature) ? null : style.dashArray, lineCap: style.lineCap,
    fillColor: casing, fillOpacity: 1,
  };
}

function pointRadius(feature) {
  const base = Math.max(5, voltageWeight(projectProperties(feature)) + 2);
  return locationLook(projectProperties(feature)) === "exact" ? base : base + 1;
}

// A short label: the project name (two lines at most, full text kept) and its utility.
// Hovering adds one accuracy line; the pair's persistent labels hide it (see openLabel).
// Citations live in the pair and project details, never on the map.
function tooltipFor(feature) {
  const properties = projectProperties(feature);
  const wrapper = document.createElement("div");
  const title = document.createElement("span");
  title.className = "tooltip-name";
  title.dataset.src = "name";
  title.textContent = properties.name ?? "Name not stated";
  title.title = title.textContent;
  const utility = document.createElement("span");
  utility.className = "tooltip-meta";
  const utilityName = document.createElement("span");
  utilityName.dataset.src = "utility";
  utilityName.textContent = utilityLabel(properties);
  utility.append(swatchFor(properties), utilityName);
  const accuracy = document.createElement("span");
  const town = properties.town_only === true;
  accuracy.className = town ? "tooltip-meta tooltip-accuracy tooltip-town" : "tooltip-meta tooltip-accuracy";
  accuracy.dataset.src = town ? "town_only" : "accuracy";
  accuracy.textContent = accuracyText(properties);
  wrapper.append(title, utility, accuracy);
  return wrapper;
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
  // The selected pair's halo sits above the base map and below every project line.
  map.createPane("haloPane").style.zIndex = 390;
  map.createPane("rankPane").style.zIndex = 620;
  map.getPane("rankPane").style.pointerEvents = "none";
  map.setView([32.75, -81.55], 6);
  state.map = map;
  state.basemapControl = initializeBasemap(map);
  map.on("moveend", updateCityLabels);
  // Labels are placed against the settled view, so re-place them after every fit or pan.
  map.on("moveend", refreshPairLabels);
  let pending = 0;
  window.addEventListener("resize", () => {
    cancelAnimationFrame(pending);
    pending = requestAnimationFrame(refreshPairLabels);
  });
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
    const options = { animate: false, paddingTopLeft: mobile ? [16, 16] : [24, 24],
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
  drawHalo([]);
  drawRankMarker(null, []);
  state.pairLabelLayers = [];
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
      return L.circleMarker(latlng, { radius: pointRadius(feature) + 1, ...styleForCasing(feature), interactive: false });
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
      return L.circleMarker(latlng, { radius: pointRadius(feature), ...styleForProject(feature) });
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
          element.dataset.look = locationLook(feature.properties);
          element.setAttribute("tabindex", "-1");
        }
      });
    },
  }).addTo(map);
  isolateMapControls();
}

export function fitPairBounds(bounds) {
  // The right pane may have just opened and narrowed the map; fit against the size it has now.
  // A hidden map has no size to fit into, so it keeps its view.
  state.map.invalidateSize({ pan: false });
  const size = state.map.getSize();
  if (!size.x || !size.y) return;
  const mobile = matchMedia("(max-width: 700px)").matches;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  // On a wide map, keep room around the pair for its two labels (about 260 by 72 px) above, below or
  // beside it, so the closer zoom never pushes a label under the panel or onto the lines it names.
  const room = !mobile && state.map.getSize().x >= 600 ? [140, 90] : [20, 20];
  // Close enough that the pair's two lines and labels separate, still with the streets around them.
  state.map[reduced ? "fitBounds" : "flyToBounds"](bounds.pad(room[0] > 20 ? 0.05 : 0.2), {
    animate: !reduced,
    duration: 0.6,
    maxZoom: 13,
    paddingTopLeft: room,
    paddingBottomRight: mobile ? [16, Math.min(window.innerHeight * 0.6 + 16, 530)] : room,
  });
}

// A soft accent band under the two selected projects, drawn outside the utility palette.
function projectedGeometry(geometry) {
  if (!geometry) return null;
  const point = (coordinate) => {
    if (!Array.isArray(coordinate) || !Number.isFinite(coordinate[0])
      || !Number.isFinite(coordinate[1])) return null;
    const projected = L.CRS.EPSG3857.project(L.latLng(coordinate[1], coordinate[0]));
    return [projected.x, projected.y];
  };
  if (geometry.type === "Point") return { type: "Point", coordinates: point(geometry.coordinates) };
  if (geometry.type === "LineString") return {
    type: "LineString", coordinates: geometry.coordinates.map(point),
  };
  if (geometry.type === "MultiLineString") return {
    type: "MultiLineString", coordinates: geometry.coordinates.map((line) => line.map(point)),
  };
  return null;
}

function drawRankMarker(overlap, layers) {
  state.pairRankMarker?.remove();
  state.pairRankMarker = null;
  if (!overlap || !Number.isInteger(overlap.rank) || overlap.rank < 1 || layers.length !== 2) return;
  const midpoint = nearestGeometryMidpoint(
    projectedGeometry(layers[0].feature.geometry), projectedGeometry(layers[1].feature.geometry));
  if (!midpoint) return;
  const location = L.CRS.EPSG3857.unproject(L.point(midpoint[0], midpoint[1]));
  const label = document.createElement("span");
  label.textContent = String(overlap.rank);
  label.dataset.src = "rank";
  const icon = L.divIcon({ html: label, className: "pair-rank-marker",
    iconSize: [36, 36], iconAnchor: [18, 18] });
  state.pairRankMarker = L.marker(location, {
    icon, pane: "rankPane", interactive: false, keyboard: false,
  }).addTo(state.map);
  const element = state.pairRankMarker.getElement();
  element.dataset.testid = "pair-rank-marker";
  element.setAttribute("aria-hidden", "true");
}

function drawHalo(layers) {
  if (state.haloLayer) state.haloLayer.remove();
  state.haloLayer = null;
  if (!layers.length || !state.map) return;
  const color = token("--map-halo");
  state.haloLayer = L.geoJSON({ type: "FeatureCollection", features: layers.map((layer) => layer.feature) }, {
    pane: "haloPane",
    interactive: false,
    // GeoJSON styles apply to point markers too, so points get a filled disc and lines a band.
    style: (feature) => (isPoint(feature)
      ? { stroke: false, fill: true, fillColor: color, fillOpacity: 1 }
      : { color, weight: styleForProject(feature).weight + 16, opacity: 1,
        lineCap: "round", lineJoin: "round", dashArray: null, fill: false }),
    pointToLayer: (feature, latlng) => L.circleMarker(latlng, { radius: pointRadius(feature) + 9, stroke: false,
      fillColor: color, fillOpacity: 1, interactive: false, pane: "haloPane" }),
    onEachFeature(_feature, layer) {
      layer.on("add", () => {
        const element = layer.getElement();
        if (!element) return;
        element.dataset.testid = "pair-halo";
        element.classList.add("pair-halo");
        element.setAttribute("aria-hidden", "true");
      });
    },
  }).addTo(state.map);
}

function anchorOf(layer) {
  if (layer.getLatLng) return layer.getLatLng();
  try { return layer.getCenter(); } catch (_error) { return layer.getBounds().getCenter(); }
}

const LABEL_OFFSETS = { left: [-12, 0], right: [12, 0], top: [0, -12], bottom: [0, 12] };

// Screen points along a drawn path, so a label can avoid covering the lines it names.
function pathSamples(layer) {
  const element = layer.getElement?.();
  if (!element || typeof element.getTotalLength !== "function") return [];
  const matrix = element.getScreenCTM();
  const total = element.getTotalLength();
  if (!matrix || !(total > 0)) return [];
  const steps = Math.min(48, Math.max(8, Math.ceil(total / 10)));
  return Array.from({ length: steps + 1 }, (_value, step) => {
    const point = element.getPointAtLength((total * step) / steps);
    return new DOMPoint(point.x, point.y).matrixTransform(matrix);
  });
}

// The part of the map not covered by the panel, or on phones by the sheet and the timeline card.
function visibleMapBounds() {
  const map = state.map.getContainer().getBoundingClientRect();
  const panel = document.querySelector(".panel")?.getBoundingClientRect();
  const bounds = { left: map.left + 8, right: map.right - 8, top: map.top + 8, bottom: map.bottom - 8 };
  if (panel && matchMedia("(max-width: 700px)").matches) {
    const timeline = document.querySelector(".timeline")?.getBoundingClientRect();
    bounds.bottom = Math.min(bounds.bottom, panel.top - 8, timeline?.height ? timeline.top - 8 : Infinity);
  } else if (panel) bounds.left = Math.max(bounds.left, panel.right + 8);
  return bounds;
}

// Candidate anchors: Leaflet's own (a point, or a line's middle), then each end of a line.
function anchorsFor(layer) {
  const anchors = [undefined];
  if (layer.getLatLngs) {
    const vertices = layer.getLatLngs().flat(Infinity);
    if (vertices.length > 1) anchors.push(vertices[0], vertices[vertices.length - 1]);
  }
  return anchors;
}

function openLabel(layer, direction, anchor) {
  const tooltip = layer.getTooltip();
  layer.closeTooltip();
  tooltip.options.direction = direction;
  tooltip.options.offset = L.point(LABEL_OFFSETS[direction]);
  layer.openTooltip(anchor);
  const element = tooltip.getElement();
  element?.classList.add("pair-label");
  return element?.getBoundingClientRect() ?? null;
}

// Open the pair's labels on opposite sides, then keep the best side: clear of the other label,
// fully on the visible map (not under the panel or sheet), covering as little of either
// selected project as possible. Labels never stack on one point or hide their own lines.
function placePairLabels(layers) {
  state.pairLabelLayers = layers;
  if (!layers.length || !state.map) return;
  const bounds = visibleMapBounds();
  const samples = layers.flatMap(pathSamples);
  const area = (rect) => Math.max(0, rect.right - rect.left) * Math.max(0, rect.bottom - rect.top);
  const visible = (rect) => area({ left: Math.max(rect.left, bounds.left), right: Math.min(rect.right, bounds.right),
    top: Math.max(rect.top, bounds.top), bottom: Math.min(rect.bottom, bounds.bottom) }) / Math.max(1, area(rect));
  const covered = (rect) => samples.filter((point) => point.x > rect.left && point.x < rect.right
    && point.y > rect.top && point.y < rect.bottom).length;
  const clash = (a, b) => a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  // Scores compare in order; lower is better: [overlaps the other label, partly hidden, samples covered, -share shown].
  const worse = (a, b) => {
    for (let index = 0; index < a.length; index += 1) if (a[index] !== b[index]) return a[index] > b[index];
    return false;
  };
  const ordered = [...layers].sort((a, b) => anchorOf(a).lng - anchorOf(b).lng);
  const preferences = ordered.length === 2
    ? [["left", "top", "bottom", "right"], ["right", "bottom", "top", "left"]]
    : [["top", "right", "left", "bottom"]];
  const placed = [];
  ordered.forEach((layer, index) => {
    if (!layer.getTooltip() || !layer._map) return;
    const choices = preferences[Math.min(index, preferences.length - 1)];
    let best = null;
    let last = null;
    search: for (const anchor of anchorsFor(layer)) {
      for (const direction of choices) {
        const rect = openLabel(layer, direction, anchor);
        if (!rect) continue;
        last = { direction, anchor };
        const shown = visible(rect);
        const score = [placed.some((other) => clash(rect, other)) ? 1 : 0, shown < 0.999 ? 1 : 0, covered(rect), -shown];
        if (!best || worse(best.score, score)) best = { direction, anchor, rect, score };
        if (score[0] === 0 && score[1] === 0 && score[2] === 0) break search;
      }
    }
    if (!best) return;
    const same = last && last.direction === best.direction && last.anchor === best.anchor;
    const rect = same ? best.rect : openLabel(layer, best.direction, best.anchor);
    if (rect) placed.push(rect);
  });
}

// The sheet or the window can change the visible map without moving it.
export function refreshPairLabels() {
  if (state.pairLabelLayers.length) placePairLabels(state.pairLabelLayers);
}

function resetLabel(layer) {
  layer.closeTooltip();
  const tooltip = layer.getTooltip();
  if (tooltip) {
    tooltip.options.direction = "top";
    tooltip.options.offset = L.point(0, 0);
    tooltip.getElement()?.classList.remove("pair-label");
  }
}

// While a pair is selected its two lines grow and every other line gets one step thinner, never
// fainter, so the pair reads first and the rest keeps its contrast. Dotted lines keep dots of 3 px.
function pairWeight(style, isSelected, pairOpen) {
  if (isSelected) return style.weight + 4;
  if (!pairOpen) return style.weight;
  return Math.max(style.dashArray === "1 7" ? 3 : 2, style.weight - 1);
}

export function highlightPair(overlap, { preserveLabels = false } = {}) {
  if (!state.projectLayers) { drawRankMarker(null, []); return; }
  // Read theme colours before changing SVG styles, avoiding one style flush per project.
  const names = new Set(state.projects.map((feature) => utilityToken(feature.properties)));
  names.add("--map-casing");
  const computed = getComputedStyle(document.documentElement);
  const palette = new Map([...names].map((name) => [name, computed.getPropertyValue(name).trim()]));
  const selectedIds = new Set(overlap ? [overlap.a, overlap.b] : []);
  const pairOpen = selectedIds.size > 0;
  const selected = [];
  state.projectLayers.eachLayer((layer) => {
    const isSelected = selectedIds.has(layer.feature?.properties?.id);
    const style = styleForProject(layer.feature, palette);
    layer.setStyle({ ...style, weight: pairWeight(style, isSelected, pairOpen) });
    const element = layer.getElement();
    if (element) element.dataset.selected = String(isSelected);
    if (isSelected) { layer.bringToFront(); selected.push(layer); }
    else resetLabel(layer);
  });
  state.casingLayers?.eachLayer((layer) => {
    const isSelected = selectedIds.has(layer.feature?.properties?.id);
    const style = styleForCasing(layer.feature, palette);
    // The casing stays 2 px wider than its line. A selected dashed line sits on a continuous casing,
    // so the halo never shows through the gaps.
    layer.setStyle({ ...style, weight: pairWeight(styleForProject(layer.feature, palette), isSelected, pairOpen) + 2,
      dashArray: isSelected ? null : style.dashArray });
    if (isSelected) layer.bringToFront();
  });
  selected.forEach((layer) => layer.bringToFront());
  drawHalo(selected);
  drawRankMarker(overlap, selected);
  // A year/theme refresh changes styles, not label geometry. Movement and sheet
  // changes reposition labels separately; new project layers always need placement.
  if (!preserveLabels || selected.length !== state.pairLabelLayers.length
      || selected.some((layer) => !state.pairLabelLayers.includes(layer))) {
    placePairLabels(selected);
  }
}

export function refreshMapTheme() {
  state.basemapControl?.refreshTheme();
  if (state.basemapLayers) state.basemapLayers.setStyle(styleForBasemap);
  if (state.casingLayers) state.casingLayers.setStyle(styleForCasing);
  refreshProjectStyles();
}

export function refreshProjectStyles() {
  if (state.projectLayers) {
    highlightPair(state.overlaps.find((overlap) => overlap.id === state.selectedOverlapId), { preserveLabels: true });
  }
}
