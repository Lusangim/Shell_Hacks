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

function field(list, label, value, source) {
  const row = document.createElement("div");
  row.className = "project-field";
  const title = document.createElement("dt");
  title.textContent = label;
  const content = document.createElement("dd");
  content.append(sourced("span", value, source));
  row.append(title, content);
  list.append(row);
}

function citation(source) {
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

  function showView(next) {
    view = next;
    opportunities.hidden = next !== "overlaps";
    projectsPanel.hidden = next !== "projects";
    detail.hidden = next !== "detail";
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
      : projects.length === 0 ? "No projects in the loaded plans."
      : visible === 0 ? "No projects match this search." : `${visible} projects shown.`;
  }

  function renderProjects(features, pairs) {
    projects = features;
    overlaps = pairs;
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
      button.append(sourced("strong", props.name, "name"), sourced("span", props.utility, "utility"));
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
    const values = document.createElement("dl");
    values.className = "project-fields";
    field(values, "Utility", props.utility, "utility");
    field(values, "Description", props.description, "description");
    field(values, "In service", props.in_service, "in_service");
    field(values, "Location", `${props.accuracy ?? "unknown"} location`, "accuracy");
    field(values, "Location basis", props.location_source, "location_source");
    const cost = props.cost_basis === "plan" && Number.isFinite(props.cost_usd)
      ? new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(props.cost_usd)
      : "not stated";
    field(values, "Plan cost", cost, "cost_usd");
    const sourceRow = document.createElement("div");
    sourceRow.className = "project-field";
    const sourceTitle = document.createElement("dt");
    sourceTitle.textContent = "Source";
    const sourceValue = document.createElement("dd");
    sourceValue.append(citation(props.source));
    sourceRow.append(sourceTitle, sourceValue);
    values.append(sourceRow);
    fields.replaceChildren(values);

    related.replaceChildren();
    const matching = overlaps.filter((pair) => pair.a === props.id || pair.b === props.id);
    if (matching.length === 0) {
      related.textContent = "This project has no overlap within 40 km.";
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
    else document.getElementById("opportunities-heading").focus();
  });
  filter.addEventListener("input", filterProjects);
  back.addEventListener("click", () => {
    showView(previousView);
    if (selectedButton?.isConnected && previousView === "projects") selectedButton.focus();
    else toggle.focus();
  });

  return { renderProjects, showLoadError, openProject };
}
