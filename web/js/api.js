async function getJson(path, signal) {
  const response = await fetch(path, { headers: { Accept: "application/json" }, signal });
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

export async function loadShellData() {
  const [projects, overlaps, meta, basemap] = await Promise.all([
    getJson("/api/projects"),
    getJson("/api/overlaps"),
    getJson("/api/meta"),
    getJson("/api/basemap"),
  ]);
  return { projects, overlaps, meta, basemap };
}

export async function loadFilteredData(params, signal) {
  const query = params.toString();
  const suffix = query ? `?${query}` : "";
  const [projects, overlaps] = await Promise.all([
    getJson(`/api/projects${suffix}`, signal),
    getJson(`/api/overlaps${suffix}`, signal),
  ]);
  return { projects, overlaps };
}
