const RADIUS_M = 40000;

function token(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function createAreaController(map, announce) {
  const output = document.getElementById("area-selection");
  let circle = null;

  function clear() {
    if (circle) map.removeLayer(circle);
    circle = null;
    output.hidden = true;
    output.replaceChildren();
  }

  function explore(result) {
    clear();
    circle = L.circle([result.lat, result.lon], {
      radius: RADIUS_M,
      color: token("--ink"),
      weight: 2,
      dashArray: "8 5",
      fillColor: token("--map-state"),
      fillOpacity: 0.08,
      interactive: false,
    }).addTo(map);
    const path = circle.getElement();
    path.dataset.testid = "area-circle";
    path.dataset.radiusM = String(circle.getRadius());
    path.setAttribute("aria-hidden", "true");
    path.setAttribute("tabindex", "-1");

    const label = document.createElement("span");
    label.dataset.src = "label";
    label.textContent = result.label;
    output.replaceChildren(document.createTextNode("40 km around "), label);
    output.hidden = false;
    announce("40 km area selected.");
  }

  function refreshTheme() {
    if (circle) circle.setStyle({ color: token("--ink"), fillColor: token("--map-state") });
  }

  return { clear, explore, refreshTheme };
}
