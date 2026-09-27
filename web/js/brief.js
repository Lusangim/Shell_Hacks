import { citation, detailBlock, money, readableEvidence } from "./project-detail.js";
import { AI_BRIEF_EXAMPLE } from "./ai-brief-example.js";

function text(tag, value, field, className = "") {
  const node = document.createElement(tag);
  node.textContent = value ?? "not stated";
  if (field) node.dataset.src = field;
  if (className) node.className = className;
  return node;
}

// What the optional Claude API brief adds; shown instead of repeating the pair's facts.
function aiBriefCard(pairDetail, aiDrafted) {
  const { project_a: a, project_b: b } = pairDetail;
  const card = detailBlock(aiDrafted
    ? "This brief is AI-drafted. It passed the same evidence checks before it was saved."
    : "AI-drafted briefs are off in this build: they need a Claude API key and a spending limit.",
  "ai_brief", pairDetail.overlap.id === AI_BRIEF_EXAMPLE.overlap_id ? "Example for this pair" : "How AI briefs stay safe", [
    text("li", "Writes one plain-language note for both utilities' planners, specific to these two jobs.", "ai_brief_adds"),
    text("li", "Picks out the open question to settle first, from the plan text.", "ai_brief_adds"),
    text("li", "Checked before it is shown: every number, year, page and contact must match the plan data.", "ai_brief_adds"),
  ]);
  card.block.classList.add("ai-brief-card");
  if (pairDetail.overlap.id === AI_BRIEF_EXAMPLE.overlap_id) {
    card.disclosure.append(text("p", "Drafted with Claude outside the app from this pair's data, and checked by the same evidence "
      + "grader the live feature uses. This build did not generate it.", "ai_brief_note"));
    card.disclosure.append(text("p", readableEvidence(AI_BRIEF_EXAMPLE.what, [a, b]), "ai_brief_example"));
    const steps = document.createElement("ul");
    for (const step of AI_BRIEF_EXAMPLE.what_to_share) steps.append(text("li", readableEvidence(step, [a, b]), "ai_brief_example"));
    card.disclosure.append(steps);
  } else {
    card.disclosure.append(text("p", "Off by default. When switched on, the server drafts one brief at a time, at most 5 per run, "
      + "within a spending limit, and only for requests from this page. A draft that fails the evidence checks falls back to "
      + "the template, and every AI draft is labelled.", "ai_brief_note"));
  }
  return card.block;
}

function renderBrief(brief, pairDetail, content, aiDrafted) {
  const { overlap: pair, project_a: a, project_b: b } = pairDetail;
  const clean = (value) => readableEvidence(value, [a, b]);
  const block = (parent, heading, title, answer, field, evidence, bullets = []) => {
    const section = detailBlock(clean(answer), field, title === "What" ? "Full project evidence" : `Full ${title.toLowerCase()} evidence`,
      bullets.map((value) => text("li", clean(value), field)));
    for (const value of evidence) section.disclosure.append(text("p", clean(value), field));
    parent.append(text(heading, title), section.block);
  };
  content.append(text("p", "Who to contact and what to settle first. The pair's facts, savings and sources are above; "
    + "Copy brief includes them.", "", "brief-intro"));
  // The route grades contacts; retain a second boundary here: only this pair's organizations.
  const organizations = new Set([a.properties.utility, b.properties.utility]);
  const contacts = [...new Set(brief.who_to_contact)].filter((value) => organizations.has(value));
  block(content, "h3", "Next step", contacts.length ? `Contact ${contacts.join(" and ")} planning.` : "Organizations not stated",
    "brief_contacts", ["Ask the organizations to identify the appropriate planning function. No individual contact is supplied."],
    brief.what_to_share.slice(0, 3));
  block(content, "h3", "Check first", "Public plan screening only. Coordination is not verified.", "brief_caveats", brief.caveats, [
    pair.accuracy_pair === "approximate" ? "Approximate locations need checking against source drawings."
      : "Check locations and construction limits against source drawings.",
    "Neither source confirms a joint project or shared saving.",
  ]);
  // The same facts as the pair detail, folded away so the note can be copied whole without repeating them on screen.
  const facts = document.createElement("details");
  facts.className = "brief-facts";
  const factsSummary = document.createElement("summary");
  factsSummary.textContent = "Facts in this note (the same as the pair detail)";
  facts.append(factsSummary);
  block(facts, "h4", "What", `${a.properties.name} / ${b.properties.name}`, "brief_what", [brief.what]);
  block(facts, "h4", "Where", `${pair.distance_km.toFixed(1)} km apart · ${pair.band_label}`, "brief_where", [brief.where], [
    pair.accuracy_pair === "approximate" ? "Approximate locations; physical sharing is not verified."
      : pair.accuracy_pair === "exact" ? "Exact mapped locations; physical sharing is not verified."
        : "Location accuracy is unknown; physical sharing is not verified.",
    ...(pair.town_capped === true ? ["Counted as under 40 km: a location is only a town centre, not a substation."] : []),
  ]);
  block(facts, "h4", "When", `${a.properties.in_service ?? "Not stated"} / ${b.properties.in_service ?? "Not stated"}`,
    "brief_when", [brief.when], ["Confirm current schedules with both organizations."]);
  const savings = brief.savings_range;
  const assumptions = [];
  if (pairDetail.savings.assumption_ids?.includes("unit_costs_2026")) {
    assumptions.push("Team unit costs, 2026-09-26: only costs both job types need at this distance count.");
  }
  if (savings.status === "range" && !assumptions.length) assumptions.push("Screening assumption details are not stated.");
  const reasons = { no_cost: "No estimate: the plans do not size this pair, or these job types share nothing at this distance.",
    timing_too_far: "No estimate: project timing is too far apart.", unknown_year: "No estimate: a project year is not stated." };
  block(facts, "h4", "Saving estimate", savings.status === "range" && Number.isFinite(savings.low_usd) && Number.isFinite(savings.high_usd)
    ? `Possible saving (estimate): ${money(savings.low_usd)} to ${money(savings.high_usd)}`
    : reasons[savings.status] ?? "No estimate available.", "brief_savings", [savings.basis], [
      ...assumptions,
      "A saving is not verified or agreed.",
    ]);
  content.append(facts, text("h3", "Sources"));
  for (const source of brief.sources) {
    const paragraph = document.createElement("p");
    paragraph.className = "brief-source";
    // citation uses a fixed document whitelist, never a payload's URL.
    paragraph.append(citation({ ...source, doc: clean(source.doc) }));
    content.append(paragraph);
  }
  content.append(text("h3", "With the Claude API", "", "ai-brief-heading"), aiBriefCard(pairDetail, aiDrafted));
}

