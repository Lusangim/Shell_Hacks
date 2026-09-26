(() => {
  let theme = null;
  try { theme = localStorage.getItem("gridlock-theme"); } catch (_error) { theme = null; }
  if (theme !== "light" && theme !== "dark") {
    theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.dataset.theme = theme;
  // Reserve the requested sheet layout before paint; area.js still validates all area state.
  if (new URLSearchParams(location.search).has("area")) {
    document.documentElement.dataset.areaLayout = "pending";
  }
})();
