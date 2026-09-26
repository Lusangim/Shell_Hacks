import { citation, money, readableEvidence, touchReasonLabel } from "./project-detail.js";
import { renderOverlapDetail } from "./overlap-detail.js";
import { state } from "./state.js";

const ASSUMPTIONS = new Map([
  ["coordination_fraction_v1", "Team screening assumption, 2026-09-26: 1% to 3% of reference cost. This is not a measured saving or evidence of a shared asset."],
  ["line_cost_per_mile_v1", "Team screening proxy, 2026-09-26: $1 million to $3 million per stated line mile. This is not a published rate or evidence of shared physical scope."],
]);

function text(tag, value, source) {
  const node = document.createElement(tag);
  node.textContent = value ?? "not stated";
  if (source) node.dataset.src = source;
  return node;
}

function field(parent, label, value, source) {
  const line = text("p", "");
  line.append(text("strong", `${label}: `), text("span", value, source));
  parent.append(line);
}

function distanceText(value) {
  if (!Number.isFinite(value)) return "not stated";
  return `${Number.isInteger(value) ? value.toFixed(1) : value} km`;
}

function savingsText(savings) {
  if (savings?.status === "range" && Number.isFinite(savings.low_usd) && Number.isFinite(savings.high_usd)) {
    return `${money(savings.low_usd)} to ${money(savings.high_usd)} estimate`;
  }
  const reasons = {
    timing_too_far: "No estimate: project timing is too far apart.",
    no_cost: "No estimate: usable cost or line mileage is not stated.",
    unknown_year: "No estimate: at least one project year is unknown.",
  };
  return reasons[savings?.status] ?? "No estimate available.";
}

function projectBlock(project, tag = "section") {
  const block = document.createElement(tag);
  if (!project) {
    block.append(text("p", "Project details not available in the current results."));
    return block;
  }
  const props = project.properties;
  block.append(text("p", props.name, "name"));
  field(block, "Utility", props.utility, "utility");
  field(block, "In service", props.in_service, "in_service");
  field(block, "Year", props.year, "year");
  field(block, "Accuracy", props.accuracy, "accuracy");
  block.append(citation(props.source));
  return block;
}

function coordinationField(parent) {
  const blank = text("p", "");
  blank.className = "coordination-status";
  parent.append(blank);
}

function selectedBlock(payload, selectedId) {
  const section = document.createElement("section");
  section.id = "print-selected";
  section.append(text("h2", "Selected overlap"));
  if (!payload) {
    section.append(text("p", selectedId ? "Selected overlap detail unavailable. Prepare the report again from Print report." : "No overlap selected. Choose a ranked pair to include its detail."));
    return section;
  }
  const pair = payload.overlap;
  if (!state.overlaps.some((item) => item.id === pair.id)) section.append(text("p", "Selected pair is outside the current filters."));
  const detail = document.createElement("div");
  renderOverlapDetail(payload, detail, section.querySelector("h2"));
  // Paper keeps every evidence disclosure open, including verbatim source descriptions.
  for (const disclosure of detail.querySelectorAll("details")) disclosure.open = true;
  field(detail.querySelector("details"), "Nearest mapped distance", distanceText(pair.distance_km), "distance_km");
  section.append(detail);
  section.append(text("h3", "Coordination status"));
  coordinationField(section);
  return section;
}

function rankedTable(projects) {
  const table = document.createElement("table");
  table.append(text("caption", `${state.overlaps.length} ranked overlaps`));
  const header = document.createElement("thead");
  const headings = document.createElement("tr");
  for (const label of ["Rank", "Project A / source", "Project B / source", "Distance / timing / evidence", "Screening savings", "Coordination status"]) {
    const cell = text("th", label);
    cell.scope = "col";
    headings.append(cell);
  }
  header.append(headings);
  const body = document.createElement("tbody");
  for (const pair of state.overlaps) {
    const row = document.createElement("tr");
    const rank = text("td", String(pair.rank), "rank");
    const context = [projects.get(pair.a), projects.get(pair.b)].filter(Boolean);
    const evidence = document.createElement("td");
    field(evidence, "Distance", distanceText(pair.distance_km), "distance_km");
    field(evidence, "Band", pair.band_label, "band_label");
    field(evidence, "Year gap", pair.year_gap == null ? "not stated" : `${pair.year_gap} years`, "year_gap");
    field(evidence, "Touch reason", touchReasonLabel(pair.touch_reason), "touch_reason");
    field(evidence, "Source evidence", readableEvidence(pair.touch_detail, context), "touch_detail");
    const savings = text("td", "");
    savings.append(text("p", savingsText(pair.savings), "savings_range"), text("p", readableEvidence(pair.savings?.basis, context), "savings_basis"));
    const blank = document.createElement("td");
    coordinationField(blank);
    row.append(rank, projectBlock(projects.get(pair.a), "td"), projectBlock(projects.get(pair.b), "td"), evidence, savings, blank);
    body.append(row);
  }
  table.append(header, body);
  return table;
}

