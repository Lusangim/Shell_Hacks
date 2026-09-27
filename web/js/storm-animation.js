const DAMAGE = {
  none: { token: "--storm-none", weight: 2, dashArray: "2 5" },
  minor: { token: "--storm-minor", weight: 2, dashArray: "5 5" },
  moderate: { token: "--storm-moderate", weight: 3, dashArray: null },
  severe: { token: "--storm-severe", weight: 4, dashArray: "8 4" },
  failed: { token: "--storm-failed", weight: 5, dashArray: null },
};
const token = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const point = (frame) => [frame.lat, frame.lon];

function damageClass(asset) {
  const { minor, moderate, severe, failed } = asset.damage;
  const chances = { none: Math.max(0, 1 - minor), minor: Math.max(0, minor - moderate),
    moderate: Math.max(0, moderate - severe), severe: Math.max(0, severe - failed), failed };
  return Object.entries(chances).sort((a, b) => b[1] - a[1])[0][0];
}

function mark(layer, testid) {
  const element = layer.getElement();
  if (!element) return;
  element.dataset.testid = testid;
  element.setAttribute("aria-hidden", "true");
  element.setAttribute("tabindex", "-1");
}

function geometry(asset) {
  if (asset.geometry.type === "Point") return [asset.geometry.coordinates[1], asset.geometry.coordinates[0]];
  return asset.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
}

function symbolIcon() {
  const arms = [0, 90, 180, 270].map((angle) =>
    `<path transform="rotate(${angle} 40 40)" d="M40 27 C53 15 66 20 69 29 C63 25 56 28 51 35 C47 40 43 43 40 43"/>`).join("");
  return L.divIcon({ className: "storm-icon", iconSize: [80, 80], iconAnchor: [40, 40],
    html: `<svg class="storm-symbol-art" viewBox="0 0 80 80" aria-hidden="true" xmlns="http://www.w3.org/2000/svg"><circle cx="40" cy="40" r="35" class="storm-cloud-back"/>${arms}<circle cx="40" cy="40" r="8" class="storm-eye"/></svg>` });
}