// Copy the whole note: every answer and point, including the folded facts, plus any evidence the reader
// opened, and the sources. The on-screen intro and the AI showcase are not part of the note.
function noteText(content) {
  const blockText = (block) => {
    const parts = [block.querySelector(":scope > .detail-answer")?.textContent ?? ""];
    for (const item of block.querySelectorAll(":scope > ul > li")) parts.push(item.textContent);
    const evidence = block.querySelector(":scope > details");
    if (evidence?.open) for (const paragraph of evidence.querySelectorAll(":scope > p")) parts.push(paragraph.textContent);
    return parts.filter(Boolean).join("\n");
  };
  const lines = [];
  const walk = (nodes) => {
    for (const node of nodes) {
      if (["brief-intro", "ai-brief-heading", "ai-brief-card", "brief-source"].some((name) => node.classList.contains(name))) continue;
      if (node.classList.contains("brief-facts")) walk(Array.from(node.children).filter((child) => child.tagName !== "SUMMARY"));
      else if (node.classList.contains("detail-block")) lines.push(blockText(node));
      else lines.push(node.textContent);
    }
  };
  walk(Array.from(content.children));
  return lines.filter(Boolean).join("\n\n");
}

export function setupBrief() {
  const panel = document.getElementById("brief-panel");
  const content = document.getElementById("brief-content");
  const origin = document.getElementById("brief-origin");
  const status = document.getElementById("brief-state");
  const copy = document.getElementById("brief-copy");
  const retry = document.getElementById("brief-retry");
  const heading = document.getElementById("brief-heading");
  let revision = 0;
  let controller;
  let current;

  function clear() {
    revision += 1;
    controller?.abort();
    controller = null;
    current = null;
    panel.hidden = true;
    panel.removeAttribute("aria-busy");
    content.replaceChildren();
    origin.textContent = "";
    status.textContent = "";
    copy.disabled = true;
    retry.hidden = true;
  }

  async function open(pairDetail, { fromRetry = false } = {}) {
    clear();
    if (document.getElementById("overlap-detail").hidden) return;
    current = pairDetail;
    const ownRevision = revision;
    controller = new AbortController();
    panel.hidden = false;
    panel.setAttribute("aria-busy", "true");
    status.textContent = "Loading coordination brief.";
    // A retry hides its own button; keep the keyboard position on the brief's heading.
    if (fromRetry) heading.focus({ preventScroll: true });
    try {
      const response = await fetch(`/api/briefs/${encodeURIComponent(pairDetail.overlap.id)}`, { signal: controller.signal });
      if (ownRevision !== revision) return;
      if (!response.ok) throw new Error("Brief unavailable");
      const brief = await response.json();
      if (ownRevision !== revision) return;
      if (brief.overlap_id !== pairDetail.overlap.id) throw new Error("Mismatched brief");
      const aiDrafted = response.headers.get("X-GridLock-Brief-Status") === "cached";
      renderBrief(brief, pairDetail, content, aiDrafted);
      origin.textContent = aiDrafted ? "AI-drafted from public plan data. Check before use." : "Template";
      status.textContent = "Brief ready. Check the source documents before use.";
      copy.disabled = false;
    } catch (error) {
      if (ownRevision !== revision || error.name === "AbortError") return;
      content.replaceChildren();
      status.textContent = "Could not load this brief. Retry for the selected pair or check the local server.";
      retry.hidden = false;
      if (fromRetry && document.activeElement === heading) retry.focus();
    } finally {
      if (ownRevision === revision) panel.removeAttribute("aria-busy");
    }
  }

  retry.addEventListener("click", () => { if (current) void open(current, { fromRetry: true }); });
  copy.addEventListener("click", async () => {
    const ownRevision = revision;
    const sources = Array.from(content.querySelectorAll(".brief-source a")).map((link) => `${link.textContent}: ${link.href}`);
    try {
      await navigator.clipboard.writeText(["Coordination brief", origin.textContent, noteText(content), ...sources].join("\n\n"));
      if (ownRevision === revision) status.textContent = "Brief copied with sources.";
    } catch (_error) {
      if (ownRevision === revision) status.textContent = "Could not copy the brief. Select the text to copy it manually.";
    }
  });
  // Project navigation owns this element. Observe only its hidden attribute, never brief writes.
  const pairPanel = document.getElementById("overlap-detail");
  new MutationObserver(() => { if (pairPanel.hidden) clear(); })
    .observe(pairPanel, { attributes: true, attributeFilter: ["hidden"] });
  return { open, clear };
}
