import { swatchFor } from "./look.js";

const SOURCE_DOCS = new Map([
  ["SCRTP Planned Facilities 2026-2030 $2M & Above", "desc-scrtp-2026-2030"],
  ["SERTP 2025 Regional Transmission Plan (Nov 26 2025)", "sertp-2025-rtp"],
]);

function sourced(tag, value, name) {
  const element = document.createElement(tag);
  element.dataset.src = name;
  element.textContent = value ?? "not stated";
  return element;
}

export function money(value) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

export function utilityLabel(props) {
  const utility = props?.utility ?? "Utility not stated";
  return props?.utility_basis === "inferred_from_location" ? `${utility} (inferred)` : utility;
}

export function readableEvidence(value, projects = []) {
  let result = value ?? "not stated";
  // Only presentation changes: summaries use structured fields, never extracted prose.
  for (const project of projects) {
    const props = project.properties;
    result = result.replaceAll(props.id, `${utilityLabel(props)} project`);
  }
  return result.replace(/\b(?:desc-p\d+|sertp-p\d+-[a-f0-9]+(?:-\d+)?)(?:__(?:desc-p\d+|sertp-p\d+-[a-f0-9]+(?:-\d+)?))?\b/g, "project")
    .replace(/\bdata[\\/][^\s;)]+/g, "committed source file")
    .replace(/\b[A-Za-z]:[\\/][^\s;)]+/g, "local source file")
    .replace(/\bTAP\d+\b/g, "archived line feature")
    .replace(/\b[a-z]+(?:_[a-z0-9]+)+\b/g, (label) => label.replaceAll("_", " "));
}

export function touchReasonLabel(reason) {
  return { same_substation: "Same named substation", shared_endpoint: "Shared named endpoint",
    lines_cross: "Mapped lines cross", proximity: "Nearby mapped locations",
    same_area_approximate: "Same approximate area" }[reason] ?? "Relationship not stated";
}

export function detailBlock(answer, source, disclosureLabel, bullets = []) {
  const block = document.createElement("section");
  block.className = "detail-block";
  const lead = sourced("p", answer, source);
  lead.className = "detail-answer";
  const list = document.createElement("ul");
  list.className = "detail-points";
  for (const bullet of bullets) list.append(bullet);
  const disclosure = document.createElement("details");
  const summary = document.createElement("summary");
  summary.textContent = disclosureLabel;
  disclosure.append(summary);
  block.append(lead, list, disclosure);
  return { block, list, disclosure };
}

export function projectSummary(feature, includeName = true) {
  const props = feature.properties;
  const container = document.createElement("div");
  container.className = "overlap-project";
  if (includeName) container.append(sourced("h3", props.name, "name"));
  const summary = detailBlock(utilityLabel(props), "utility", "Source text", [
    sourced("li", `In service: ${props.in_service ?? "not stated"}`, "in_service"),
  ]);
  summary.block.querySelector(".detail-answer").prepend(swatchFor(props));
  const cost = document.createElement("li");
  cost.append(document.createTextNode("Plan cost: "), sourced("span",
    props.cost_basis === "plan" && Number.isFinite(props.cost_usd) ? money(props.cost_usd) : "not stated", "cost_usd"));
  const warnings = {
    printed_total_differs_from_sum: "Printed total differs from the year columns; verify the source.",
    below_list_threshold: "Printed total is below the list's $2 million threshold.",
  };
  for (const flag of props.cost_flags ?? []) {
    if (!warnings[flag]) continue;
    const warning = document.createElement("span");
    warning.className = "cost-warning";
    warning.textContent = warnings[flag];
    cost.append(warning);
  }
  summary.list.append(cost);
  summary.block.insertBefore(citation(props.source), summary.list);
  summary.disclosure.append(sourced("p", props.description, "description"),
    sourced("p", props.need, "need"), sourced("p", `Status: ${props.status ?? "not stated"}`, "status"));
  // A town-centre-only location says so in the visible bullets, not only behind "Location sources".
  const townOnly = props.town_only === true && Boolean(feature.geometry);
  const where = townOnly
    ? sourced("li", feature.geometry.type === "Point"
      ? "Town-level location: drawn at the town centre, not at a substation."
      : "Town-level location: drawn as a straight line between town centres, not substations.", "town_only")
    : sourced("li", !feature.geometry ? "Proximity cannot be assessed." : feature.geometry.type === "Point"
      ? "Shown as a mapped point." : "Shown as a mapped line.", "geometry");
  const location = detailBlock(`Location: ${props.accuracy ?? "unknown"}`, "accuracy", "Location sources", [
    where,
    sourced("li", "Construction limits are not verified.", "location_caveat"),
  ]);
  location.disclosure.append(sourced("p", readableEvidence(props.location_source, [feature]), "location_source"));
  container.append(summary.block, location.block);
  return container;
}

export function projectAbsenceMessage(feature, filtered) {
  if (!feature?.geometry) return "Location unknown; proximity cannot be assessed.";
  return filtered ? "No related overlaps are shown by the current filters."
    : "This placed project has no overlap within 40 km in the loaded plans.";
}

export function citation(source) {
  const text = source?.doc ? `${source.doc}${source.page ? `, p. ${source.page}` : ""}` : "Source not stated";
  const documentId = SOURCE_DOCS.get(source?.doc);
  if (documentId && Number.isInteger(source.page) && source.page > 0) {
    const link = sourced("a", text, "source");
    link.href = `/api/sources/${documentId}#page=${source.page}`;
    return link;
  }
  return sourced("span", text, "source");
}

