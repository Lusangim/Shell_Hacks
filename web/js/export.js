import { citation, money, readableEvidence, touchReasonLabel } from "./project-detail.js";
import { renderOverlapDetail } from "./overlap-detail.js";
import { state } from "./state.js";

const ASSUMPTIONS = new Map([
  ["unit_costs_2026", "Team unit-cost file, 2026-09-26: shareable cost items by job type and distance, priced from MISO's transmission cost guide (escalated to 2026 at 4% a year) and public land, wage and rental sources. Saving rates are team assumptions, not measured savings or evidence of a shared asset."],
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
    no_cost: "No estimate: the plans do not size this pair, or these job types share nothing at this distance.",
    unknown_year: "No estimate: at least one project year is unknown.",
  };
  return reasons[savings?.status] ?? "No estimate available.";
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

function yearsToCoordinate(pair) {
  if (!Number.isInteger(pair.a_year) || !Number.isInteger(pair.b_year)) return "Years not stated";
  const years = Math.max(0, Math.min(pair.a_year, pair.b_year) - new Date().getFullYear());
  return years === 0 ? "Coordinate now" : `${years} year${years === 1 ? "" : "s"} to coordinate`;
}

// A one-screen summary of the pairs in this report, so the reader knows what the pages below hold.
function glanceSection(pairs) {
  const section = document.createElement("section");
  section.id = "print-glance";
  section.append(text("h2", "At a glance"));
  if (!pairs.length) return section;
  const crossing = pairs.filter((pair) => pair.cross_state).length;
  section.append(text("p", `${pairs.length} ranked pair${pairs.length === 1 ? "" : "s"} in this report; ${crossing} cross the state line.`));
  const bands = [["touching", "touching"], ["lt_1_6km", "under 1.6 km"], ["lt_8km", "under 8 km"], ["lt_40km", "under 40 km"]]
    .map(([band, label]) => [label, pairs.filter((pair) => pair.band === band).length])
    .filter(([, count]) => count > 0).map(([label, count]) => `${label} ${count}`);
  section.append(text("p", `By distance: ${bands.join(", ")}.`));
  const ranged = pairs.filter((pair) => pair.savings?.status === "range" && Number.isFinite(pair.savings.low_usd) && Number.isFinite(pair.savings.high_usd));
  section.append(text("p", ranged.length
    ? `Possible savings: ${money(ranged.reduce((sum, pair) => sum + pair.savings.low_usd, 0))} to `
      + `${money(ranged.reduce((sum, pair) => sum + pair.savings.high_usd, 0))} across ${ranged.length} pair${ranged.length === 1 ? "" : "s"} `
      + "with an estimate. Each pair is estimated on its own and pairs can share a project, so this is a screening figure, not a budget."
    : "No pair in this report has a savings estimate."));
  const top = pairs[0];
  section.append(text("p", `Highest ranked: #${top.rank}, ${top.a_name} / ${top.b_name} (score ${top.score.toPrecision(2)}).`, "name"));
  return section;
}

function projectsCell(pair, projects) {
  const cell = document.createElement("td");
  for (const id of [pair.a, pair.b]) {
    const project = projects.get(id);
    const line = document.createElement("p");
    if (!project) {
      line.textContent = "Project details not available in the current results.";
    } else {
      const props = project.properties;
      const utility = props.utility_basis === "inferred_from_location" ? `${props.utility} (inferred)` : props.utility;
      line.append(text("strong", props.name, "name"), document.createTextNode(" · "), text("span", utility, "utility"),
        document.createTextNode(` · ${props.year ?? "year not stated"}`));
    }
    cell.append(line);
  }
  return cell;
}

function rankedTable(projects) {
  const table = document.createElement("table");
  table.append(text("caption", `${state.overlaps.length} ranked overlaps. The CSV export has every field, including the evidence text.`));
  // Letter width: names get the room; the status column stays wide enough to write in.
  const columns = document.createElement("colgroup");
  for (const width of ["6%", "32%", "19%", "14%", "16%", "13%"]) {
    const column = document.createElement("col");
    column.style.width = width;
    columns.append(column);
  }
  table.append(columns);
  const header = document.createElement("thead");
  const headings = document.createElement("tr");
  for (const label of ["Rank", "Projects", "Distance, timing and score", "Possible saving", "Sources", "Status"]) {
    const cell = text("th", label);
    cell.scope = "col";
    headings.append(cell);
  }
  header.append(headings);
  const body = document.createElement("tbody");
  for (const pair of state.overlaps) {
    const row = document.createElement("tr");
    const rank = text("td", String(pair.rank), "rank");
    const timing = document.createElement("td");
    const where = document.createElement("p");
    where.append(text("span", distanceText(pair.distance_km), "distance_km"), document.createTextNode(" · "),
      text("span", pair.band_label ?? "band not stated", "band_label"));
    timing.append(where, text("p", touchReasonLabel(pair.touch_reason), "touch_reason"),
      text("p", yearsToCoordinate(pair), "year_gap"), text("p", `Score ${pair.score.toPrecision(2)}`, "score"));
    const savings = text("td", savingsText(pair.savings), "savings_range");
    const sources = document.createElement("td");
    for (const id of [pair.a, pair.b]) {
      const project = projects.get(id);
      const line = document.createElement("p");
      if (project) line.append(citation(project.properties.source));
      sources.append(line);
    }
    const blank = document.createElement("td");
    coordinationField(blank);
    row.append(rank, projectsCell(pair, projects), timing, savings, sources, blank);
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
  report.append(glanceSection(state.overlaps));
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
