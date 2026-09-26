import { detailBlock, money, projectSummary, readableEvidence, touchReasonLabel } from "./project-detail.js";
import { highlightPair } from "./map.js";
import { state } from "./state.js";
import { setupBrief } from "./brief.js";

const ASSUMPTIONS = new Map([
  ["coordination_fraction_v1", "Team screening assumption, 2026-09-26: 1% to 3% of reference cost. This is not a measured saving or evidence of a shared asset."],
  ["line_cost_per_mile_v1", "Team screening proxy, 2026-09-26: $1 million to $3 million per stated line mile. This is not a published rate or evidence of shared physical scope."],
]);
const PAIR_ID = /^(?:desc-p[1-9][0-9]*|sertp-p[1-9][0-9]*-[0-9a-f]{6}(?:-[2-9][0-9]*)?)__(?:desc-p[1-9][0-9]*|sertp-p[1-9][0-9]*-[0-9a-f]{6}(?:-[2-9][0-9]*)?)$/;

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
  evidence.disclosure.append(text("p", readableEvidence(pair.touch_detail, [a, b]), "touch_detail"),
    text("p", readableEvidence(pair.can_share, [a, b]), "can_share"),
    text("p", Number.isInteger(pair.year_gap) ? `${pair.year_gap} years apart` : "Year gap not stated", "year_gap"),
    text("p", readableEvidence(pair.pair_note, [a, b]), "pair_note"));
  container.append(text("h3", "Why these projects appear together"), evidence.block, projects);

  let answer;
  if (savings.status === "range" && Number.isFinite(savings.low_usd) && Number.isFinite(savings.high_usd)) {
    answer = `Possible saving (estimate): ${money(savings.low_usd)} to ${money(savings.high_usd)}`;
  } else {
    const reasons = {
      timing_too_far: "No estimate: project timing is too far apart.",
      no_cost: "No estimate: usable cost or line mileage is not stated.",
      unknown_year: "No estimate: at least one project year is unknown.",
    };
    answer = reasons[savings.status] ?? "No estimate available.";
  }
  const estimate = detailBlock(answer, "savings_status", "How we estimated this");
  estimate.block.classList.add("savings-detail");
  estimate.list.classList.add("overlap-assumptions");
  const planCosts = [a, b].filter((project) => project.properties.cost_basis === "plan" && Number.isFinite(project.properties.cost_usd));
  if (savings.status === "range") {
    estimate.list.append(text("li", planCosts.length
      ? "Based on the stated plan costs shown above; unstated partner costs are excluded."
      : savings.assumption_ids?.includes("line_cost_per_mile_v1")
        ? "Team cost proxy: $1 million to $3 million per stated line mile."
        : "Based on stated line mileage; cost assumption details unavailable.", "estimate_scope"));
  }
  const assumptionLabels = [];
  for (const id of savings.assumption_ids ?? []) {
    if (id !== "line_cost_per_mile_v1") assumptionLabels.push(id === "coordination_fraction_v1"
      ? "1% to 3% of reference cost" : "details unavailable");
    estimate.disclosure.append(text("p", ASSUMPTIONS.get(id) ?? "Assumption details unavailable in this build.", "assumption_evidence"));
  }
  if (assumptionLabels.length) estimate.list.append(text("li", `Team screening assumption, 2026-09-26: ${assumptionLabels.join("; ")}.`, "assumption"));
  estimate.list.append(text("li", "Not verified: the plans do not show shared work.", "savings_caveat"));
  estimate.disclosure.append(text("p", readableEvidence(savings.basis, [a, b]), "savings_basis"));
  container.append(text("h3", "Screening savings"), estimate.block);
  content.replaceChildren(container);
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

  async function open(overlapId, { push = false } = {}) {
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
      if (ownRequest !== requestNumber) return;
      if (response.status === 404) {
        heading.textContent = "Stale overlap link";
        stateMessage.textContent = "This overlap link is stale. Choose a pair from the current ranked overlaps.";
        return;
      }
      if (!response.ok) throw new Error("Overlap detail request failed");
      const payload = await response.json();
      if (ownRequest !== requestNumber) return;
      if (payload.overlap?.id !== overlapId) throw new Error("Mismatched overlap detail");
      renderOverlapDetail(payload, content, heading);
      visiblePair = payload.overlap;
      select(visiblePair);
      void brief.open(payload);
      stateMessage.textContent = state.overlaps.some((pair) => pair.id === overlapId)
        ? "Public plan screening detail. A coordination opportunity is unverified."
        : "This pair is outside the current filters; its public-plan detail is shown below.";
    } catch (error) {
      if (ownRequest !== requestNumber || error.name === "AbortError") return;
      heading.textContent = "Overlap detail unavailable";
      stateMessage.textContent = "Could not load this overlap detail. Check the local server and try again.";
    }
  }

  function restoreFromHash() {
    if (!location.hash.startsWith("#overlap=")) {
      close();
      return;
    }
    try {
      open(decodeURIComponent(location.hash.slice(9)));
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
