function loadScript(url) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    const timer = setTimeout(() => finish(new Error("Map script timed out")), 10000);
    function finish(error) {
      clearTimeout(timer);
      script.onload = null;
      script.onerror = null;
      if (error) { script.remove(); reject(error); }
      else resolve();
    }
    script.src = url;
    script.onload = () => finish();
    script.onerror = () => finish(new Error("Map script unavailable"));
    document.head.append(script);
  });
}

export function isolateMapControls() {
  document.querySelectorAll(".panel, .timeline, .map-note, .map-pair-open, .basemap-controls, .basemap-status, .leaflet-control").forEach((element) => {
    L.DomEvent.disableScrollPropagation(element);
    L.DomEvent.disableClickPropagation(element);
  });
}

function createControls() {
  const region = document.querySelector(".map-region");
  const status = document.createElement("p");
  status.className = "basemap-status";
  status.dataset.testid = "basemap-status";
  status.setAttribute("aria-live", "polite");
  status.textContent = "Loading offline map.";
  const group = document.createElement("div");
  group.className = "basemap-controls";
  group.setAttribute("role", "group");
  group.setAttribute("aria-label", "Base map");
  group.hidden = true;
  const buttons = ["Map", "Google Maps", "Satellite"].map((name) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = name;
    button.setAttribute("aria-pressed", String(name === "Map"));
    group.append(button);
    return button;
  });
  region.append(group, status);
  isolateMapControls();
  return { status, group, buttons };
}

export function initializeBasemap(map) {
  const ui = createControls();
  const model = { config: null, offline: null, google: null, request: 0, flavor: null, archive: null, googleReady: null, wantsGoogle: false };
  map.attributionControl.setPrefix(false);
  map.attributionControl.addAttribution('© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a> · <a href="https://protomaps.com">Protomaps</a>');

  function fallback(message = "Outline map: offline street map unavailable.") {
    if (model.offline) map.removeLayer(model.offline);
    model.offline = null;
    map.getContainer().classList.remove("vector-basemap");
    ui.status.textContent = message;
  }

  function offlineSelection(message) {
    model.wantsGoogle = false;
    model.request += 1;
    if (model.google) map.removeLayer(model.google);
    model.google = null;
    ui.buttons.forEach((button, index) => button.setAttribute("aria-pressed", String(index === 0)));
    ui.status.textContent = message || (model.offline ? "Offline street map" : "Outline map: offline street map unavailable.");
  }

  function refreshTheme() {
    const flavor = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
    if (!model.archive || model.flavor === flavor) return;
    model.flavor = flavor;
    if (model.offline) map.removeLayer(model.offline);
    model.offline = protomapsL.leafletLayer({
      url: model.archive, flavor, maxDataZoom: 13, maxZoom: 17, noWrap: true,
      attribution: "", pane: "tilePane",
    }).addTo(map);
    map.getContainer().classList.add("vector-basemap");
  }

  async function loadOffline() {
    try {
      await loadScript("/web/vendor/protomaps-leaflet/protomaps-leaflet.js");
      const archive = new protomapsL.PmtilesSource("/basemap/gasc.pmtiles").p;
      await archive.getHeader();
      model.archive = {
        async getZxy(...args) {
          try { return await archive.getZxy(...args); }
          catch (error) {
            if (error.name !== "AbortError") fallback();
            // Protomaps logs ordinary tile errors; expose failure in the status instead.
            throw new DOMException("Offline map unavailable", "AbortError");
          }
        },
      };
      refreshTheme();
      ui.status.textContent = "Offline street map";
    } catch (_error) { fallback(); }
  }

  async function googleSelection(index) {
    if (!model.config?.google_enabled || !model.config.google_key || !navigator.onLine) return;
    model.wantsGoogle = true;
    const ownRequest = ++model.request;
    ui.status.textContent = "Loading Google map.";
    try {
      if (!model.googleReady) {
        const ready = (async () => {
          await loadScript("/web/vendor/googlemutant/Leaflet.GoogleMutant.js");
          if (!model.wantsGoogle || !navigator.onLine) throw new Error("Map selection changed");
          if (window.google?.maps?.Map) return;
          const url = new URL("https://maps.googleapis.com/maps/api/js");
          url.searchParams.set("key", model.config.google_key);
          url.searchParams.set("v", "weekly");
          url.searchParams.set("loading", "async");
          await loadScript(url.href);
          if (!window.google?.maps?.Map) throw new Error("Google map unavailable");
        })();
        model.googleReady = ready;
        // A cancelled initializer can fail after another selection starts loading.
        void ready.catch(() => {
          if (model.googleReady === ready) model.googleReady = null;
        });
      }
      await model.googleReady;
      if (ownRequest !== model.request) return;
      if (!navigator.onLine) { offlineSelection(); return; }
      if (model.google) map.removeLayer(model.google);
      const layer = L.gridLayer.googleMutant({ type: index === 2 ? "hybrid" : "roadmap", maxZoom: 17 });
      model.google = layer;
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => reject(new Error("Google map timed out")), 10000);
        layer.once("tileload", () => { clearTimeout(timeout); resolve(); });
        layer.once("tileerror", () => { clearTimeout(timeout); reject(new Error("Google tiles unavailable")); });
        layer.addTo(map);
      });
      if (ownRequest !== model.request) return;
      ui.buttons.forEach((button, position) => button.setAttribute("aria-pressed", String(position === index)));
      ui.status.textContent = index === 2 ? "Satellite map" : "Google Maps";
    } catch (_error) {
      if (ownRequest === model.request) {
        model.googleReady = null;
        offlineSelection("Google map unavailable. Showing offline map.");
      }
    }
  }

  function onlineChanged() {
    ui.group.hidden = !(model.config?.google_enabled && model.config.google_key && navigator.onLine);
    if (!navigator.onLine) offlineSelection();
  }
  ui.buttons.forEach((button, index) => button.addEventListener("click", () => {
    if (index === 0) offlineSelection();
    else void googleSelection(index);
  }));
  window.addEventListener("online", onlineChanged);
  window.addEventListener("offline", onlineChanged);
  window.gm_authFailure = () => offlineSelection("Google map unavailable. Showing offline map.");
  void (async () => {
    try {
      const response = await fetch("/api/map-config", { signal: AbortSignal.timeout(10000) });
      if (!response.ok) throw new Error("Map settings unavailable");
      model.config = await response.json();
      onlineChanged();
      if (model.config.offline_available) await loadOffline();
      else fallback();
    } catch (_error) { fallback("Outline map: map settings unavailable."); }
  })();
  return { refreshTheme };
}
