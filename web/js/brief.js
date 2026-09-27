import { citation, detailBlock, money, readableEvidence } from "./project-detail.js";

function text(tag, value, field) {
  const node = document.createElement(tag);
  node.textContent = value ?? "not stated";
  if (field) node.dataset.src = field;
  return node;
}

function renderBrief(brief, pairDetail, content) {
  const { overlap: pair, project_a: a, project_b: b } = pairDetail;
  const clean = (value) => readableEvidence(value, [a, b]);
  const block = (title, answer, field, evidence, bullets = []) => {
    const section = detailBlock(clean(answer), field, title === "What" ? "Full project evidence" : `Full ${title.toLowerCase()} evidence`,
      bullets.map((value) => text("li", clean(value), field)));
    for (const value of evidence) section.disclosure.append(text("p", clean(value), field));
    content.append(text("h3", title), section.block);
  };
  block("What", `${a.properties.name} / ${b.properties.name}`, "brief_what", [brief.what]);
  block("Where", `${pair.distance_km.toFixed(1)} km apart · ${pair.band_label}`, "brief_where", [brief.where], [
    pair.accuracy_pair === "approximate" ? "Approximate locations; physical sharing is not verified."
      : pair.accuracy_pair === "exact" ? "Exact mapped locations; physical sharing is not verified."
        : "Location accuracy is unknown; physical sharing is not verified.",
  ]);
  block("When", `${a.properties.in_service ?? "Not stated"} / ${b.properties.in_service ?? "Not stated"}`,
    "brief_when", [brief.when], ["Confirm current schedules with both organizations."]);
  block("Possible coordination", "Compare planned work before proposing shared scope.", "brief_sharing", brief.what_to_share,
    ["Shared equipment, access and outages are not verified."]);
  const savings = brief.savings_range;
  const assumptions = [];
  if (pairDetail.savings.assumption_ids?.includes("unit_costs_2026")) {
    assumptions.push("Team unit costs, 2026-09-26: only costs both job types need at this distance count.");
  }
  if (savings.status === "range" && !assumptions.length) assumptions.push("Screening assumption details are not stated.");
  const reasons = { no_cost: "No estimate: the plans do not size this pair, or these job types share nothing at this distance.",
    timing_too_far: "No estimate: project timing is too far apart.", unknown_year: "No estimate: a project year is not stated." };
  block("Saving estimate", savings.status === "range" && Number.isFinite(savings.low_usd) && Number.isFinite(savings.high_usd)
    ? `Possible saving (estimate): ${money(savings.low_usd)} to ${money(savings.high_usd)}`
    : reasons[savings.status] ?? "No estimate available.", "brief_savings", [savings.basis], [
      ...assumptions,
      "A saving is not verified or agreed.",
    ]);
  // The route grades contacts; retain a second boundary here: only this pair's organizations.
  const organizations = new Set([a.properties.utility, b.properties.utility]);
  const contacts = [...new Set(brief.who_to_contact)].filter((value) => organizations.has(value));
  block("Organizations to contact", contacts.join(" / ") || "Organizations not stated", "brief_contacts", [
    "Ask the organizations to identify the appropriate planning function. No individual contact is supplied.",
  ]);
  block("Caveats", "Public plan screening only. Coordination is not verified.", "brief_caveats", brief.caveats, [
    pair.accuracy_pair === "approximate" ? "Approximate locations need checking against source drawings."
      : "Check locations and construction limits against source drawings.",
    "Neither source confirms a joint project or shared saving.",
  ]);
  content.append(text("h3", "Sources"));
  for (const source of brief.sources) {
    const paragraph = document.createElement("p");
    paragraph.className = "brief-source";
    // citation uses a fixed document whitelist, never a payload's URL.
    paragraph.append(citation({ ...source, doc: clean(source.doc) }));
    content.append(paragraph);
  }
}

export function setupBrief() {
  const panel = document.getElementById("brief-panel");
  const content = document.getElementById("brief-content");
  const origin = document.getElementById("brief-origin");
  const status = document.getElementById("brief-state");
  const copy = document.getElementById("brief-copy");
  const retry = document.getElementById("brief-retry");
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

  async function open(pairDetail) {
    clear();
    if (document.getElementById("overlap-detail").hidden) return;
    current = pairDetail;
    const ownRevision = revision;
    controller = new AbortController();
    panel.hidden = false;
    panel.setAttribute("aria-busy", "true");
    status.textContent = "Loading coordination brief.";
    try {
      const response = await fetch(`/api/briefs/${encodeURIComponent(pairDetail.overlap.id)}`, { signal: controller.signal });
      if (ownRevision !== revision) return;
      if (!response.ok) throw new Error("Brief unavailable");
      const brief = await response.json();
      if (ownRevision !== revision) return;
      if (brief.overlap_id !== pairDetail.overlap.id) throw new Error("Mismatched brief");
      renderBrief(brief, pairDetail, content);
      origin.textContent = response.headers.get("X-GridLock-Brief-Status") === "cached"
        ? "AI-drafted from public plan data. Check before use." : "Template";
      status.textContent = "Brief ready. Check the source documents before use.";
      copy.disabled = false;
    } catch (error) {
      if (ownRevision !== revision || error.name === "AbortError") return;
      content.replaceChildren();
      status.textContent = "Could not load this brief. Retry for the selected pair or check the local server.";
      retry.hidden = false;
    } finally {
      if (ownRevision === revision) panel.removeAttribute("aria-busy");
    }
  }

  retry.addEventListener("click", () => { if (current) void open(current); });
  copy.addEventListener("click", async () => {
    const ownRevision = revision;
    // innerText includes only evidence whose disclosure the reader has opened.
    const sources = Array.from(content.querySelectorAll("a")).map((link) => `${link.textContent}: ${link.href}`);
    const visibleText = Array.from(content.children).map((node) => {
      if (!node.classList.contains("detail-block")) return node.innerText;
      return Array.from(node.children).map((child) => child.tagName === "DETAILS"
        ? child.open ? Array.from(child.children).filter((item) => item.tagName !== "SUMMARY").map((item) => item.innerText).join("\n") : ""
        : child.innerText).filter(Boolean).join("\n");
    }).join("\n\n");
    try {
      await navigator.clipboard.writeText(["Coordination brief", origin.textContent, visibleText, ...sources].join("\n\n"));
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
