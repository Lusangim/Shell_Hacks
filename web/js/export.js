import { citation, money, readableEvidence, touchReasonLabel, utilityLabel } from "./project-detail.js";
import { state } from "./state.js";
import { addTrackingToCsv, coordinationText } from "./tracker.js";

const ASSUMPTIONS = new Map([
  ["unit_costs_2026", "Team unit-cost file, 2026-09-26: shareable cost items by job type and distance, priced from MISO's transmission cost guide (escalated to 2026 at 4% a year) and public land, wage and rental sources. Saving rates are team assumptions, not measured savings or evidence of a shared asset."],
]);
const DISCLAIMER = "Screening leads from public plans: shared work, locations and savings are not verified.";
// The same credit the offline basemap carries on screen.
const MAP_ATTRIBUTION = "Map data: © OpenStreetMap contributors · Protomaps.";
const NO_ESTIMATE = {
  timing_too_far: "No estimate: project timing is too far apart.",
  no_cost: "No estimate: the plans do not size this pair, or these job types share nothing at this distance.",
  unknown_year: "No estimate: at least one project year is unknown.",
};
const NO_ESTIMATE_SHORT = {
  timing_too_far: "No estimate: timing too far apart",
  no_cost: "No estimate: not sized",
  unknown_year: "No estimate: a year is unknown",
};
// Widths of # | Utilities | Projects | In service | Distance | Possible saving | Status on Letter paper.
const COLUMNS = [["#", "5%", true], ["Utilities", "16%"], ["Projects", "35%"], ["In service", "8%", true],
  ["Distance", "11%", true], ["Possible saving (estimate)", "14%", true], ["Status", "11%"]];

function text(tag, value, source, className) {
  const node = document.createElement(tag);
  node.textContent = value ?? "unknown";
  if (source) node.dataset.src = source;
  if (className) node.className = className;
  return node;
}

function hasEstimate(savings) {
  return savings?.status === "range" && Number.isFinite(savings.low_usd) && Number.isFinite(savings.high_usd);
}

function distanceText(value) {
  return Number.isFinite(value) ? `${value.toFixed(1)} km` : "Distance unknown";
}

function savingsText(savings) {
  if (hasEstimate(savings)) return `Possible saving (estimate): ${money(savings.low_usd)} to ${money(savings.high_usd)}`;
  return NO_ESTIMATE[savings?.status] ?? "No estimate available.";
}

function yearsToCoordinate(pair) {
  if (!Number.isInteger(pair.a_year) || !Number.isInteger(pair.b_year)) return "Unknown: an in-service year is not stated";
  const years = Math.max(0, Math.min(pair.a_year, pair.b_year) - new Date().getFullYear());
  return years === 0 ? "Coordinate now" : `${years} year${years === 1 ? "" : "s"} to coordinate`;
}

function locationConfidence(pair) {
  return pair.accuracy_pair === "approximate"
    ? `Approximate locations${pair.band === "touching" ? ": possibly touching" : "; distance is approximate"}.`
    : `${pair.accuracy_pair === "exact" ? "Exact" : "Unknown"} mapped locations.`;
}

function coordinationField(parent, pairId) {
  const blank = text("p", coordinationText(pairId));
  blank.className = "coordination-status";
  parent.append(blank);
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

function metaRow(list, label, value, source) {
  list.append(text("dt", label), text("dd", value, source));
}

function headerSection(query) {
  const header = document.createElement("header");
  header.id = "print-header";
  const meta = document.createElement("dl");
  meta.className = "print-meta";
  metaRow(meta, "Prepared", new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }), "report_date");
  // One plan per line, each exactly as the metadata names it, as on the page's edition line.
  const editions = document.createElement("dd");
  editions.dataset.src = "source_documents";
  for (const source of state.meta?.source_documents ?? []) {
    editions.append(text("span", [source.doc, source.date].filter(Boolean).join(" / "), null, "print-edition"));
  }
  if (!editions.childElementCount) editions.textContent = "Plan editions unavailable";
  meta.append(text("dt", "Plan editions"), editions);
  metaRow(meta, "Filters", filterLabels(query), "filters");
  header.append(meta);
  return header;
}

