// Places where the loaded plans have the most close pairs.

export function renderStartHere(hotspots) {
  const region = document.getElementById("start-here");
  const places = document.getElementById("start-here-places");
  places.replaceChildren();
  for (const place of Array.isArray(hotspots) ? hotspots : []) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.src = "hotspots";
    button.textContent = `${place.label} · ${place.pairs} close pairs`;
    button.addEventListener("click", () => {
      document.dispatchEvent(new CustomEvent("gridlock:explore-place", {
        detail: { place, entry: button },
      }));
    });
    places.append(button);
  }
  region.hidden = places.childElementCount === 0;
}
