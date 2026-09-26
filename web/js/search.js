import { createAreaController } from "./area.js";
import { state } from "./state.js";

function validResult(item) {
  return item && ["place", "project", "substation"].includes(item.type)
    && typeof item.label === "string" && item.label.length > 0
    && Number.isFinite(item.lat) && Math.abs(item.lat) <= 90
    && Number.isFinite(item.lon) && Math.abs(item.lon) <= 180;
}

export function setupSearch(filterControl) {
  const form = document.getElementById("search-form");
  const input = document.getElementById("search-input");
  const options = document.getElementById("search-options");
  const searchState = document.getElementById("search-state");
  const selection = document.getElementById("search-selection");
  const exploreButton = document.getElementById("explore-area");
  const status = document.getElementById("status");
  const area = createAreaController(state.map, (message) => {
    delete status.dataset.src;
    status.textContent = message;
  }, filterControl.setArea);
  const choices = new Map();
  let sequence = 0;
  let controller = null;
  let currentQuery = "";
  let currentResults = [];
  let selected = null;

  function showMessage(message, query) {
    searchState.replaceChildren(document.createTextNode(message));
    if (query) {
      const value = document.createElement("span");
      value.dataset.src = "search_query";
      value.textContent = query;
      searchState.append(value);
    }
  }

  function clearSelection() {
    selected = null;
    selection.replaceChildren();
    selection.hidden = true;
    exploreButton.hidden = true;
    area.clear();
  }

  async function search(query) {
    const request = ++sequence;
    if (controller) controller.abort();
    controller = new AbortController();
    currentQuery = "";
    currentResults = [];
    choices.clear();
    options.replaceChildren();
    showMessage("Searching local plans for ", query);
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
        headers: { Accept: "application/json" }, signal: controller.signal,
      });
      if (!response.ok) throw new Error(`Search returned ${response.status}`);
      const results = await response.json();
      if (!Array.isArray(results) || !results.every(validResult)) throw new Error("Invalid search results");
      if (request !== sequence) return null;
      currentQuery = query;
      currentResults = results;
      const labelCounts = new Map();
      for (const result of results) {
        labelCounts.set(result.label, (labelCounts.get(result.label) || 0) + 1);
      }
      for (const result of results) {
        const source = result.ref || `${result.lat}, ${result.lon}`;
        const value = labelCounts.get(result.label) > 1
          ? `${result.label} (${result.type}: ${source})` : result.label;
        choices.set(value, result);
        const option = document.createElement("option");
        option.value = value;
        option.label = labelCounts.get(result.label) > 1 ? value : `${result.label} (${result.type})`;
        options.append(option);
      }
      showMessage(results.length ? `${results.length} local matches for ` : "No local matches for ", query);
      return results;
    } catch (error) {
      if (request !== sequence || error.name === "AbortError") return null;
      showMessage("Search unavailable. Check the local server and try again.");
      return null;
    }
  }

  input.addEventListener("input", () => {
    const query = input.value.trim();
    clearSelection();
    if (choices.has(query)) {
      showMessage("Press Enter to center the selected result.");
      return;
    }
    if (query.length < 2) {
      ++sequence;
      if (controller) controller.abort();
      currentQuery = "";
      currentResults = [];
      choices.clear();
      options.replaceChildren();
      showMessage("Enter at least 2 characters to search local plans.");
      return;
    }
    void search(query);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = input.value.trim();
    if (query.length < 2) {
      showMessage("Enter at least 2 characters to search local plans.");
      return;
    }
    let result = choices.get(query);
    if (!result) {
      const results = currentQuery === query ? currentResults : await search(query);
      if (input.value.trim() !== query || !results) return;
      result = results[0];
    }
    if (!result) {
      showMessage("No local matches for ", query);
      return;
    }
    selected = result;
    area.clear();
    const label = document.createElement("span");
    label.dataset.src = "label";
    label.textContent = result.label;
    selection.replaceChildren(document.createTextNode(`${result.type}: `), label);
    selection.hidden = false;
    exploreButton.hidden = false;
    // A user's destination takes precedence over a pending initial overview fit.
    state.initialMapFitted = true;
    state.map.flyTo([result.lat, result.lon], 11, {
      animate: !matchMedia("(prefers-reduced-motion: reduce)").matches,
    });
    delete status.dataset.src;
    status.textContent = "Map centered on search result. Explore this area to mark 40 km.";
  });

  exploreButton.addEventListener("click", () => {
    if (selected) area.explore(selected, { entry: exploreButton });
  });

  return { refreshTheme: area.refreshTheme };
}
