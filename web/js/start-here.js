// Places where the loaded plans have the most close pairs.

// A short chip ("Rincon · 6") keeps the row to one line; the full place name stays in the accessible name.
export function shortPlace(label) {
  return String(label ?? "").replace(/\s+(city|town|CDP|village)$/i, "");
}

export function renderStartHere(hotspots) {
  const region = document.getElementById("start-here");
  const places = document.getElementById("start-here-places");
  places.replaceChildren();
  for (const place of Array.isArray(hotspots) ? hotspots : []) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.src = "hotspots";
    button.textContent = `${shortPlace(place.label)} · ${place.pairs}`;
    button.title = `${place.label}: ${place.pairs} close pairs`;
    button.setAttribute("aria-label", `${place.label}, ${place.pairs} close pairs`);
    button.addEventListener("click", () => {
      document.dispatchEvent(new CustomEvent("gridlock:explore-place", {
        detail: { place, entry: button },
      }));
    });
    places.append(button);
  }
  region.hidden = places.childElementCount === 0;
}
