const ACTIONS = {
  human_review: "Review the estimate",
  coordinate_project_timing: "Coordinate project timing",
  inspect_asset: "Inspect exposed asset",
  preposition_crews: "Preposition crews",
  verify_source: "Verify source data",
};

const DAMAGE = {
  none: { token: "--storm-none", weight: 2, dashArray: "2 5" },
  minor: { token: "--storm-minor", weight: 2, dashArray: "5 5" },
  moderate: { token: "--storm-moderate", weight: 3, dashArray: null },
  severe: { token: "--storm-severe", weight: 4, dashArray: "8 4" },
  failed: { token: "--storm-failed", weight: 5, dashArray: null },
};

const dollars = (value) => value == null ? "no cost basis" : `$${Number(value).toLocaleString("en-US")}`;
const percent = (value) => `${Math.round(Number(value) * 100)}%`;
const cssToken = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

function node(tag, value, source) {
  const result = document.createElement(tag);
  result.textContent = String(value);
  if (source) result.dataset.src = source;
  return result;
}

function damageClass(asset) {
  const { minor, moderate, severe, failed } = asset.damage;
  const chances = {
    none: Math.max(0, 1 - minor),
    minor: Math.max(0, minor - moderate),
    moderate: Math.max(0, moderate - severe),
    severe: Math.max(0, severe - failed),
    failed,
  };
  return Object.entries(chances).sort((a, b) => b[1] - a[1])[0][0];
}

function mark(layer, testid) {
  const element = layer.getElement();
  if (!element) return;
  element.dataset.testid = testid;
  element.setAttribute("aria-hidden", "true");
  element.setAttribute("tabindex", "-1");
}

function coordinates(asset) {
  const geometry = asset.geometry;
  if (geometry?.type === "Point") return [geometry.coordinates[1], geometry.coordinates[0]];
  if (geometry?.type === "LineString") return geometry.coordinates.map(([lon, lat]) => [lat, lon]);
  return null;
}

