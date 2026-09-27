import { detailBlock, money, projectSummary, readableEvidence, touchReasonLabel } from "./project-detail.js";
import { fitPairBounds, highlightPair } from "./map.js";
import { state } from "./state.js";
import { setupBrief } from "./brief.js";

const ASSUMPTIONS = new Map([
  ["unit_costs_2026", "Team unit-cost file, 2026-09-26: shareable cost items by job type and distance, priced from MISO's transmission cost guide (escalated to 2026 at 4% a year) and public land, wage and rental sources. Saving rates are team assumptions, not measured savings or evidence of a shared asset."],
]);
const PAIR_ID = /^(?:desc-p[1-9][0-9]*|sertp-p[1-9][0-9]*-[0-9a-f]{6}(?:-[2-9][0-9]*)?)__(?:desc-p[1-9][0-9]*|sertp-p[1-9][0-9]*-[0-9a-f]{6}(?:-[2-9][0-9]*)?)$/;
const BAND_WORDS = { touching: "touching", lt_1_6km: "under 1.6 km", lt_8km: "under 8 km", lt_40km: "under 40 km" };
const SCORE_RULES = "Distance band: touching 4, under 1.6 km 3, under 8 km 2, under 40 km 1. Timing: same year 1.0, "
  + "1 year apart 0.7, 2 years 0.4, 3 or more 0.1, a year unknown 0.3. Location: 1.0 for each exact project and 0.8 "
  + "for each approximate one. State line: 1.5 when the projects are in different states. Savings: 1 plus up to 0.3, "
  + "growing with the top of the savings range (0.15 at $100,000, the full 0.3 from $1,000,000).";

function text(tag, value, source, className = "") {
  const node = document.createElement(tag);
  if (source) node.dataset.src = source;
  if (className) node.className = className;
  node.textContent = value ?? "not stated";
  return node;
}

export function renderOverlapDetail(payload, content, heading) {
  const { overlap: pair, project_a: a, project_b: b, savings } = payload;
  if (!pair || !a?.properties || !b?.properties || !savings) throw new Error("Incomplete overlap detail");
  heading.textContent = `Overlap #${pair.rank}`;
  const container = document.createElement("div");
  container.className = "overlap-evidence";
  const projects = document.createElement("div");
  projects.className = "overlap-projects";
  projects.append(projectSummary(a), projectSummary(b));
  const confidence = pair.accuracy_pair === "approximate"
    ? `Approximate locations${pair.band === "touching" ? ": possibly touching" : "; distance is approximate"}.`
    : `${pair.accuracy_pair === "exact" ? "Exact" : "Unknown"} mapped locations.`;
  const evidence = detailBlock(`${Number.isFinite(pair.distance_km) ? pair.distance_km.toFixed(1) + " km" : "Distance not stated"} · ${pair.band_label ?? "band not stated"}`,
    "distance_km", "Pair evidence", [
      text("li", touchReasonLabel(pair.touch_reason), "touch_reason"),
      text("li", confidence, "accuracy_pair"),
      text("li", `Timing: ${pair.timeline ?? "not stated"}. Sharing is not verified.`, "timeline"),
    ]);
  if (pair.town_capped === true) {
    // The distance stays verbatim; the note explains why the band reads "Under 40 km".
    const towns = [a, b].filter((project) => project.properties.town_only === true).length;
    evidence.block.insertBefore(text("p", towns === 2
      ? "Counted as under 40 km: both locations are only town centres, not substations."
      : "Counted as under 40 km: one location is only a town centre, not a substation.", "town_capped", "detail-note"), evidence.list);
  }
  const gap = pair.year_gap;
  evidence.disclosure.append(text("p", readableEvidence(pair.touch_detail, [a, b]), "touch_detail"),
    text("p", readableEvidence(pair.can_share, [a, b]), "can_share"),
    text("p", !Number.isInteger(gap) ? "Year gap not stated" : gap === 0 ? "Same in-service year"
      : `${gap} year${gap === 1 ? "" : "s"} apart`, "year_gap"));
  // Only Georgia-only pairs carry a note; an absent note is not shown as "not stated".
  if (pair.pair_note) evidence.disclosure.append(text("p", readableEvidence(pair.pair_note, [a, b]), "pair_note"));
  container.append(text("h3", "Why these projects appear together"), evidence.block, projects);

  let answer;
  if (savings.status === "range" && Number.isFinite(savings.low_usd) && Number.isFinite(savings.high_usd)) {
    answer = `Possible saving (estimate): ${money(savings.low_usd)} to ${money(savings.high_usd)}`;
  } else {
    const reasons = {
      timing_too_far: "No estimate: project timing is too far apart.",
      no_cost: "No estimate: the plans do not size this pair, or these job types share nothing at this distance.",
      unknown_year: "No estimate: at least one project year is unknown.",
    };
    answer = reasons[savings.status] ?? "No estimate available.";
  }
  const estimate = detailBlock(answer, "savings_status", "How we estimated this");
  estimate.block.classList.add("savings-detail");
  estimate.list.classList.add("overlap-assumptions");
  if (savings.status === "range") {
    estimate.list.append(text("li", "Only costs both job types need at this distance count; the low end keeps sharing with a public precedent.", "estimate_scope"));
  }
  const assumptionLabels = [];
  for (const id of savings.assumption_ids ?? []) {
    assumptionLabels.push(id === "unit_costs_2026" ? "team unit costs by job type and distance" : "details unavailable");
    estimate.disclosure.append(text("p", ASSUMPTIONS.get(id) ?? "Assumption details unavailable in this build.", "assumption_evidence"));
  }
  if (assumptionLabels.length) estimate.list.append(text("li", `Team estimate, 2026-09-26: ${assumptionLabels.join("; ")}.`, "assumption"));
  estimate.list.append(text("li", "Not verified: the plans do not show shared work.", "savings_caveat"));
  estimate.disclosure.append(text("p", readableEvidence(savings.basis, [a, b]), "savings_basis"));
  container.append(text("h3", "Screening savings"), estimate.block);
  if (pair.score_parts && Number.isFinite(pair.score)) container.append(text("h3", "How this pair ranks"), scoreBlock(pair, savings));
  content.replaceChildren(container);
}

