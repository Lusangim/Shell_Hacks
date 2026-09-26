import { citation } from "./project-detail.js";
import { state } from "./state.js";

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

function row(list, label, value, source) {
  const wrapper = document.createElement("div");
  wrapper.className = "project-field";
  wrapper.append(text("dt", label), text("dd", value, source));
  list.append(wrapper);
}

function money(value) {
  if (value >= 1000000 && value % 1000000 === 0) return `$${value / 1000000}m`;
  if (value >= 1000 && value % 1000 === 0) return `$${value / 1000}k`;
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function projectCard(feature) {
  const props = feature.properties;
  const card = document.createElement("section");
  card.className = "overlap-project";
  card.append(text("h3", props.name, "name"), text("p", props.utility, "utility", "overlap-utility"),
    text("span", `${props.accuracy ?? "unknown"} location`, "accuracy", "overlap-accuracy"));
  const fields = document.createElement("dl");
  fields.className = "project-fields";
  row(fields, "Location basis", props.location_source, "location_source");
  row(fields, "In service", props.in_service, "in_service");
  const cost = Number.isFinite(props.cost_usd) ? money(props.cost_usd) : "not stated";
  row(fields, "Cost", `${cost} (${props.cost_basis ?? "none"} basis)`, "cost_basis");
  const sourceRow = document.createElement("div");
  sourceRow.className = "project-field";
  const value = document.createElement("dd");
  value.append(citation(props.source));
  sourceRow.append(text("dt", "Source"), value);
  fields.append(sourceRow);
  card.append(fields);
  return card;
}

function render(payload, content, heading) {
  const { overlap: pair, project_a: a, project_b: b, savings } = payload;
  if (!pair || !a?.properties || !b?.properties || !savings) throw new Error("Incomplete overlap detail");
  heading.textContent = `Overlap #${pair.rank}`;
  const container = document.createElement("div");
  container.className = "overlap-evidence";
  const projects = document.createElement("div");
  projects.className = "overlap-projects";
  projects.append(projectCard(a), projectCard(b));
  container.append(projects);

  const evidence = document.createElement("dl");
  evidence.className = "project-fields";
  row(evidence, "Distance", `${Number.isFinite(pair.distance_km) ? pair.distance_km.toFixed(1) + " km" : "not stated"} · ${pair.band_label ?? "band not stated"}`, "distance_km");
  row(evidence, "Touch reason", pair.touch_reason, "touch_reason");
  row(evidence, "Source evidence", pair.touch_detail, "touch_detail");
  row(evidence, "Opportunity", pair.can_share, "can_share");
  row(evidence, "Timeline", pair.timeline, "timeline");
  row(evidence, "Year gap", Number.isInteger(pair.year_gap) ? `${pair.year_gap} years` : "not stated", "year_gap");
  row(evidence, "Location confidence", pair.accuracy_pair === "approximate" ? "Approximate locations: possibly touching" : `${pair.accuracy_pair ?? "unknown"} locations`, "accuracy_pair");
  row(evidence, "Pair note", pair.pair_note, "pair_note");
  container.append(text("h3", "Why these projects appear together"), evidence);

  const savingsHeading = text("h3", "Screening savings");
  container.append(savingsHeading);
  if (savings.status === "range" && Number.isFinite(savings.low_usd) && Number.isFinite(savings.high_usd)) {
    container.append(text("p", `${money(savings.low_usd)} to ${money(savings.high_usd)} screening range`, "savings_range", "overlap-range"));
  } else {
    const reasons = {
      timing_too_far: "No screening range: project timing is too far apart.",
      no_cost: "No screening range: usable cost or line mileage is not stated.",
      unknown_year: "No screening range: at least one project year is unknown.",
    };
    container.append(text("p", reasons[savings.status] ?? "No screening range available.", "savings_status"));
  }
  const savingsFields = document.createElement("dl");
  savingsFields.className = "project-fields";
  row(savingsFields, "Estimate basis", savings.basis, "savings_basis");
  container.append(savingsFields);
  const assumptions = document.createElement("ul");
  assumptions.className = "overlap-assumptions";
  for (const id of savings.assumption_ids ?? []) {
    assumptions.append(text("li", ASSUMPTIONS.get(id) ?? `Assumption ${id}: details unavailable in this build.`, "assumption"));
  }
  if (assumptions.childElementCount) container.append(assumptions);
  content.replaceChildren(container);
}

export function setupOverlapDetail(projectView) {
  const detail = document.getElementById("overlap-detail");
  const content = document.getElementById("overlap-content");
  const stateMessage = document.getElementById("overlap-state");
  const heading = document.getElementById("overlap-detail-heading");
  const back = document.getElementById("overlap-back");
  let requestNumber = 0;
  let controller = null;

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
    requestNumber += 1;
    controller?.abort();
    controller = null;
    projectView.showOpportunities();
    if (push && location.hash.startsWith("#overlap=")) history.pushState(null, "", `${location.pathname}${location.search}`);
  }

  async function open(overlapId, { push = false } = {}) {
    requestNumber += 1;
    const ownRequest = requestNumber;
    controller?.abort();
    controller = null;
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
      render(payload, content, heading);
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
    if (detail.hidden || !location.hash.startsWith("#overlap=")) return;
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