function filterLabels(query) {
  const labels = { utility: "Utility", voltage_kv: "Voltage", year_min: "In service from",
    year_max: "In service through", project_type: "Project type", band: "Distance band", cross_state: "Cross-state" };
  const values = { touching: "Touching / crossing", lt_1_6km: "Under 1.6 km", lt_8km: "Under 8 km", lt_40km: "Under 40 km",
    new_line: "New line", rebuild_line: "Rebuild line", reconductor: "Reconductor", new_substation: "New substation",
    substation_upgrade: "Substation upgrade", equipment: "Equipment", other: "Other", true: "Yes", false: "No" };
  return [...new URLSearchParams(query)].map(([key, value]) =>
    `${labels[key] ?? "Filter"}: ${key === "voltage_kv" ? `${value} kV` : values[value] ?? readableEvidence(value)}`).join("; ") || "All overlaps";
}

function renderReport(report, query, payload, ready) {
  report.replaceChildren(text("h1", "GridLock coordination report"));
  if (!ready) {
    report.append(text("p", "Current filtered results are unavailable. Wait for the plans to load or retry the failed request before printing."));
    return;
  }
  field(report, "Prepared", new Date().toLocaleString("en-US"), "report_date");
  field(report, "Filters", filterLabels(query), "filters");
  field(report, "Timeline emphasis", state.timelineYear ?? "All years", "timeline_year");
  report.append(text("p", "Timeline emphasis does not change ranked or exported rows. Coordination opportunities and shared assets are unverified. Estimates are for discussion only; no realized savings are claimed."));
  report.append(selectedBlock(payload, state.selectedOverlapId));
  report.append(text("h2", "Team assumptions"));
  const ids = new Set([...state.overlaps.flatMap((pair) => pair.savings?.assumption_ids ?? []), ...(payload?.savings?.assumption_ids ?? [])]);
  for (const id of ids) report.append(text("p", ASSUMPTIONS.get(id) ?? "Assumption details unavailable.", "assumption"));
  if (!ids.size) report.append(text("p", "No screening assumptions apply to these results."));
  report.append(text("h2", "Ranked overlaps"));
  if (!state.overlaps.length) report.append(text("p", "No ranked overlaps match the current filters."));
  else report.append(rankedTable(new Map(state.projects.map((project) => [project.properties.id, project]))));
  report.append(text("h2", "Sources and attribution"));
  for (const source of state.meta?.source_documents ?? []) report.append(text("p", `${source.doc}; edition date: ${source.date ?? "not stated"}. Project citations above identify PDF pages.`, "source_documents"));
  report.append(text("p", document.querySelector(".disclaimer").textContent));
}

export function setupExport(filterControl) {
  const csv = document.getElementById("export-csv");
  const print = document.getElementById("print-report-button");
  const status = document.getElementById("export-status");
  const report = document.getElementById("print-report");
  let ready = false;
  let busy = false;
  let query = "";
  let revision = 0;
  let selected = null;

  function buttons() { csv.disabled = print.disabled = !ready || busy; }
  function setReady(value) {
    ready = value;
    revision += 1;
    selected = null;
    if (value) query = filterControl.query().toString();
    status.textContent = value ? "Export or print the current ranked results." : "Export and print are available after the current results load.";
    buttons();
  }

  async function download() {
    const ownRevision = revision;
    busy = true;
    buttons();
    status.textContent = "Preparing CSV download.";
    try {
      const response = await fetch(`/api/export/overlaps.csv${query ? `?${query}` : ""}`);
      if (!response.ok) throw new Error("CSV request failed");
      const blob = await response.blob();
      if (ownRevision !== revision) return;
      const filename = /filename="([^"/\\]+)"/i.exec(response.headers.get("Content-Disposition") ?? "")?.[1];
      if (!filename || !response.headers.get("Content-Type")?.startsWith("text/csv")) throw new Error("Invalid CSV response");
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = "CSV download prepared with the current filters.";
    } catch (_error) {
      if (ownRevision === revision) status.textContent = "Could not export CSV. Check the local server and select Export CSV to try again.";
    } finally { busy = false; buttons(); }
  }

  async function preparePrint() {
    const ownRevision = revision;
    const selectedId = state.selectedOverlapId;
    busy = true;
    selected = null;
    buttons();
    status.textContent = "Preparing print report.";
    try {
      let payload = null;
      if (selectedId) {
        const response = await fetch(`/api/overlaps/${encodeURIComponent(selectedId)}`);
        if (!response.ok) throw new Error("Selected detail request failed");
        payload = await response.json();
        if (!payload.overlap || !payload.project_a?.properties || !payload.project_b?.properties || !payload.savings) throw new Error("Incomplete print detail");
      }
      if (ownRevision !== revision) return;
      if (selectedId !== state.selectedOverlapId) {
        status.textContent = "Selection changed. Select Print report again for the current pair.";
        return;
      }
      selected = payload;
      renderReport(report, query, selected, ready);
      status.textContent = "Report prepared. Choose Letter paper in the print dialog.";
      window.print();
    } catch (_error) {
      if (ownRevision === revision) status.textContent = "Could not prepare print report. Check the local server and select Print report to try again.";
    } finally { busy = false; buttons(); }
  }

  csv.addEventListener("click", () => { void download(); });
  print.addEventListener("click", () => { void preparePrint(); });
  window.addEventListener("beforeprint", () => {
    const pair = state.overlaps.find((item) => item.id === state.selectedOverlapId);
    const current = selected?.overlap.id === state.selectedOverlapId ? selected : pair ? {
      overlap: pair, savings: pair.savings,
      project_a: state.projects.find((project) => project.properties.id === pair.a),
      project_b: state.projects.find((project) => project.properties.id === pair.b),
    } : null;
    renderReport(report, query, current, ready);
  });
  return { setReady };
}
