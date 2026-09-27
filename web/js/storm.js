import { createStormAnimation } from "./storm-animation.js";

const ACTIONS = {
  human_review: "Review the estimate", coordinate_project_timing: "Coordinate project timing",
  inspect_asset: "Inspect exposed asset", preposition_crews: "Preposition crews",
  verify_source: "Verify source data",
};
const dollars = (value) => value == null ? "no cost basis" : `$${Number(value).toLocaleString("en-US")}`;
const percent = (value) => `${Math.round(Number(value) * 100)}%`;

function node(tag, value, source) {
  const result = document.createElement(tag);
  result.textContent = String(value);
  if (source) result.dataset.src = source;
  return result;
}

export function createStormController(map, currentArea) {
  const button = document.getElementById("storm-estimate");
  const status = document.getElementById("storm-status");
  const results = document.getElementById("storm-results");
  const frameInput = document.getElementById("storm-frame");
  const frameLabel = document.getElementById("storm-frame-label");
  const playButton = document.getElementById("storm-play");
  const resetButton = document.getElementById("storm-reset");
  const skipButton = document.getElementById("storm-skip");
  const direction = document.getElementById("storm-direction");
  const category = document.getElementById("storm-category");
  let data = null;
  let animation = null;
  let controller = null;
  let requestId = 0;
  let playing = false;

  function clear() {
    requestId += 1;
    controller?.abort();
    controller = null;
    animation?.clear();
    animation = null;
    data = null;
    playing = false;
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
    frameInput.setAttribute("aria-valuetext", `${selected.t_hours} hours from area crossing`);
    const time = selected.t_hours < 0 ? `t ${selected.t_hours} h` : `t +${selected.t_hours} h`;
    frameLabel.textContent = `${time}; 33 m/s radius ${selected.radius_33_ms_km} km`;
    frameLabel.dataset.src = "scenario.frames";
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
    target.replaceChildren(...top.map((asset) => {
      const row = document.createElement("li");
      row.append(node("strong", asset.name, "assets.name"),
        node("p", `${asset.class.replaceAll("_", " ")} | Peak wind ${asset.peak_wind_ms.toFixed(1)} m/s (${asset.peak_wind_mph.toFixed(1)} mph)`, "assets.peak_wind_ms"),
        node("p", `Damage chance: ${percent(asset.damage.minor)} | Expected cost: ${dollars(asset.expected_usd)}`, "assets.damage"),
        node("p", `${asset.accuracy} location | ${asset.source}`, "assets.source"));
      return row;
    }));
  }

  async function estimate() {
    const area = currentArea();
    if (!area) return;
    clear();
    const ownRequest = ++requestId;
    controller = new AbortController();
    button.disabled = true;
    status.textContent = "Loading a hypothetical storm estimate.";
    try {
      const params = new URLSearchParams({ scenario: "synthetic", direction: direction.value, category: category.value,
        lat: area.lat, lon: area.lon, radius_km: area.radius });
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
      animation = createStormAnimation(map, payload, {
        onFrame: frame,
        onState: (state) => { playing = state === "playing"; playButton.textContent = playing ? "Pause storm" : "Resume storm"; },
        onFinish: () => { status.textContent = "Storm passage complete. Hypothetical scenario, not observed damage."; },
      });
      if (playing) status.textContent = "Hypothetical storm in progress. Not observed damage.";
    } catch (error) {
      if (ownRequest !== requestId || error.name === "AbortError") return;
      status.textContent = "Could not estimate storm cost. Check the local server, then try again.";
    } finally {
      if (ownRequest === requestId) button.disabled = false;
    }
  }

  button.addEventListener("click", () => { void estimate(); });
  playButton.addEventListener("click", () => { if (playing) animation?.pause(); else animation?.resume(); });
  resetButton.addEventListener("click", () => animation?.replay());
  skipButton.addEventListener("click", () => animation?.skip());
  frameInput.addEventListener("input", () => animation?.scrub(Number(frameInput.value)));

  return { clear, refreshTheme: () => animation?.refreshTheme() };
}