export function createStormAnimation(map, data, { onFrame, onFinish, onState }) {
  const frames = data.scenario.frames;
  const group = L.layerGroup().addTo(map);
  const track = L.polyline([], { color: token("--storm-track"), weight: 3, dashArray: "8 6", interactive: false }).addTo(group);
  const dots = frames.map((frame) => L.circleMarker(point(frame), { radius: 2, color: token("--storm-track"),
    fillColor: token("--panel"), fillOpacity: .45, weight: 1, interactive: false }).addTo(group));
  const ring = L.circle(point(frames[0]), { radius: 0, color: token("--storm-track"), weight: 2,
    dashArray: "4 4", fillColor: token("--storm-track"), fillOpacity: .07, interactive: false }).addTo(group);
  const eye = L.marker(point(frames[0]), { icon: symbolIcon(), interactive: false, keyboard: false }).addTo(group);
  const assets = data.assets.map((asset) => {
    const location = geometry(asset);
    const style = DAMAGE[damageClass(asset)];
    const layer = asset.geometry.type === "Point"
      ? L.circleMarker(location, { radius: 5, color: token("--storm-none"), fillColor: token("--storm-none"),
        fillOpacity: .45, weight: 2, interactive: false })
      : L.polyline(location, { color: token("--storm-none"), weight: 2, dashArray: "2 5", interactive: false });
    layer.addTo(group);
    mark(layer, "storm-asset");
    return { asset, layer, style, active: false };
  });
  mark(track, "storm-track");
  dots.forEach((dot) => mark(dot, "storm-frame-dot"));
  mark(ring, "storm-rmax");
  mark(eye, "storm-symbol");
  const art = eye.getElement()?.querySelector(".storm-symbol-art");
  const areaCircle = document.querySelector('[data-testid="area-circle"]');
  let raf = null;
  let started = null;
  let elapsed = 0;
  let finished = false;
  let crossed = false;
  let lastIndex = -1;
  const duration = 9500;

  function paint(position, scale = 1, opacity = 1, rotation = 0) {
    const frameIndex = Math.min(frames.length - 1, Math.floor(position));
    const next = Math.min(frames.length - 1, frameIndex + 1);
    const fraction = position - frameIndex;
    const location = [frames[frameIndex].lat + (frames[next].lat - frames[frameIndex].lat) * fraction,
      frames[frameIndex].lon + (frames[next].lon - frames[frameIndex].lon) * fraction];
    eye.setLatLng(location);
    ring.setLatLng(location);
    ring.setRadius((frames[frameIndex].radius_33_ms_km ?? 0) * 1000);
    track.setLatLngs([...frames.slice(0, frameIndex + 1).map(point), location]);
    if (art) {
      art.style.transform = `scale(${scale}) rotate(${-rotation}deg)`;
      art.style.opacity = String(opacity);
    }
    if (frameIndex !== lastIndex) {
      lastIndex = frameIndex;
      dots.forEach((dot, index) => dot.setStyle({ fillOpacity: index === frameIndex ? 1 : .45,
        weight: index === frameIndex ? 2 : 1 }));
      for (const entry of assets) {
        const active = entry.asset.peak_frame <= frameIndex;
        if (entry.active === active) continue;
        entry.active = active;
        const style = active ? entry.style : DAMAGE.none;
        const color = token(style.token);
        entry.layer.setStyle({ color, fillColor: color, weight: style.weight,
          dashArray: style.dashArray, fillOpacity: active ? .8 : .45 });
      }
      onFrame(frameIndex);
      if (!crossed && frames[frameIndex].t_hours >= 0) {
        crossed = true;
        areaCircle?.classList.add("storm-crossing");
      }
    }
  }

  function draw(ms) {
    if (ms < 1500) {
      paint(0, .3 + .7 * ms / 1500, ms / 1500, ms * .08);
    } else if (ms < 8500) {
      const position = (ms - 1500) / 7000 * (frames.length - 1);
      paint(position, 1, 1, ms * .08);
    } else {
      paint(frames.length - 1, 1 - .7 * (ms - 8500) / 1000, 1 - (ms - 8500) / 1000, ms * .08);
    }
  }

  function tick(now) {
    if (started == null) started = now - elapsed;
    elapsed = Math.min(duration, now - started);
    draw(elapsed);
    if (elapsed >= duration) {
      raf = null;
      finished = true;
      onState("finished");
      onFinish();
    } else raf = requestAnimationFrame(tick);
  }

  function pause() {
    if (raf == null) return;
    cancelAnimationFrame(raf);
    raf = null;
    started = null;
    onState("paused");
  }

  function resume() {
    if (raf != null || finished) return;
    onState("playing");
    raf = requestAnimationFrame(tick);
  }

  function replay() {
    pause();
    elapsed = 0;
    started = null;
    finished = false;
    crossed = false;
    areaCircle?.classList.remove("storm-crossing");
    lastIndex = -1;
    assets.forEach((entry) => { entry.active = true; });
    draw(0);
    resume();
  }

  function skip() {
    pause();
    elapsed = duration;
    draw(duration);
    finished = true;
    onState("finished");
    onFinish();
  }

  function scrub(index) {
    pause();
    const bounded = Math.max(0, Math.min(frames.length - 1, index));
    elapsed = 1500 + 7000 * bounded / (frames.length - 1);
    draw(elapsed);
  }

  function clear() {
    if (raf != null) cancelAnimationFrame(raf);
    raf = null;
    areaCircle?.classList.remove("storm-crossing");
    group.remove();
  }

  function refreshTheme() {
    const color = token("--storm-track");
    track.setStyle({ color });
    ring.setStyle({ color, fillColor: color });
    dots.forEach((dot) => dot.setStyle({ color, fillColor: token("--panel") }));
    assets.forEach((entry) => {
      const style = entry.active ? entry.style : DAMAGE.none;
      entry.layer.setStyle({ color: token(style.token), fillColor: token(style.token) });
    });
  }

  draw(0);
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) skip();
  else resume();
  return { pause, resume, replay, skip, scrub, clear, refreshTheme };
}