export function setupProjectDetail() {
  const toggle = document.getElementById("projects-toggle");
  const opportunities = document.getElementById("opportunities");
  const projectsPanel = document.getElementById("projects-panel");
  const detail = document.getElementById("project-detail");
  const overlapDetail = document.getElementById("overlap-detail");
  const detailBar = document.getElementById("detail-bar");
  const unknown = document.getElementById("unknown-locations");
  const filter = document.getElementById("project-filter");
  const list = document.getElementById("project-list");
  const message = document.getElementById("projects-state");
  const back = document.getElementById("project-back");
  const status = document.getElementById("status");
  let projects = [];
  let overlaps = [];
  let view = "overlaps";
  let previousView = "overlaps";
  let selectedButton = null;
  let loadError = false;
  let filtered = false;

  function showView(next) {
    view = next;
    opportunities.hidden = next !== "overlaps" && next !== "overlap-detail";
    // The ranked list remains available alongside the selected pair's detail.
    opportunities.classList.toggle("pair-open", next === "overlap-detail");
    detailBar.hidden = next !== "overlap-detail";
    projectsPanel.hidden = next !== "projects";
    detail.hidden = next !== "detail";
    overlapDetail.hidden = next !== "overlap-detail";
    document.querySelector(".detail-pane").hidden = next !== "overlap-detail";
    requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
    unknown.hidden = next !== "overlaps" || !unknown.querySelector("li");
    toggle.textContent = next === "overlaps" ? "Projects" : "Overlaps";
    toggle.setAttribute("aria-pressed", String(next !== "overlaps"));
  }

  function filterProjects() {
    const query = filter.value.trim().toLocaleLowerCase();
    let visible = 0;
    for (const row of list.children) {
      row.hidden = !row.dataset.searchText.includes(query);
      if (!row.hidden) visible += 1;
    }
    message.textContent = loadError ? "Could not load public plan data. Check the local server and try again."
      : projects.length === 0 ? filtered
        ? "No projects match the current filters. Open Filters and select Clear all filters to see all projects."
        : "No projects in the loaded plans."
      : visible === 0 ? "No projects match this search." : `${visible} projects shown.`;
  }

  function renderProjects(features, pairs, hasFilters = false) {
    projects = features;
    overlaps = pairs;
    filtered = hasFilters;
    loadError = false;
    list.replaceChildren();
    for (const feature of projects) {
      const props = feature.properties;
      const item = document.createElement("li");
      item.className = "project-row";
      item.dataset.testid = "project-row";
      item.dataset.projectRef = props.id;
      item.dataset.searchText = `${props.name} ${props.utility}`.toLocaleLowerCase();
      const button = document.createElement("button");
      button.type = "button";
      button.append(sourced("strong", props.name, "name"), sourced("span", utilityLabel(props), "utility"));
      button.addEventListener("click", () => openProject(props.id, "projects", button));
      item.append(button);
      list.append(item);
    }
    filterProjects();
  }

  function showLoadError() {
    projects = [];
    overlaps = [];
    loadError = true;
    list.replaceChildren();
    filterProjects();
  }

  function renderDetail(feature) {
    const props = feature.properties;
    const fields = document.getElementById("project-fields");
    const related = document.getElementById("project-overlaps");
    document.getElementById("project-detail-heading").textContent = props.name;
    fields.replaceChildren(projectSummary(feature, false));

    related.replaceChildren();
    const matching = overlaps.filter((pair) => pair.a === props.id || pair.b === props.id);
    if (matching.length === 0) {
      related.textContent = projectAbsenceMessage(feature, filtered);
    } else {
      const items = document.createElement("ol");
      items.className = "project-related";
      for (const pair of matching) {
        const otherId = pair.a === props.id ? pair.b : pair.a;
        const other = projects.find((item) => item.properties.id === otherId)?.properties;
        const item = document.createElement("li");
        item.append(sourced("span", `#${pair.rank}`, "rank"), document.createTextNode(" / "),
          sourced("span", other?.name ?? "Project not stated", "name"), document.createTextNode(" / "),
          sourced("span", pair.band_label, "band_label"));
        items.append(item);
      }
      related.append(items);
    }
  }

  function openProject(projectId, origin = view, button = null) {
    const feature = projects.find((item) => item.properties.id === projectId);
    if (!feature) return;
    previousView = origin;
    selectedButton = button;
    renderDetail(feature);
    showView("detail");
    back.textContent = origin === "projects" ? "Back to projects" : "Back to overlaps";
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
    if (origin === "projects") {
      status.dataset.src = "name";
      status.textContent = `Project selected: ${feature.properties.name}.`;
    }
  }

  toggle.addEventListener("click", () => {
    showView(view === "overlaps" ? "projects" : "overlaps");
    if (view === "projects") filter.focus();
    else opportunities.focus();
  });
  filter.addEventListener("input", filterProjects);
  back.addEventListener("click", () => {
    showView(previousView);
    if (selectedButton?.isConnected && previousView === "projects") selectedButton.focus();
    else opportunities.focus();
  });

  return { renderProjects, showLoadError, openProject,
    showOverlapDetail: () => showView("overlap-detail"),
    showOpportunities: () => showView("overlaps") };
}
