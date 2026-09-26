const FILTER_KEYS = ["utility", "voltage_kv", "year_min", "year_max", "project_type", "band", "cross_state"];
const URL_KEYS = [...FILTER_KEYS, "year", "area"];
const TYPES = new Set(["new_line", "rebuild_line", "reconductor", "new_substation", "substation_upgrade", "equipment", "other"]);
const BANDS = new Set(["touching", "lt_1_6km", "lt_8km", "lt_40km"]);

function emptyFilters() {
  return { utility: [], voltage_kv: "", year_min: "", year_max: "", project_type: "", band: "", cross_state: "" };
}

function validYear(value) {
  return /^(?:19|20|21)\d{2}$|^2200$/.test(value) && Number(value) >= 1900;
}

function validArea(value) {
  const parts = value.split(",");
  if (parts.length !== 2 || parts.some((part) => !/^-?\d+(?:\.\d+)?$/.test(part))) return false;
  const [lat, lon] = parts.map(Number);
  return Number.isFinite(lat) && Number.isFinite(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180;
}

function filterQuery(filters) {
  const params = new URLSearchParams();
  for (const utility of filters.utility) params.append("utility", utility);
  for (const key of FILTER_KEYS.slice(1)) {
    if (filters[key]) params.set(key, filters[key]);
  }
  return params;
}

export function setupFilters(onChange) {
  const toggle = document.getElementById("filters-toggle");
  const panel = document.getElementById("filter-panel");
  const warning = document.getElementById("filter-warning");
  const utilities = document.getElementById("filter-utility-options");
  const voltage = document.getElementById("filter-voltage");
  const fields = {
    voltage_kv: voltage,
    year_min: document.getElementById("filter-year-min"),
    year_max: document.getElementById("filter-year-max"),
    project_type: document.getElementById("filter-type"),
    band: document.getElementById("filter-band"),
    cross_state: document.getElementById("filter-cross-state"),
  };
  let knownUtilities = new Set();
  let knownVoltages = new Set();
  let current = emptyFilters();
  let reserved = { year: "", area: "" };
  let ready = false;

  function showWarning(message) {
    warning.textContent = message;
    warning.hidden = !message;
  }

  function readURL() {
    const params = new URLSearchParams(location.search);
    const next = emptyFilters();
    const nextReserved = { year: "", area: "" };
    let invalid = false;
    for (const value of params.getAll("utility")) {
      if (knownUtilities.has(value)) {
        if (!next.utility.includes(value)) next.utility.push(value);
      } else invalid = true;
    }
    const validators = {
      voltage_kv: (value) => knownVoltages.has(value),
      year_min: validYear,
      year_max: validYear,
      project_type: (value) => TYPES.has(value),
      band: (value) => BANDS.has(value),
      cross_state: (value) => value === "true" || value === "false",
      year: validYear,
      area: validArea,
    };
    for (const key of URL_KEYS.slice(1)) {
      const values = params.getAll(key);
      if (values.length === 0) continue;
      if (values.length === 1 && validators[key](values[0])) {
        if (key === "year" || key === "area") nextReserved[key] = values[0];
        else next[key] = values[0];
      } else invalid = true;
    }
    if (next.year_min && next.year_max && Number(next.year_min) > Number(next.year_max)) {
      next.year_min = "";
      next.year_max = "";
      invalid = true;
    }
    return { filters: next, reserved: nextReserved, invalid };
  }

  function writeURL(replace = false) {
    const url = new URL(location.href);
    for (const key of URL_KEYS) url.searchParams.delete(key);
    const active = filterQuery(current);
    for (const [key, value] of active) url.searchParams.append(key, value);
    if (reserved.year) url.searchParams.set("year", reserved.year);
    if (reserved.area) url.searchParams.set("area", reserved.area);
    if (replace) history.replaceState(null, "", url);
    else history.pushState(null, "", url);
  }

  function applyControls() {
    for (const input of utilities.querySelectorAll('input[name="utility"]')) {
      input.checked = current.utility.includes(input.value);
    }
    for (const [key, element] of Object.entries(fields)) element.value = current[key];
    const count = current.utility.length + FILTER_KEYS.slice(1).filter((key) => current[key]).length;
    toggle.textContent = count ? `Filters (${count})` : "Filters";
  }

  function fromControls() {
    const next = emptyFilters();
    next.utility = Array.from(utilities.querySelectorAll('input[name="utility"]:checked'), (input) => input.value);
    for (const [key, element] of Object.entries(fields)) next[key] = element.value;
    return next;
  }

  function onControlsChanged() {
    if (!ready) return;
    const next = fromControls();
    if ((next.year_min && !validYear(next.year_min)) || (next.year_max && !validYear(next.year_max))
      || (next.year_min && next.year_max && Number(next.year_min) > Number(next.year_max))) {
      showWarning("Enter an in-service range from 1900 to 2200, with the start before the end.");
      return;
    }
    showWarning("");
    if (filterQuery(next).toString() === filterQuery(current).toString()) return;
    current = next;
    applyControls();
    writeURL();
    onChange();
  }

  function clear() {
    current = emptyFilters();
    applyControls();
    showWarning("");
    writeURL();
    onChange();
  }

  function restoreFromHistory() {
    if (!ready) return;
    const previous = filterQuery(current).toString();
    const result = readURL();
    current = result.filters;
    reserved = result.reserved;
    applyControls();
    showWarning(result.invalid ? "Invalid link filters were ignored; showing available public-plan results." : "");
    if (result.invalid) writeURL(true);
    if (filterQuery(current).toString() !== previous) onChange();
  }

  function hydrate(features) {
    knownUtilities = new Set(features.map((feature) => feature.properties.utility));
    knownVoltages = new Set(features.flatMap((feature) => feature.properties.voltage_kv.map(String)));
    utilities.replaceChildren();
    voltage.replaceChildren(voltage.options[0]);
    for (const name of [...knownUtilities].sort()) {
      const label = document.createElement("label");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.name = "utility";
      input.value = name;
      const caption = document.createElement("span");
      caption.dataset.src = "utility";
      caption.textContent = name;
      label.append(input, caption);
      utilities.append(label);
    }
    for (const value of [...knownVoltages].sort((a, b) => Number(a) - Number(b))) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = `${value} kV`;
      voltage.append(option);
    }
    const result = readURL();
    current = result.filters;
    reserved = result.reserved;
    ready = true;
    toggle.disabled = false;
    applyControls();
    showWarning(result.invalid ? "Invalid link filters were ignored; showing available public-plan results." : "");
    if (result.invalid) writeURL(true);
  }

  toggle.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
    toggle.setAttribute("aria-expanded", String(!panel.hidden));
    if (!panel.hidden && matchMedia("(max-width: 700px)").matches) {
      const sheet = document.querySelector(".panel");
      sheet.classList.add("expanded");
      const sheetButton = document.getElementById("sheet-toggle");
      sheetButton.setAttribute("aria-expanded", "true");
      sheetButton.textContent = "Collapse opportunities";
      window.requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
    }
  });
  panel.addEventListener("change", onControlsChanged);
  document.getElementById("filter-clear").addEventListener("click", clear);
  window.addEventListener("popstate", restoreFromHistory);
  return { hydrate, clear, hasActive: () => filterQuery(current).toString() !== "", query: () => filterQuery(current) };
}
