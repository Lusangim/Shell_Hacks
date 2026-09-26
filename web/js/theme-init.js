(() => {
  let theme = null;
  try { theme = localStorage.getItem("gridlock-theme"); } catch (_error) { theme = null; }
  if (theme !== "light" && theme !== "dark") {
    theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.dataset.theme = theme;
})();