// The pipeline supplies the five factors; the page only names them.
function scoreBlock(pair, savings) {
  const parts = pair.score_parts;
  const gap = pair.year_gap;
  const one = (value) => (Number.isInteger(value) ? value.toFixed(1) : String(value));
  const terms = [
    `${BAND_WORDS[pair.band] ?? "distance band"}${pair.town_capped ? " (town only)" : ""} (${parts.band})`,
    `${gap == null ? "a year unknown" : gap === 0 ? "same year" : `${gap} year${gap > 1 ? "s" : ""} apart`} (${one(parts.timing)})`,
    `${parts.location === 1 ? "both locations exact" : parts.location === 0.8 ? "one location approximate" : "both locations approximate"} (${one(parts.location)})`,
    `${pair.cross_state ? "crosses the state line" : "same state"} (${one(parts.state_line)})`,
    parts.savings > 1 && Number.isFinite(savings.high_usd)
      ? `savings up to ${money(savings.high_usd)} (${parts.savings.toFixed(2)})` : `no savings bonus (${one(parts.savings)})`,
  ];
  const rank = detailBlock(`Score ${pair.score.toPrecision(2)} = ${terms.join(" × ")}`, "score", "How the score works", [
    text("li", "Distance counts most: savings add at most 30%, so with the rest equal a closer pair ranks higher.", "score_rule"),
    text("li", "Filters hide pairs; they never change a score or rank.", "score_filters"),
  ]);
  rank.block.classList.add("score-detail");
  rank.disclosure.append(text("p", SCORE_RULES, "score_rules"));
  return rank.block;
}

