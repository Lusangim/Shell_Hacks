import { state } from "./state.js";

const KEY = "gridlock-tracker-v1";
const PAIR_ID = /^(?:desc-p[1-9][0-9]*|sertp-p[1-9][0-9]*-[0-9a-f]{6}(?:-[2-9][0-9]*)?)__(?:desc-p[1-9][0-9]*|sertp-p[1-9][0-9]*-[0-9a-f]{6}(?:-[2-9][0-9]*)?)$/;
const STATUSES = ["Not started", "Contacted", "Meeting set", "Coordinating", "Not relevant"];
const STORAGE_MESSAGE = "Tracking needs browser storage, which is off in this browser";

function readEntries() {
  try {
    const stored = localStorage.getItem(KEY);
    let raw;
    try { raw = JSON.parse(stored ?? "{}"); }
    catch (_error) { raw = {}; }
    const entries = {};
    if (raw && typeof raw === "object" && !Array.isArray(raw)) {
      for (const [id, entry] of Object.entries(raw)) {
        if (PAIR_ID.test(id) && entry && STATUSES.slice(1).includes(entry.status)) {
          entries[id] = {
            status: entry.status,
            note: typeof entry.note === "string" ? entry.note.slice(0, 300) : "",
            updated: typeof entry.updated === "string" ? entry.updated : "",
          };
        }
      }
    }
    return entries;
  } catch (_error) {
    return null;
  }
}

function writeEntries(entries) {
  try {
    localStorage.setItem(KEY, JSON.stringify(entries));
    return true;
  } catch (_error) {
    return false;
  }
}

export function trackedPair(id) {
  return PAIR_ID.test(id ?? "") ? readEntries()?.[id] ?? null : null;
}

export function coordinationText(id) {
  const entry = trackedPair(id);
  return entry ? [entry.status, entry.note].filter(Boolean).join("\n") : "";
}

function escapeFormula(value) {
  return /^[=+\-@\t\r\n]/.test(value) ? `'${value}` : value;
}

// RFC 4180 fields, including doubled quotes and line breaks inside quoted fields.
function parseCsv(source) {
  const rows = [];
  let row = [], field = "", quoted = false;
  const start = source.charCodeAt(0) === 0xfeff ? 1 : 0;
  for (let index = start; index < source.length; index += 1) {
    const char = source[index];
    if (quoted) {
      if (char === '"' && source[index + 1] === '"') { field += '"'; index += 1; }
      else if (char === '"') quoted = false;
      else field += char;
    } else if (char === '"') quoted = true;
    else if (char === ",") { row.push(field); field = ""; }
    else if (char === "\r" || char === "\n") {
      row.push(field);
      rows.push(row);
      row = []; field = "";
      if (char === "\r" && source[index + 1] === "\n") index += 1;
    } else field += char;
  }
  if (quoted) throw new Error("Unclosed CSV field");
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

function writeCsv(rows) {
  const encode = (value) => /[",\r\n]/.test(value) ? `"${value.replaceAll('"', '""')}"` : value;
  return `\ufeff${rows.map((row) => row.map(encode).join(",")).join("\r\n")}\r\n`;
}

export async function addTrackingToCsv(blob) {
  const entries = readEntries();
  if (!entries || !Object.keys(entries).length) return blob;
  const rows = parseCsv(await blob.text());
  const [header] = rows;
  if (!header) return blob;
  const idColumn = header.indexOf("Overlap ID");
  const statusColumn = header.indexOf("Coordination status");
  const noteColumn = header.indexOf("Notes");
  if ([idColumn, statusColumn, noteColumn].includes(-1)) throw new Error("Missing CSV tracker column");
  let changed = false;
  for (const row of rows.slice(1)) {
    const entry = entries[row[idColumn]];
    if (!entry) continue;
    row[statusColumn] = entry.status;
    row[noteColumn] = escapeFormula(entry.note);
    changed = true;
  }
  return changed ? new Blob([writeCsv(rows)], { type: "text/csv;charset=utf-8" }) : blob;
}

function decorateRows() {
  const entries = readEntries() ?? {};
  for (const row of document.querySelectorAll("#overlap-list [data-overlap-id]")) {
    row.querySelector(".tracker-chip")?.remove();
    const entry = entries[row.dataset.overlapId];
    if (!entry) continue;
    const chip = document.createElement("span");
    chip.className = "tracker-chip";
    chip.textContent = entry.status;
    // The row's number line (distance, years) is visible in every layout, so the status sits with it.
    (row.querySelector(".row-metric") ?? row.querySelector(".overlap-button") ?? row).append(" ", chip);
  }
}

export function setupTracker() {
  const widget = document.getElementById("pair-tracker");
  const detail = document.getElementById("overlap-detail");
  const detailState = document.getElementById("overlap-state");
  const select = document.getElementById("tracker-status");
  const notes = document.getElementById("tracker-notes");
  const saveState = document.getElementById("tracker-save-state");
  let displayedId = null;
  let timer = null;

  function unavailable() {
    widget.replaceChildren(document.createTextNode(STORAGE_MESSAGE));
    widget.hidden = detail.hidden;
  }

  function render() {
    if (timer && (detail.hidden || displayedId !== state.selectedOverlapId)) save();
    if (detail.hidden || !PAIR_ID.test(state.selectedOverlapId ?? "")) {
      widget.hidden = true;
      displayedId = null;
      return;
    }
    if (readEntries() === null) { unavailable(); return; }
    const id = state.selectedOverlapId;
    widget.hidden = false;
    if (id === displayedId) return;
    displayedId = id;
    const entry = trackedPair(id);
    select.value = entry?.status ?? "Not started";
    notes.value = entry?.note ?? "";
    saveState.textContent = "";
  }

  function save() {
    clearTimeout(timer);
    timer = null;
    const id = displayedId;
    if (!PAIR_ID.test(id ?? "")) return;
    const entries = readEntries();
    if (!entries) { unavailable(); return; }
    const status = select.value;
    if (!STATUSES.includes(status)) return;
    if (status === "Not started") {
      delete entries[id];
      notes.value = "";
    } else entries[id] = { status, note: notes.value.slice(0, 300), updated: new Date().toISOString() };
    if (!writeEntries(entries)) { unavailable(); return; }
    saveState.textContent = "Saved";
    decorateRows();
  }

  select.addEventListener("change", save);
  notes.addEventListener("input", () => {
    saveState.textContent = "";
    clearTimeout(timer);
    timer = setTimeout(save, 250);
  });
  notes.addEventListener("change", save);
  document.addEventListener("gridlock:list-rendered", decorateRows);
  window.addEventListener("hashchange", () => queueMicrotask(render));
  window.addEventListener("popstate", () => queueMicrotask(render));
  new MutationObserver(render).observe(detailState, { childList: true, characterData: true, subtree: true });
  new MutationObserver(render).observe(detail, { attributes: true, attributeFilter: ["hidden"] });
  render();
}
