async function getJson(path) {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
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
