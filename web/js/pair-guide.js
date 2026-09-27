// Step 3 guidance around a pair's detail: an at-a-glance summary, section headings with a
// one-line hint each, and the section nav in the sticky bar. Presentation only: every value
// shown is the pair's own field, and the detail's evidence, savings and score text is untouched.
import { bandGlyph, coordinateTag, swatchFor } from "./look.js";
import { money } from "./project-detail.js";

function text(tag, value, source, className = "") {
  const node = document.createElement(tag);
  if (source) node.dataset.src = source;
  if (className) node.className = className;
  node.textContent = value ?? "not stated";
  return node;
}

function savingsLabel(savings) {
  return savings?.status === "range" && Number.isFinite(savings.low_usd) && Number.isFinite(savings.high_usd)
    ? `Savings estimate ${money(savings.low_usd)} to ${money(savings.high_usd)}`
    : "No savings estimate";
}

// Two short names (one line each, full text in the title), then chips for the numbers.
export function renderPairSummary(payload, target) {
  const { overlap: pair, project_a: a, project_b: b, savings } = payload;
  const names = document.createElement("div");
  names.className = "summary-names";
  for (const project of [a, b]) {
    const line = document.createElement("p");
    line.className = "summary-project";
    const name = text("span", project?.properties?.name, "summary_name", "summary-name");
    name.title = name.textContent;
    line.append(swatchFor(project?.properties), name);
    names.append(line);
  }
  const chips = document.createElement("ul");
  chips.className = "summary-chips";
  chips.setAttribute("aria-label", "Pair at a glance");
  const chip = (className, ...children) => {
    const item = document.createElement("li");
    item.className = `summary-chip ${className}`.trim();
    item.append(...children);
    chips.append(item);
  };
  chip("summary-chip-band", bandGlyph(pair.band), text("span", pair.band_label ?? "Band not stated", "summary_band"), " ",
    text("span", Number.isFinite(pair.distance_km) ? `${pair.distance_km.toFixed(1)} km` : "Distance not stated", "summary_distance"));
  if (pair.town_capped === true) chip("summary-chip-quiet", text("span", "Counted as under 40 km"));
  chip("", text("span", `${pair.a_year ?? "unknown"} / ${pair.b_year ?? "unknown"}`, "summary_years"));
  const coordinate = coordinateTag(pair.a_year, pair.b_year, "");
  if (coordinate) chip("summary-chip-quiet coordinate-chip", coordinate);
  if (Number.isFinite(pair.score)) chip("", text("span", `Score ${pair.score}`, "summary_score"));
  chip("summary-chip-savings", text("span", savingsLabel(savings), "summary_savings"));
  target.replaceChildren(names, chips);
  target.hidden = false;
}

export function clearPairSummary(target) {
  target.replaceChildren();
  target.hidden = true;
}

const GUIDES = {
  why: "How close the two projects are, how sure their locations are, and their timing.",
  projects: "Each plan entry with its utility, source page, cost and location.",
  savings: "How the screening estimate was made and what it assumes.",
  rank: "How the score behind this rank is built.",
};

function guide(heading, section) {
  heading.dataset.section = section;
  heading.id = `pair-${section}`;
  heading.tabIndex = -1;
  heading.after(text("p", GUIDES[section], "", "section-hint"));
}

// Marks the rendered sections by structure (the block each heading introduces), not by wording.
export function addSectionGuides(content) {
  const evidence = content.querySelector(".overlap-evidence");
  if (!evidence) return;
  const projects = evidence.querySelector(":scope > .overlap-projects");
  if (projects) {
    const heading = text("h3", "The two projects");
    projects.before(heading);
  }
  let why = false;
  for (const heading of evidence.querySelectorAll(":scope > h3")) {
    const next = heading.nextElementSibling;
    if (next?.classList.contains("overlap-projects")) guide(heading, "projects");
    else if (next?.classList.contains("savings-detail")) guide(heading, "savings");
    else if (next?.classList.contains("score-detail")) guide(heading, "rank");
    else if (!why && next?.classList.contains("detail-block")) { guide(heading, "why"); why = true; }
  }
}

// Jumps keep the sticky bar in view (see scroll-margin in app.css) and move focus with the view.
export function setupDetailNav(nav, content) {
  const brief = document.getElementById("brief-panel");
  const targetFor = (section) => section === "brief"
    ? (brief.hidden ? null : brief)
    : content.querySelector(`[data-section="${section}"]`);
  nav.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-section]");
    const target = button && targetFor(button.dataset.section);
    if (!target) return;
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    target.scrollIntoView({ block: "start", behavior: reduced ? "auto" : "smooth" });
    (target === brief ? document.getElementById("brief-heading") : target).focus({ preventScroll: true });
  });
  return {
    refresh() {
      for (const button of nav.querySelectorAll("button[data-section]")) button.hidden = !targetFor(button.dataset.section);
      nav.hidden = false;
    },
    hide() { nav.hidden = true; },
  };
}
