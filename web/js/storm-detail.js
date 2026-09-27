const ACTIONS = {
  human_review: "Review the estimate", coordinate_project_timing: "Coordinate project timing",
  inspect_asset: "Inspect exposed asset", preposition_crews: "Preposition crews",
  verify_source: "Verify source data",
};
const money = (value) => `$${Number(value).toLocaleString("en-US")}`;
const percent = (value) => `${Math.round(Number(value) * 100)}%`;
// Illustrative inputs do not support cents or tenths: winds to the whole unit, costs to the thousand.
export const wind = (asset) => `${Math.round(asset.peak_wind_ms)} m/s (${Math.round(asset.peak_wind_mph)} mph)`;
export const nearestThousand = (value) => (value < 1000 ? "under $1,000" : `about ${money(Math.round(value / 1000) * 1000)}`);
export const className = (value) => (value.startsWith("line_") ? `${value.slice(5)} line` : value.replaceAll("_", " "));
export const confidenceText = (decision) =>
  `Rule confidence ${percent(decision.confidence)}: the share of the expected cost on exactly located assets`;

function node(tag, value, source) {
  const item = document.createElement(tag);
  item.textContent = value;
  if (source) item.dataset.src = source;
  return item;
}

function fact(label, value, source) {
  const box = document.createElement("div");
  box.append(node("dt", label), node("dd", value, source));
  return box;
}

function disclosure(title, content, open = false) {
  const details = document.createElement("details");
  details.className = "pair-disclosure";
  details.open = open;
  details.append(node("summary", title), content);
  return details;
}

function assetsList(data) {
  const list = document.createElement("ol");
  list.className = "storm-detail-assets";
  const top = [...data.assets].sort((a, b) => b.peak_wind_ms - a.peak_wind_ms || a.id.localeCompare(b.id)).slice(0, 10);
  if (!top.length) list.append(node("li", "No mapped assets in this area."));
  for (const asset of top) {
    const item = document.createElement("li");
    item.append(node("strong", asset.name, "assets.name"),
      node("p", `${className(asset.class)} | Peak wind ${wind(asset)}`, "assets.peak_wind_ms"),
      node("p", `Illustrative damage chance ${percent(asset.damage.minor)} | Expected repair cost ${asset.expected_usd == null ? "no cost basis" : nearestThousand(asset.expected_usd)}`, "assets.damage"),
      node("small", `${asset.accuracy} location | ${asset.source}`, "assets.source"));
    list.append(item);
  }
  return list;
}

function recommendation(data) {
  const box = document.createElement("div");
  const decision = data.decision;
  box.append(node("p", "System rule (Jev not configured)"),
    node("p", ACTIONS[decision.action] ?? decision.action, "decision.action"),
    node("p", confidenceText(decision), "decision.confidence"));
  if (decision.review_required) {
    const banner = node("p", "Requires human review");
    banner.className = "storm-review";
    box.prepend(banner);
    if (decision.review_reason) box.append(node("p", decision.review_reason, "decision.review_reason"));
  }
  const reasons = document.createElement("ul");
  for (const reason of decision.reasons) {
    const item = document.createElement("li");
    item.append(node("span", reason.text, "decision.reasons"),
      node("small", `Evidence: ${reason.evidence.join(", ")}`, "decision.reasons.evidence"));
    reasons.append(item);
  }
  box.append(reasons);
  return box;
}

function assumptions(data) {
  const list = document.createElement("ul");
  list.append(node("li", "Holland wind model with illustrative fragility and repair ratios."));
  for (const assumption of data.summary.top_assumptions) list.append(node("li", assumption, "summary.top_assumptions"));
  list.append(node("li", `${data.summary.draws.toLocaleString("en-US")} draws with seed ${data.summary.seed}.`, "summary"));
  return list;
}

function sources(data) {
  const list = document.createElement("ul");
  for (const source of new Set(["HIFLD transmission lines (archived)", "OpenStreetMap substations",
    ...data.assets.map((asset) => asset.source)])) {
    list.append(node("li", source, "assets.source"));
  }
  list.append(node("li", "Team unit-cost file", "assets.evidence"));
  return list;
}

export function createStormDetail() {
  const pane = document.querySelector("aside.detail-pane");
  const section = document.getElementById("storm-detail");
  const pairBar = document.getElementById("detail-bar");
  const pair = document.getElementById("overlap-detail");
  const brief = document.getElementById("brief-panel");
  const nav = document.getElementById("detail-nav");
  const invoke = document.getElementById("storm-estimate");
  let prior = null;

  function close({ focus = true } = {}) {
    if (section.hidden) return;
    section.hidden = true;
    pane.hidden = prior.pane;
    pane.setAttribute("aria-label", prior.name);
    pairBar.hidden = prior.pairBar;
    pair.hidden = prior.pair;
    brief.hidden = prior.brief;
    nav.hidden = prior.nav;
    pane.classList.toggle("brief-open", prior.briefOpen);
    prior = null;
    if (focus) invoke.focus();
    requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
  }

  function open(data, area) {
    if (section.hidden) {
      prior = { pane: pane.hidden, name: pane.getAttribute("aria-label"), pairBar: pairBar.hidden,
        pair: pair.hidden, brief: brief.hidden, nav: nav.hidden, briefOpen: pane.classList.contains("brief-open") };
    }
    const counts = { line_wood: 0, line_steel: 0, substation: 0 };
    for (const asset of data.assets) counts[asset.class] += 1;
    const strongest = [...data.assets].sort((a, b) => b.peak_wind_ms - a.peak_wind_ms)[0];
    const summary = data.summary;
    const facts = document.createElement("dl");
    facts.className = "pair-facts storm-facts";
    facts.append(fact("Peak wind in area", strongest ? wind(strongest) : "No mapped assets", "assets.peak_wind_ms"),
      fact("Assets exposed", `${counts.line_wood} wood lines, ${counts.line_steel} steel lines, ${counts.substation} substations`, "assets.class"),
      fact("Possible repair cost", `${money(summary.p10_usd)} to ${money(summary.p90_usd)}; median ${money(summary.p50_usd)}`, "summary"),
      fact("Coverage", `${summary.assets_with_cost} of ${summary.assets_total} assets with a cost basis`, "summary"));
    document.getElementById("storm-detail-content").replaceChildren(facts,
      disclosure("Most exposed assets", assetsList(data)),
      disclosure("Recommendation", recommendation(data), true),
      disclosure("Assumptions", assumptions(data)),
      disclosure("Sources", sources(data)));
    document.getElementById("storm-detail-heading").textContent = data.scenario.name;
    document.getElementById("storm-detail-area").textContent =
      `Over: ${area.label ?? `${Number(area.lat).toFixed(5)}, ${Number(area.lon).toFixed(5)}`}, ${area.radius} km`;
    pairBar.hidden = pair.hidden = brief.hidden = nav.hidden = true;
    pane.classList.remove("brief-open");
    section.hidden = false;
    pane.hidden = false;
    pane.setAttribute("aria-label", "Storm results");
    pane.scrollTop = 0;
    document.getElementById("storm-detail-heading").focus({ preventScroll: true });
    requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
  }

  document.getElementById("storm-detail-close").addEventListener("click", () => close());
  document.addEventListener("gridlock:pair-view", () => close({ focus: false }));
  return { open, close };
}