// Three counts and the savings range, so the reader knows what the pages below hold.
function glanceSection(pairs) {
  const section = document.createElement("section");
  section.id = "print-glance";
  section.append(text("h2", "Key figures"));
  const figures = document.createElement("div");
  figures.className = "print-figures";
  const figure = (value, label, note) => {
    const item = document.createElement("div");
    item.className = "print-figure";
    item.append(text("p", value, null, "print-figure-value"), text("p", label, null, "print-figure-label"));
    if (note) item.append(text("p", note, null, "print-figure-note"));
    figures.append(item);
  };
  const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;
  figure(String(pairs.length), pairs.length === 1 ? "Pair in this report" : "Pairs in this report");
  figure(String(pairs.filter((pair) => pair.cross_state).length), "Cross-state pairs");
  figure(String(pairs.filter((pair) => pair.band === "touching").length), "Touching pairs");
  const ranged = pairs.filter((pair) => hasEstimate(pair.savings));
  if (ranged.length) {
    // Each pair is estimated on its own and pairs can share a project, so the total is not a budget.
    figure(`${money(ranged.reduce((sum, pair) => sum + pair.savings.low_usd, 0))} to ${money(ranged.reduce((sum, pair) => sum + pair.savings.high_usd, 0))}`,
      `Possible savings across ${plural(ranged.length, "pair")} with an estimate`, "Screening estimate, not a budget");
  } else {
    figure("No estimate", "No pair in this report has a savings estimate");
  }
  section.append(figures);
  return section;
}

function projectCard(label, feature) {
  const block = document.createElement("div");
  block.className = "print-project";
  block.append(text("p", label, null, "print-label"));
  if (!feature?.properties) {
    block.append(text("p", "Project details not available in the current results."));
    return block;
  }
  const props = feature.properties;
  block.append(text("p", utilityLabel(props), "utility", "print-utility"), text("p", props.name, "name", "print-name"));
  const facts = text("p", `In service ${props.year ?? "unknown"} · Location ${props.accuracy ?? "unknown"}${props.town_only ? " (town only)" : ""}`, null, "print-muted");
  const source = text("p", "Source: ", null, "print-cite");
  source.append(citation(props.source));
  block.append(facts, source);
  return block;
}

function fact(list, label, ...values) {
  const value = document.createElement("dd");
  value.append(...values);
  list.append(text("dt", label), value);
}

function selectedBlock(payload, selectedId) {
  const section = document.createElement("section");
  section.id = "print-selected";
  section.append(text("h2", "Selected pair"));
  if (!payload) {
    section.append(text("p", selectedId ? "Selected overlap detail unavailable. Prepare the report again from Print report." : "No overlap selected. Choose a ranked pair to include its detail.", null, "print-muted"));
    return section;
  }
  const { overlap: pair, project_a: a, project_b: b, savings } = payload;
  const card = document.createElement("div");
  card.className = "print-card";
  const title = text("h3", `Pair #${pair.rank}`, null, "print-card-title");
  if (Number.isFinite(pair.score)) title.append(text("span", ` · score ${pair.score.toPrecision(2)}`, "score", "print-muted"));
  card.append(title);
  if (!state.overlaps.some((item) => item.id === pair.id)) card.append(text("p", "Selected pair is outside the current filters.", null, "print-flag"));
  const projects = document.createElement("div");
  projects.className = "print-projects";
  projects.append(projectCard("Project A", a), projectCard("Project B", b));
  const facts = document.createElement("dl");
  facts.className = "print-facts";
  const where = document.createElement("p");
  where.append(text("span", distanceText(pair.distance_km), "distance_km"), " · ", text("span", pair.band_label, "band_label"),
    " · ", text("span", locationConfidence(pair), "accuracy_pair"));
  const distance = [where];
  if (pair.town_capped === true) {
    // The distance stays verbatim; the note explains why the band reads "Under 40 km".
    distance.push(text("p", [a, b].filter((project) => project?.properties?.town_only === true).length === 2
      ? "Counted as under 40 km: both locations are only town centres, not substations."
      : "Counted as under 40 km: one location is only a town centre, not a substation.", "town_capped", "print-muted"));
  }
  fact(facts, "Distance", ...distance);
  fact(facts, "Years to coordinate", text("span", yearsToCoordinate(pair), "years_to_coordinate"));
  fact(facts, "Possible saving", text("span", savingsText(savings), "savings_status"));
  fact(facts, "Why together", text("span", `${touchReasonLabel(pair.touch_reason)}. `, "touch_reason"),
    text("span", readableEvidence(pair.touch_detail, [a, b].filter(Boolean)), "touch_detail"));
  const status = document.createElement("dd");
  coordinationField(status, pair.id);
  facts.append(text("dt", "Coordination status"), status);
  card.append(projects, facts);
  section.append(card);
  return section;
}

