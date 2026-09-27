// Disclosures and pane layout only; feature controllers retain their original controls.
export function setupShell(overlapView) {
  const more = document.getElementById("more-toggle");
  const menu = document.getElementById("more-menu");
  const filters = document.getElementById("filters-toggle");
  const filterPanel = document.getElementById("filter-panel");
  const impactCard = document.getElementById("impact-card");
  const impactDisclosure = impactCard.querySelector("details");
  const setMore = (open, restore = false) => {
    menu.hidden = !open;
    more.setAttribute("aria-expanded", String(open));
    if (restore) more.focus();
  };
  more.addEventListener("click", () => {
    if (!filterPanel.hidden) filters.click();
    setMore(menu.hidden);
  });
  filters.addEventListener("click", () => { if (!filterPanel.hidden) setMore(false); });
  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || document.querySelector(".tour-card:not([hidden])")) return;
    if (impactDisclosure.open && impactCard.contains(event.target)) {
      impactDisclosure.open = false;
      impactDisclosure.querySelector("summary").focus();
      event.preventDefault();
      event.stopImmediatePropagation();
      return;
    }
    if (!menu.hidden) { setMore(false, true); event.preventDefault(); event.stopImmediatePropagation(); }
    else if (!filterPanel.hidden) { filters.click(); filters.focus(); event.preventDefault(); event.stopImmediatePropagation(); }
  }, true);
  document.addEventListener("pointerdown", (event) => {
    if (!impactCard.contains(event.target)) impactDisclosure.open = false;
    if (!menu.hidden && !menu.contains(event.target) && !more.contains(event.target)) setMore(false);
    if (!filterPanel.hidden && !filterPanel.contains(event.target) && !filters.contains(event.target)) filters.click();
  });
  // Programmatic focus of a retained control reveals its containing disclosure.
  menu.addEventListener("focusin", () => setMore(true));
  document.getElementById("search-form").addEventListener("submit", () => {
    if (matchMedia("(max-width: 1099px)").matches && !document.querySelector(".detail-pane").hidden) {
      overlapView.close({ push: true });
    }
  });
  document.addEventListener("focusin", (event) => {
    if (!impactCard.contains(event.target)) impactDisclosure.open = false;
    if (!menu.hidden && !menu.contains(event.target) && event.target !== more && !event.target.closest(".tour-card")) setMore(false);
    if (!filterPanel.hidden && !filterPanel.contains(event.target) && event.target !== filters && event.target !== more && !event.target.closest(".tour-card")) filters.click();
    const pane = document.querySelector(".detail-pane");
    const coveredMap = matchMedia("(max-width: 1099px)").matches && event.target.closest(".map-region");
    const coveredList = matchMedia("(max-width: 700px)").matches && event.target.closest(".panel");
    if (!pane.hidden && (coveredMap || coveredList)) overlapView.close({ push: true });
  });
  document.getElementById("projects-toggle").addEventListener("click", () => setMore(false));
  document.getElementById("tour-launch").addEventListener("click", () => setMore(false));
}
