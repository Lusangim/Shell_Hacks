// How a project's location is drawn, shared by the map, the list, tooltips and details.
const UTILITY_TOKENS = new Map([
  ["Dominion Energy SC", "--dominion"],
  ["Georgia Power", "--georgia-power"],
  ["MEAG Power", "--meag-power"],
  ["Georgia Transmission Corp.", "--gtc"],
  ["Dalton Utilities", "--minor"],
  ["Georgia ITS (joint)", "--minor"],
]);

export function utilityToken(properties) {
  return UTILITY_TOKENS.get(properties?.utility) || "--minor";
}

// "town": only a Census town centre matched; "approximate"; "exact".
export function locationLook(properties) {
  if (properties?.town_only === true) return "town";
  return properties?.accuracy === "approximate" ? "approximate" : "exact";
}

export function accuracyText(properties) {
  if (properties?.town_only === true) return "Town-level location";
  const accuracy = properties?.accuracy ?? "unknown";
  return `${accuracy.charAt(0).toUpperCase()}${accuracy.slice(1)} location`;
}

// A short line sample in the utility colour, drawn the way the map draws this project.
export function swatchFor(properties) {
  const swatch = document.createElement("span");
  swatch.className = "swatch";
  swatch.dataset.look = locationLook(properties);
  swatch.style.setProperty("--swatch", `var(${utilityToken(properties)})`);
  swatch.setAttribute("aria-hidden", "true");
  return swatch;
}

// Years left before the earlier project's in-service year; null when either year is unknown.
export function coordinateText(aYear, bYear, now = new Date()) {
  if (!Number.isInteger(aYear) || !Number.isInteger(bYear)) return null;
  const years = Math.max(0, Math.min(aYear, bYear) - now.getFullYear());
  if (years === 0) return "Coordinate now";
  return years === 1 ? "1 year to coordinate" : `${years} years to coordinate`;
}

export function coordinateTag(aYear, bYear, className = "coordinate-tag") {
  const value = coordinateText(aYear, bYear);
  if (!value) return null;
  const tag = document.createElement("span");
  tag.className = className;
  tag.textContent = value;
  return tag;
}

// An ordered four-bar glyph: more filled bars means closer. Text always accompanies it.
const BAND_BARS = { touching: 4, lt_1_6km: 3, lt_8km: 2, lt_40km: 1 };

export function bandGlyph(band) {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("class", "band-glyph");
  svg.setAttribute("viewBox", "0 0 14 12");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  const filled = BAND_BARS[band] ?? 0;
  [[0.5, 8.5, 3], [4.2, 6, 5.5], [7.9, 3.5, 8], [11.5, 0.5, 11]].forEach(([x, y, height], index) => {
    const bar = document.createElementNS(ns, "rect");
    bar.setAttribute("x", String(x));
    bar.setAttribute("y", String(y));
    bar.setAttribute("width", "2");
    bar.setAttribute("height", String(height));
    if (index < filled) bar.setAttribute("class", "on");
    svg.append(bar);
  });
  return svg;
}
