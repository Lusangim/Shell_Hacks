import { tourSteps, tourWords } from "./tour-content.js";

function visible(node) {
  return Boolean(node && node.getClientRects().length && !node.closest("[hidden]")
    && getComputedStyle(node).visibility !== "hidden");
}

export function setupTour() {
  const launch = document.getElementById("tour-launch");
  const invitation = document.getElementById("tour-invitation");
  const invitationBox = document.getElementById("tour-invitation-box");
  const dismiss = document.getElementById("tour-dismiss");
  launch.textContent = tourWords.launch;
  invitation.textContent = tourWords.invitation;
  const dismissIcon = document.createElement("span");
  dismissIcon.className = "icon";
  dismissIcon.dataset.icon = "x";
  dismissIcon.setAttribute("aria-hidden", "true");
  dismiss.replaceChildren(dismissIcon);
  dismiss.setAttribute("aria-label", tourWords.dismiss);
  let dismissed = false;
  try { dismissed = localStorage.getItem("gridlock-tour-dismissed") === "yes"; }
  catch (_error) { dismissed = false; }
  invitationBox.hidden = dismiss.hidden = dismissed;

  function remember() {
    invitationBox.hidden = dismiss.hidden = true;
    try { localStorage.setItem("gridlock-tour-dismissed", "yes"); }
    catch (_error) { dismissed = true; }
  }
  dismiss.addEventListener("click", () => { remember(); document.getElementById("more-toggle").focus(); });

  const card = document.createElement("section");
  card.id = "tour-card";
  card.className = "tour-card";
  card.hidden = true;
  card.tabIndex = -1;
  card.setAttribute("role", "dialog");
  card.setAttribute("aria-label", tourWords.label);
  card.setAttribute("aria-describedby", "tour-count tour-heading tour-body");
  const count = document.createElement("p");
  count.id = "tour-count";
  const progress = document.createElement("div");
  progress.className = "tour-progress";
  progress.setAttribute("aria-hidden", "true");
  const progressFill = document.createElement("span");
  progress.append(progressFill);
  const heading = document.createElement("h2");
  heading.id = "tour-heading";
  const body = document.createElement("p");
  body.id = "tour-body";
  const controls = document.createElement("div");
  controls.className = "tour-controls";
  const buttons = [tourWords.back, tourWords.next, tourWords.skip].map((word) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = word;
    controls.append(button);
    return button;
  });
  const [back, next, skip] = buttons;
  next.classList.add("btn-primary");
  skip.classList.add("tour-skip");
  card.append(count, progress, heading, body, controls);
  document.querySelector("main").append(card);
  let steps = [];
  let index = -1;
  let active = false;
  let revision = 0;
  let target = null;
  let openedLegend = false;
  let pendingCleanup = null;

  function clearTarget() {
    target?.classList.remove("tour-target");
    target = null;
  }

  function finish() {
    active = false;
    revision += 1;
    pendingCleanup?.();
    clearTarget();
    card.hidden = true;
    if (openedLegend) document.querySelector(".legend").open = false;
    openedLegend = false;
    remember();
    document.getElementById("more-toggle").focus();
  }

  // Observe the real detail request, with a bounded wait when it fails or is removed.
  function waitForTarget(selector) {
    if (visible(document.querySelector(selector))) return Promise.resolve();
    return new Promise((resolve) => {
      const stop = () => { observer.disconnect(); clearTimeout(timer); pendingCleanup = null; resolve(); };
      const observer = new MutationObserver(() => {
        if (visible(document.querySelector(selector))) stop();
      });
      const timer = setTimeout(stop, 2000);
      pendingCleanup = stop;
      observer.observe(document.querySelector("main"), { childList: true, subtree: true, attributes: true });
    });
  }

  // Phones flip the card above or below the target; wider screens place it beside what it explains.
  function positionCard() {
    if (!target || card.hidden) return;
    const rect = target.getBoundingClientRect();
    card.dataset.placement = rect.top < innerHeight / 2 ? "bottom" : "top";
    if (matchMedia("(max-width: 700px)").matches) {
      card.style.removeProperty("left");
      card.style.removeProperty("top");
      delete card.dataset.arrow;
      return;
    }
    const margin = 16;
    const panel = document.querySelector(".panel").getBoundingClientRect();
    const box = card.getBoundingClientRect();
    let left = panel.right + margin;
    let top = margin;
    const inPanel = Boolean(target.closest(".panel"));
    if (inPanel) {
      top = rect.top + Math.min(rect.height, 64) / 2 - 36;
    } else if (target.closest(".timeline")) {
      left = Math.max(left, rect.left);
      top = rect.top - box.height - 12;
    } else if (innerWidth >= 1100) {
      left = Math.max(left, innerWidth - box.width - 76);
    }
    left = Math.min(Math.max(margin, left), innerWidth - box.width - margin);
    top = Math.min(Math.max(margin, top), innerHeight - box.height - margin);
    card.style.left = `${left}px`;
    card.style.top = `${top}px`;
    if (inPanel) {
      card.dataset.arrow = "left";
      const pointer = rect.top + Math.min(rect.height, 64) / 2 - top;
      card.style.setProperty("--arrow-y", `${Math.min(Math.max(24, pointer), box.height - 24)}px`);
    } else delete card.dataset.arrow;
  }

  function enter() {
    // Reduced motion shows each step at once; otherwise a short rise explains the change of step.
    if (matchMedia("(prefers-reduced-motion: reduce)").matches || typeof card.animate !== "function") return;
    card.animate([{ opacity: 0, transform: "translateY(6px)" }, { opacity: 1, transform: "none" }],
      { duration: 180, easing: "cubic-bezier(0.23, 1, 0.32, 1)" });
  }

  async function show(candidate, direction = 1) {
    const ownRevision = ++revision;
    pendingCleanup?.();
    clearTarget();
    while (active && candidate >= 0 && candidate < steps.length) {
      const step = steps[candidate];
      if (step.prepare === "list") {
        if (visible(document.getElementById("overlap-back"))) document.getElementById("overlap-back").click();
        const sheet = document.getElementById("sheet-toggle");
        if (visible(sheet) && sheet.getAttribute("aria-expanded") === "false") sheet.click();
      }
      if (step.prepare === "pair" && !visible(document.querySelector(step.target))) {
        const pair = document.querySelector(".overlap-button");
        if (visible(pair)) pair.click();
        await waitForTarget(step.target);
      }
      if (step.prepare === "export") {
        const more = document.getElementById("more-toggle");
        if (more.getAttribute("aria-expanded") !== "true") more.click();
        const legend = document.querySelector(".legend");
        if (legend && !legend.open) { legend.querySelector("summary").click(); openedLegend = true; }
      }
      if (!active || ownRevision !== revision) return;
      const node = document.querySelector(step.target);
      if (!visible(node)) {
        steps.splice(candidate, 1);
        if (direction < 0) candidate -= 1;
        continue;
      }
      index = candidate;
      target = node;
      target.classList.add("tour-target");
      target.scrollIntoView({ block: "nearest", behavior: "instant" });
      heading.textContent = step.title;
      body.textContent = step.body;
      count.textContent = tourWords.count(index + 1, steps.length);
      progressFill.style.setProperty("--progress", `${Math.round(((index + 1) / steps.length) * 100)}%`);
      back.disabled = index === 0;
      next.textContent = index === steps.length - 1 ? tourWords.finish : tourWords.next;
      card.hidden = false;
      positionCard();
      enter();
      card.focus({ preventScroll: true });
      return;
    }
    finish();
  }

  function start() {
    if (active) { card.focus(); return; }
    // Conditional features participate only when their real controls are available.
    steps = tourSteps.filter((step) => step.prepare || visible(document.querySelector(step.target)));
    active = true;
    remember();
    void show(0);
  }
  launch.addEventListener("click", start);
  invitation.addEventListener("click", start);
  back.addEventListener("click", () => { void show(index - 1, -1); });
  next.addEventListener("click", () => { void show(index + 1); });
  skip.addEventListener("click", finish);
  document.addEventListener("keydown", (event) => {
    if (active && event.key === "Escape") { event.preventDefault(); finish(); }
  });
  window.addEventListener("resize", positionCard);
  document.getElementById("panel-body").addEventListener("scroll", positionCard, { passive: true });
}
