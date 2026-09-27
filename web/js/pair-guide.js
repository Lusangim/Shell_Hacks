// Presentation of the selected pair. Facts and evidence remain the API's own fields.
import { coordinateTag, swatchFor } from "./look.js";
import { money, utilityLabel } from "./project-detail.js";

function text(tag, value, source, className = "") {
  const node = document.createElement(tag);
  if (source) node.dataset.src = source;
  if (className) node.className = className;
  node.textContent = value ?? "not stated";
  return node;
}

export function renderPairSummary(payload, target) {
  const { overlap: pair, project_a: a, project_b: b, savings } = payload;
  const title = text("h3", utilityLabel(a.properties), "summary_utility", "pair-title");
  title.append(text("span", "+ " + utilityLabel(b.properties), "summary_utility", "pair-partner"));
  const projects = document.createElement("div");
  projects.className = "summary-names";
  for (const project of [a, b]) {
    const entry = document.createElement("div");
    entry.className = "summary-project";
    const copy = document.createElement("div");
    const name = text("p", project.properties.name, "summary_name", "summary-name");
    name.title = name.textContent;
    copy.append(text("strong", utilityLabel(project.properties), "summary_utility"),
      text("span", "Plan entry", "", "project-caption"), name);
    entry.append(swatchFor(project.properties), copy);
    projects.append(entry);
  }
  const facts = document.createElement("dl");
  facts.className = "pair-facts";
  facts.setAttribute("aria-label", "Pair at a glance");
  const fact = (label, value, source, className = "") => {
    const item = document.createElement("div");
    const result = text("dd", "", "", className);
    result.append(value instanceof Node ? value : text("span", value, source));
    item.append(text("dt", label), result);
    facts.append(item);
  };
  fact("Proximity", pair.band_label ?? "Band not stated", "summary_band");
  const accuracy = { approximate: "Approx.", exact: "Exact" }[pair.accuracy_pair] ?? "Unknown";
  fact("Distance", Number.isFinite(pair.distance_km) ? `${pair.distance_km.toFixed(1)} km · ${accuracy}` : "Distance not stated", "summary_distance");
  fact("Years (in service)", `${pair.a_year ?? "unknown"} / ${pair.b_year ?? "unknown"}`, "summary_years");
  fact("Coordination window", coordinateTag(pair.a_year, pair.b_year, "coordinate-chip") ?? "Unknown", "summary_window");
  fact("Score", Number.isFinite(pair.score) ? String(pair.score) : "Unknown", "summary_score");
  fact("Possible saving", savings?.status === "range" && Number.isFinite(savings.low_usd) && Number.isFinite(savings.high_usd)
    ? `${money(savings.low_usd)} to ${money(savings.high_usd)} (estimate)` : "No savings estimate", "summary_savings");
  target.replaceChildren(title, projects, facts);
  if (pair.town_capped === true) target.append(text("p", "Counted as under 40 km: town-level location.", "town_capped", "detail-note"));
  target.hidden = false;
}

export function clearPairSummary(target) {
  target.replaceChildren();
  target.hidden = true;
}

function disclosure(label, section, block) {
  const details = document.createElement("details");
  details.className = "pair-disclosure";
  const summary = text("summary", label);
  summary.id = `pair-${section}`;
  summary.dataset.section = section;
  details.append(summary, block);
  return details;
}

// The seven original detail blocks, source links and all data-src hooks stay intact inside.
export function addSectionGuides(content) {
  const evidence = content.querySelector(".overlap-evidence");
  if (!evidence) return;
  const why = evidence.querySelector(":scope > .detail-block");
  const projects = evidence.querySelector(":scope > .overlap-projects");
  const savings = evidence.querySelector(":scope > .savings-detail");
  const rank = evidence.querySelector(":scope > .score-detail");
  const sections = [
    disclosure("Why they appear together", "why", why),
    disclosure("Sources", "projects", projects),
    disclosure("About the estimate", "savings", savings),
  ];
  if (rank) sections.push(disclosure("How this pair ranks", "rank", rank));
  evidence.replaceChildren(...sections);
}