function pairCell(pair, projects) {
  const cell = document.createElement("td");
  cell.colSpan = 3;
  cell.className = "print-pair";
  // One grid row per project keeps each utility, name and year on the same line across three columns.
  const grid = document.createElement("div");
  grid.className = "print-pair-grid";
  for (const id of [pair.a, pair.b]) {
    const props = projects.get(id)?.properties;
    if (!props) {
      grid.append(text("div", "Project details not available in the current results.", null, "print-missing"));
      continue;
    }
    const name = document.createElement("div");
    const cite = text("div", "", null, "print-cite");
    cite.append(citation(props.source));
    name.append(text("div", props.name, "name", "print-name"), cite);
    grid.append(text("div", utilityLabel(props), "utility"), name, text("div", props.year ?? "unknown", "in_service", "print-num"));
  }
  cell.append(grid);
  return cell;
}

function rankedTable(pairs, projects) {
  const table = document.createElement("table");
  table.className = "print-table";
  const columns = document.createElement("colgroup");
  const headings = document.createElement("tr");
  for (const [label, width, numeric] of COLUMNS) {
    const column = document.createElement("col");
    column.style.width = width;
    columns.append(column);
    const cell = text("th", label, null, numeric ? "print-num" : "");
    cell.scope = "col";
    headings.append(cell);
  }
  const header = document.createElement("thead");
  header.append(headings);
  const body = document.createElement("tbody");
  for (const pair of pairs) {
    const row = document.createElement("tr");
    const distance = document.createElement("td");
    distance.className = "print-num";
    distance.append(text("div", distanceText(pair.distance_km), "distance_km"), text("div", pair.band_label, "band_label", "print-muted"));
    const saving = text("td", hasEstimate(pair.savings) ? `${money(pair.savings.low_usd)} – ${money(pair.savings.high_usd)}`
      : NO_ESTIMATE_SHORT[pair.savings?.status] ?? "No estimate", "savings_range", "print-num");
    const status = document.createElement("td");
    coordinationField(status, pair.id);
    row.append(text("td", String(pair.rank), "rank", "print-num"), pairCell(pair, projects), distance, saving, status);
    body.append(row);
  }
  table.append(columns, header, body);
  return table;
}

function sourcesSection(payload) {
  const section = document.createElement("section");
  section.id = "print-sources";
  section.append(text("h2", "Sources and notes"));
  const notes = document.createElement("ul");
  for (const source of state.meta?.source_documents ?? []) {
    notes.append(text("li", `${source.doc}, ${source.date ? `edition ${source.date}` : "edition date not stated"}${source.url ? `: ${source.url}` : ""}.`, "source_documents"));
  }
  notes.append(text("li", MAP_ATTRIBUTION, "map_attribution"));
  const ids = new Set([...state.overlaps.flatMap((pair) => pair.savings?.assumption_ids ?? []), ...(payload?.savings?.assumption_ids ?? [])]);
  for (const id of ids) notes.append(text("li", ASSUMPTIONS.get(id) ?? "Assumption details unavailable.", "assumption"));
  if (!ids.size) notes.append(text("li", "No screening assumptions apply to these results.", "assumption"));
  const independence = document.querySelector(".disclaimer")?.textContent?.trim();
  if (independence) notes.append(text("li", independence));
  section.append(notes, text("p", DISCLAIMER, "disclaimer", "print-disclaimer"));
  return section;
}

function renderReport(report, query, payload, ready) {
  const header = headerSection(query);
  header.prepend(text("h1", "GridLock coordination report"));
  if (!ready) {
    header.replaceChildren(header.firstChild);
    report.replaceChildren(header, text("p", "Current filtered results are unavailable. Wait for the plans to load or retry the failed request before printing."));
    return;
  }
  report.replaceChildren(header, glanceSection(state.overlaps), selectedBlock(payload, state.selectedOverlapId));
  const ranked = document.createElement("section");
  ranked.id = "print-ranked";
  ranked.append(text("h2", "Ranked pairs"));
  if (!state.overlaps.length) ranked.append(text("p", "No ranked overlaps match the current filters.", null, "print-muted"));
  else ranked.append(rankedTable(state.overlaps, new Map(state.projects.map((project) => [project.properties.id, project]))));
  report.append(ranked, sourcesSection(payload));
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
      const blob = await addTrackingToCsv(await response.blob());
      if (ownRevision !== revision) return;
      const filename = /filename="([^"/\\]+)"/i.exec(response.headers.get("Content-Disposition") ?? "")?.[1];
      if (!filename || !response.headers.get("Content-Type")?.startsWith("text/csv")) throw new Error("Invalid CSV response");
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      status.textContent = "CSV downloaded with your current filters.";
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