export function createStormController(map, currentArea) {
  const button = document.getElementById("storm-estimate");
  const status = document.getElementById("storm-status");
  const results = document.getElementById("storm-results");
  const frameInput = document.getElementById("storm-frame");
  const frameLabel = document.getElementById("storm-frame-label");
  const playButton = document.getElementById("storm-play");
  const resetButton = document.getElementById("storm-reset");
  let data = null;
  let layers = [];
  let frameDots = [];
  let radiusLayer = null;
  let timer = null;
  let controller = null;
  let requestId = 0;

  function pause() {
    if (timer != null) window.clearInterval(timer);
    timer = null;
    playButton.textContent = "Play storm";
  }

  function removeLayers() {
    for (const layer of layers) map.removeLayer(layer);
    layers = [];
    frameDots = [];
    radiusLayer = null;
  }

  function clear() {
    requestId += 1;
    controller?.abort();
    controller = null;
    pause();
    removeLayers();
    data = null;
    frameInput.value = "0";
    frameLabel.textContent = "";
    status.textContent = "";
    results.hidden = true;
    button.disabled = false;
  }

  function frame(index) {
    if (!data) return;
    const selected = data.scenario.frames[index];
    frameInput.value = String(index);
    frameInput.setAttribute("aria-valuetext", `${selected.t_hours} hours from landfall`);
    frameLabel.textContent = `${selected.t_hours} h from landfall; Rmax ${selected.rmax_km} km`;
    frameLabel.dataset.src = "scenario.frames";
    radiusLayer.setLatLng([selected.lat, selected.lon]);
    radiusLayer.setRadius(selected.rmax_km * 1000);
    frameDots.forEach((dot, dotIndex) => dot.setStyle({ fillOpacity: dotIndex === index ? 1 : 0.3,
      weight: dotIndex === index ? 3 : 1 }));
  }

  function play() {
    if (timer != null) { pause(); return; }
    if (Number(frameInput.value) >= data.scenario.frames.length - 1) frame(0);
    playButton.textContent = "Pause storm";
    timer = window.setInterval(() => {
      const next = Number(frameInput.value) + 1;
      if (next >= data.scenario.frames.length) { pause(); return; }
      frame(next);
    }, 300);
  }

  function draw() {
    const frames = data.scenario.frames;
    const track = L.polyline(frames.map((point) => [point.lat, point.lon]), {
      color: cssToken("--storm-track"), weight: 3, dashArray: "8 6", interactive: false,
    }).addTo(map);
    layers.push(track);
    mark(track, "storm-track");
    for (const point of frames) {
      const dot = L.circleMarker([point.lat, point.lon], { radius: 4, color: cssToken("--storm-track"),
        fillColor: cssToken("--panel"), fillOpacity: 0.3, weight: 1, interactive: false }).addTo(map);
      layers.push(dot);
      frameDots.push(dot);
      mark(dot, "storm-frame-dot");
    }
    radiusLayer = L.circle([frames[0].lat, frames[0].lon], { radius: frames[0].rmax_km * 1000,
      color: cssToken("--storm-track"), weight: 2, dashArray: "4 4",
      fillColor: cssToken("--storm-track"), fillOpacity: 0.06, interactive: false }).addTo(map);
    layers.push(radiusLayer);
    mark(radiusLayer, "storm-rmax");
    for (const asset of data.assets) {
      const location = coordinates(asset);
      if (!location) continue;
      const style = DAMAGE[damageClass(asset)];
      const color = cssToken(style.token);
      const layer = asset.geometry.type === "Point"
        ? L.circleMarker(location, { radius: 5, color, fillColor: color, fillOpacity: 0.8,
          weight: style.weight, interactive: false })
        : L.polyline(location, { color, weight: style.weight, dashArray: style.dashArray,
          interactive: false });
      layer.addTo(map);
      layers.push(layer);
      mark(layer, "storm-asset");
    }
    const { lat, lon } = data.area;
    const nearest = frames.reduce((best, point, index) => {
      const distance = (point.lat - lat) ** 2 + ((point.lon - lon) * Math.cos(lat * Math.PI / 180)) ** 2;
      return distance < best.distance ? { index, distance } : best;
    }, { index: 0, distance: Infinity });
    frame(nearest.index);
  }

  function renderCost() {
    const summary = data.summary;
    const cost = document.getElementById("storm-cost");
    cost.replaceChildren(document.createTextNode("Possible repair cost (estimate): "),
      node("strong", `${dollars(summary.p10_usd)} to ${dollars(summary.p90_usd)}, median ${dollars(summary.p50_usd)}`, "summary"));
    document.getElementById("storm-coverage").textContent =
      `${summary.assets_exact} of ${summary.assets_total} assets located exactly; costs available for ${percent(summary.coverage_share)}.`;
    document.getElementById("storm-coverage").dataset.src = "summary";
    document.getElementById("storm-assumptions").replaceChildren(...summary.top_assumptions.slice(0, 3)
      .map((assumption) => node("li", assumption, "summary.top_assumptions")));
  }

  function renderDecision() {
    const target = document.getElementById("storm-decision");
    const decision = data.decision;
    const title = node("p", ACTIONS[decision.action] ?? decision.action);
    title.className = "storm-action";
    const provider = node("p", "System rule (Jev not configured)");
    const confidence = node("p", `Confidence: ${percent(decision.confidence)}`, "decision.confidence");
    const reasons = document.createElement("ul");
    for (const reason of decision.reasons) {
      const row = document.createElement("li");
      row.append(node("span", reason.text, "decision.reasons"),
        node("small", `Evidence: ${reason.evidence.join(", ")}`, "decision.reasons.evidence"));
      reasons.append(row);
    }
    target.replaceChildren(title, provider, confidence, reasons);
    if (decision.review_required) {
      const banner = node("p", "Requires human review");
      banner.className = "storm-review";
      target.prepend(banner);
      if (decision.review_reason) target.insertBefore(node("p", decision.review_reason, "decision.review_reason"), title);
    }
  }

  function renderAssets() {
    const target = document.getElementById("storm-assets");
    const top = [...data.assets].sort((a, b) => (b.expected_usd ?? -1) - (a.expected_usd ?? -1)).slice(0, 5);
    if (!top.length) {
      target.replaceChildren(node("li", "No mapped assets in this area."));
      return;
    }
    const rows = top.map((asset) => {
      const row = document.createElement("li");
      row.append(node("strong", asset.name, "assets.name"),
        node("p", `${asset.class.replaceAll("_", " ")} | Peak wind ${asset.peak_wind_ms.toFixed(1)} m/s (${asset.peak_wind_mph.toFixed(1)} mph)`, "assets.peak_wind_ms"),
        node("p", `Damage chance: ${percent(asset.damage.minor)} | Expected cost: ${dollars(asset.expected_usd)}`, "assets.damage"),
        node("p", `${asset.accuracy} location | ${asset.source}`, "assets.source"));
      return row;
    });
    target.replaceChildren(...rows);
  }

  async function estimate() {
    const area = currentArea();
    if (!area) return;
    clear();
    const ownRequest = ++requestId;
    controller = new AbortController();
    button.disabled = true;
    status.textContent = "Estimating storm cost for this area.";
    try {
      const params = new URLSearchParams({ scenario: "gl1", lat: area.lat, lon: area.lon, radius_km: area.radius });
      const response = await fetch(`/api/storm/estimate?${params}`, { signal: controller.signal });
      if (!response.ok) throw new Error("Storm estimate request failed");
      const payload = await response.json();
      if (ownRequest !== requestId) return;
      if (!payload?.scenario?.frames?.length || !Array.isArray(payload.assets) || !payload.summary || !payload.decision) {
        throw new Error("Invalid storm estimate response");
      }
      data = payload;
      frameInput.max = String(payload.scenario.frames.length - 1);
      renderCost();
      renderDecision();
      renderAssets();
      results.hidden = false;
      draw();
      status.textContent = "Storm estimate ready. Hypothetical scenario, not observed damage.";
    } catch (error) {
      if (ownRequest !== requestId || error.name === "AbortError") return;
      status.textContent = "Could not estimate storm cost. Check the local server, then try again.";
    } finally {
      if (ownRequest === requestId) button.disabled = false;
    }
  }

  button.addEventListener("click", () => { void estimate(); });
  playButton.addEventListener("click", play);
  resetButton.addEventListener("click", () => { pause(); frame(0); });
  frameInput.addEventListener("input", () => { pause(); frame(Number(frameInput.value)); });

  function refreshTheme() {
    if (!data) return;
    const index = Number(frameInput.value);
    removeLayers();
    draw();
    frame(index);
  }

  return { clear, refreshTheme };
}
