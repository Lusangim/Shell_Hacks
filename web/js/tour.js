import { tourSteps, tourWords } from "./tour-content.js";

function visible(node) {
  if (!node || !node.getClientRects().length || node.closest("[hidden]")) return false;
  // Content of a closed section keeps a stale box in Chrome: only its summary counts as shown.
  const closed = node.parentElement?.closest("details:not([open])");
  if (closed && !closed.querySelector(":scope > summary")?.contains(node)) return false;
  return getComputedStyle(node).visibility !== "hidden";
}

export function setupTour() {
  const launch = document.getElementById("tour-launch");
  const invitation = document.getElementById("tour-invitation");
  const invitationBox = document.getElementById("tour-invitation-box");
  const dismiss = document.getElementById("tour-dismiss");
  launch.textContent = tourWords.launch;
  invitation.setAttribute("aria-label", tourWords.invitation);
  const invitationLabel = document.createElement("span");
  invitationLabel.className = "tour-invitation-long";
  invitationLabel.textContent = tourWords.invitation;
  const invitationShort = document.createElement("span");
  invitationShort.className = "tour-invitation-short";
  invitationShort.textContent = tourWords.shortInvitation;
  invitation.replaceChildren(invitationLabel, invitationShort);
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
  // The tour lives in the top bar on wide screens and behind ⋮ on narrower ones; focus returns to whichever shows.
  const menuEntry = () => {
    const more = document.getElementById("more-toggle");
    return more.getClientRects().length ? more : launch;
  };
  dismiss.addEventListener("click", () => { remember(); menuEntry().focus(); });

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
    menuEntry().focus();
  }

  function revealTarget(selector) {
    const node = document.querySelector(selector);
    if (!node) return false;
    for (let parent = node.parentElement; parent; parent = parent.parentElement) {
      if (parent.tagName === "DETAILS" && !parent.open) parent.open = true;
    }
    if (node.closest("#brief-panel") && !document.querySelector(".detail-pane").classList.contains("brief-open")) {
      const open = document.getElementById("open-brief");
      if (visible(open)) open.click();
    }
    return visible(node);
  }

  // Observe the real detail request, with a bounded wait when it fails or is removed.
  function waitForTarget(selector) {
    if (revealTarget(selector)) return Promise.resolve();
    return new Promise((resolve) => {
      const stop = () => { observer.disconnect(); clearTimeout(timer); pendingCleanup = null; resolve(); };
      const observer = new MutationObserver(() => {
        if (revealTarget(selector)) stop();
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
    } else {
      // Beside what the step explains: below, above, left, then right of the target. The first spot on screen
      // that leaves the target uncovered wins; otherwise the spot that covers the least of it.
      const gap = 12;
      const onScreen = ([x, y]) => [Math.min(Math.max(margin, x), innerWidth - box.width - margin),
        Math.min(Math.max(margin, y), innerHeight - box.height - margin)];
      const spots = [
        [rect.right - box.width, rect.bottom + gap], [rect.left, rect.bottom + gap],
        [rect.left, rect.top - box.height - gap], [rect.right - box.width, rect.top - box.height - gap],
        [rect.left - box.width - gap, rect.top], [rect.right + gap, rect.top],
      ].map(onScreen);
      const covered = ([x, y]) => Math.max(0, Math.min(x + box.width, rect.right) - Math.max(x, rect.left))
        * Math.max(0, Math.min(y + box.height, rect.bottom) - Math.max(y, rect.top));
      [left, top] = spots.reduce((best, spot) => (covered(spot) < covered(best) ? spot : best));
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
      if (step.id !== "brief" && document.querySelector(".detail-pane").classList.contains("brief-open")) {
        document.getElementById("brief-back").click();
      }
      if (step.id === "timeline" && matchMedia("(max-width: 1099px)").matches && visible(document.getElementById("overlap-back"))) {
        document.getElementById("overlap-back").click();
      }
      if (step.id === "timeline" && matchMedia("(max-width: 700px)").matches) {
        const sheet = document.getElementById("sheet-toggle");
        if (sheet.getAttribute("aria-expanded") === "true") sheet.click();
      }
      if (step.prepare === "list") {
        if (visible(document.getElementById("overlap-back"))) document.getElementById("overlap-back").click();
        const sheet = document.getElementById("sheet-toggle");
        if (visible(sheet) && sheet.getAttribute("aria-expanded") === "false") sheet.click();
      }
      if (step.prepare === "pair" && !visible(document.querySelector(step.target))) {
        const pair = document.querySelector(".overlap-button");
        if (document.getElementById("overlap-detail").hidden && visible(pair)) pair.click();
        await waitForTarget(step.target);
      }
      if (step.prepare === "export") {
        const more = document.getElementById("more-toggle");
        if (more.getAttribute("aria-expanded") !== "true") more.click();

      }
      if (!active || ownRevision !== revision) return;
      revealTarget(step.target);
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
      // The pair pane may still be settling (a section opening, the pane returning to its top): look again
      // shortly, bring the target back into view and place the card beside it.
      setTimeout(() => {
        if (!active || target !== node) return;
        const settled = node.getBoundingClientRect();
        if (settled.top < 0 || settled.bottom > innerHeight) {
          node.scrollIntoView({ block: settled.height > innerHeight * 0.6 ? "start" : "center", behavior: "instant" });
        }
        positionCard();
      }, 350);
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