export function setupOverlapDetail(projectView) {
  const brief = setupBrief();
  const detail = document.getElementById("overlap-detail");
  const content = document.getElementById("overlap-content");
  const stateMessage = document.getElementById("overlap-state");
  const heading = document.getElementById("overlap-detail-heading");
  const back = document.getElementById("overlap-back");
  let requestNumber = 0;
  let controller = null;
  let visiblePair = null;

  function select(pair) {
    state.selectedOverlapId = pair?.id ?? null;
    document.querySelectorAll(".overlap-button[aria-pressed]").forEach((button) => {
      button.setAttribute("aria-pressed", String(Boolean(pair) && button.closest(".overlap-row").dataset.overlapId === pair.id));
    });
    highlightPair(pair);
    document.getElementById("map-pair-open").hidden = !pair;
  }

  function show(message) {
    projectView.showOverlapDetail();
    content.replaceChildren();
    stateMessage.textContent = message;
    const panel = document.querySelector(".panel");
    if (matchMedia("(max-width: 700px)").matches && !panel.classList.contains("expanded")) {
      panel.classList.add("expanded");
      const sheetButton = document.getElementById("sheet-toggle");
      sheetButton.setAttribute("aria-expanded", "true");
      sheetButton.textContent = "Collapse opportunities";
      window.requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
    }
    back.focus();
    detail.scrollIntoView({ block: "start" });
  }

  function close({ push = false } = {}) {
    brief.clear();
    requestNumber += 1;
    controller?.abort();
    controller = null;
    projectView.showOpportunities();
    if (push && location.hash.startsWith("#overlap=")) history.pushState(null, "", `${location.pathname}${location.search}`);
  }

  // A pair opened by link, reload, history or the area list is framed like a list click.
  function framePair(payload) {
    const bounds = L.latLngBounds([]);
    for (const project of [payload.project_a, payload.project_b]) {
      if (project?.geometry) bounds.extend(L.geoJSON(project).getBounds());
    }
    if (bounds.isValid()) fitPairBounds(bounds);
  }

  async function open(overlapId, { push = false, frame = false } = {}) {
    brief.clear();
    requestNumber += 1;
    const ownRequest = requestNumber;
    controller?.abort();
    controller = null;
    visiblePair = null;
    select(null);
    if (push && location.hash !== `#overlap=${overlapId}`) history.pushState(null, "", `#overlap=${overlapId}`);
    show("Loading overlap detail.");
    if (!PAIR_ID.test(overlapId)) {
      heading.textContent = "Unknown overlap link";
      stateMessage.textContent = "Unknown overlap link. Choose a pair from ranked overlaps.";
      return;
    }
    controller = new AbortController();
    try {
      const response = await fetch(`/api/overlaps/${encodeURIComponent(overlapId)}`, { signal: controller.signal });
      if (ownRequest !== requestNumber || detail.hidden) return;
      if (response.status === 404) {
        heading.textContent = "Stale overlap link";
        stateMessage.textContent = "This overlap link is stale. Choose a pair from the current ranked overlaps.";
        return;
      }
      if (!response.ok) throw new Error("Overlap detail request failed");
      const payload = await response.json();
      if (ownRequest !== requestNumber || detail.hidden) return;
      if (payload.overlap?.id !== overlapId) throw new Error("Mismatched overlap detail");
      renderOverlapDetail(payload, content, heading);
      visiblePair = payload.overlap;
      select(visiblePair);
      if (frame) framePair(payload);
      void brief.open(payload);
      stateMessage.textContent = state.overlaps.some((pair) => pair.id === overlapId)
        ? "Public plan screening detail. A coordination opportunity is unverified."
        : "This pair is outside the current filters; its public-plan detail is shown below.";
    } catch (error) {
      if (ownRequest !== requestNumber || detail.hidden || error.name === "AbortError") return;
      heading.textContent = "Overlap detail unavailable";
      stateMessage.textContent = "Could not load this overlap detail. Check the local server and try again.";
    }
  }

  function restoreFromHash(event) {
    if (!location.hash.startsWith("#overlap=")) {
      close();
      return;
    }
    // On first load an area in the URL keeps its restored map view; navigation always frames the pair.
    const frame = Boolean(event) || !new URLSearchParams(location.search).has("area");
    try {
      open(decodeURIComponent(location.hash.slice(9)), { frame });
    } catch (_error) {
      open("invalid");
    }
  }

  function refreshFilterState() {
    if (detail.hidden || !visiblePair || !location.hash.startsWith("#overlap=")) return;
    select(visiblePair);
    stateMessage.textContent = state.overlaps.some((pair) => pair.id === state.selectedOverlapId)
      ? "Public plan screening detail. A coordination opportunity is unverified."
      : "This pair is outside the current filters; its public-plan detail is shown below.";
  }

  back.addEventListener("click", () => {
    close({ push: true });
    const selected = Array.from(document.querySelectorAll(".overlap-row"))
      .find((row) => row.dataset.overlapId === state.selectedOverlapId)?.querySelector("button");
    (selected ?? document.getElementById("opportunities")).focus();
  });
  window.addEventListener("popstate", restoreFromHash);
  window.addEventListener("hashchange", restoreFromHash);
  return { open, close, restoreFromHash, refreshFilterState };
}
