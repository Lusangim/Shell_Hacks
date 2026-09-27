"""Guarded brief journeys; all model payloads and clipboard outcomes are local fakes."""

import json
import re
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

from tests.e2e.audits.checks import TEXT_LINT_JS


PAIR = "desc-p41__sertp-p107-9bc088"
OTHER = "sertp-p68-a0289a__sertp-p72-81610d"


@pytest.fixture
def browser_page(live_server, tmp_path):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        try:
            yield page
        finally:
            page.context.tracing.stop(path=tmp_path / "brief-trace.zip")
            browser.close()


def open_brief(page, live_server, pair=PAIR):
    page.goto(f"{live_server}/#overlap={pair}")
    expect(page.locator("#brief-panel")).to_be_visible()
    expect(page.get_by_role("button", name="Copy brief", exact=True)).to_be_enabled()
    return page.locator("#brief-panel")


@pytest.mark.parametrize("status", ["template", "cached", "stale", "none"])
def test_origin_header_controls_label_and_no_access_controls(browser_page, live_server, status):
    page = browser_page
    payload = page.request.get(f"{live_server}/api/briefs/{PAIR}").json()
    # Deliberately conflicting metadata proves the UI trusts the route's status.
    payload["generated_by"] = "fake-model" if status != "cached" else "template"
    page.route(f"**/api/briefs/{PAIR}", lambda route: route.fulfill(
        json=payload, headers={"X-GridLock-Brief-Status": status}))
    requests = []
    page.on("request", lambda request: requests.append(request))
    panel = open_brief(page, live_server)
    expect(panel.locator("#brief-origin")).to_have_text(
        "AI-drafted from public plan data. Check before use." if status == "cached" else "Template")
    expect(panel).to_contain_text("Possible saving (estimate): $62,000 to $264,000")
    expect(panel).to_contain_text("Approximate")
    expect(panel).to_contain_text("not verified")
    expect(panel.get_by_role("link")).to_have_count(2)
    for link in panel.get_by_role("link").all():
        assert re.fullmatch(r"/api/sources/(desc-scrtp-2026-2030|sertp-2025-rtp)#page=\d+", link.get_attribute("href"))
    assert page.get_by_role("button", name=re.compile("Generate|Send")).count() == 0
    assert all(request.method == "GET" and request.url.startswith(live_server) for request in requests)
    assert not re.search(r"desc-p\d|sertp-p\d|input_hash|fake-model|template-v1|data/", panel.inner_text())


@pytest.mark.parametrize("width,theme", [(1440, "light"), (1440, "dark"), (390, "light"), (390, "dark")])
def test_real_template_keyboard_layout_and_local_only(browser_page, live_server, width, theme):
    page = browser_page
    page.set_viewport_size({"width": width, "height": 900 if width == 1440 else 844})
    page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
    page.emulate_media(reduced_motion="reduce")
    errors, external = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("request", lambda request: external.append(request.url) if not request.url.startswith(live_server) else None)
    panel = open_brief(page, live_server)
    expect(panel.locator("#brief-origin")).to_have_text("Template")
    page.locator("#overlap-back").focus()
    for _ in range(40):
        if page.get_by_role("button", name="Copy brief", exact=True).evaluate("node => node === document.activeElement"):
            break
        page.keyboard.press("Tab")
    else:
        pytest.fail("Copy brief not reachable from the pair detail by Tab")
    assert page.get_by_role("button", name="Copy brief", exact=True).evaluate("node => getComputedStyle(node).outlineStyle !== 'none'")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    assert panel.locator(".detail-points").evaluate_all("nodes => nodes.every(node => node.children.length <= 3)")
    lint = page.evaluate(TEXT_LINT_JS)
    assert not lint["own"] and not lint["visible"], lint
    axe_source = (Path(__file__).resolve().parent / "vendor" / "axe.min.js").read_text(encoding="utf-8")
    violations = page.evaluate(axe_source + "\nwindow.axe.run(document.querySelector('#brief-panel'), "
                               "{runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']}})")["violations"]
    assert not violations, [(item["id"], item["nodes"][0]["target"]) for item in violations]
    assert errors == external == []


@pytest.mark.parametrize("failure", [False, True])
def test_copy_visible_brief_and_sources_with_status(browser_page, live_server, failure):
    page = browser_page
    page.add_init_script("Object.defineProperty(navigator, 'clipboard', {value: {writeText: async text => {"
                         + ("throw new Error('denied');" if failure else "window.copiedBrief = text;") + "}}});")
    panel = open_brief(page, live_server)
    panel.get_by_role("button", name="Copy brief", exact=True).click()
    expect(panel.locator("#brief-state")).to_contain_text("Could not copy" if failure else "Brief copied")
    expect(panel.locator("#brief-state")).to_be_in_viewport()
    if not failure:
        copied = page.evaluate("window.copiedBrief")
        assert "Template" in copied and "Next step" in copied and "Contact Dominion Energy SC and Georgia Power planning." in copied
        # The folded facts belong to the note, so the copy stands alone.
        assert "Possible saving (estimate)" in copied and "km apart" in copied
        assert "Team unit costs" in copied and "2026-09-26" in copied
        assert "/api/sources/desc-scrtp-2026-2030#page=41" in copied
        assert "Copy brief" not in copied and "input_hash" not in copied
        assert "These are separate plan entries" not in copied  # an unopened evidence disclosure stays out
        assert "Claude API" not in copied and "Who to contact and what to settle first" not in copied


@pytest.mark.parametrize("status", ["template", "cached"])
def test_brief_leads_with_actions_and_shows_what_the_ai_brief_adds(browser_page, live_server, status):
    page = browser_page
    payload = page.request.get(f"{live_server}/api/briefs/{PAIR}").json()
    page.route(f"**/api/briefs/{PAIR}", lambda route: route.fulfill(json=payload, headers={"X-GridLock-Brief-Status": status}))
    panel = open_brief(page, live_server)
    headings = panel.locator("#brief-content > h3").all_text_contents()
    assert headings[:2] == ["Next step", "Check first"], headings
    # The facts repeat the pair detail, so they start folded away.
    facts = panel.locator(".brief-facts")
    assert facts.evaluate("node => node.open") is False
    expect(facts.locator("[data-src='brief_savings'].detail-answer")).to_be_hidden()
    card = panel.locator(".ai-brief-card")
    expect(card).to_contain_text("AI-drafted briefs are off in this build" if status == "template" else "This brief is AI-drafted")
    card.locator("summary").click()
    expect(card).to_contain_text("This build did not generate it.")
    expect(card).to_contain_text("Deerfield switching station")
    assert page.get_by_role("button", name=re.compile("Generate|Send")).count() == 0
    page.evaluate("pair => { location.hash = 'overlap=' + pair; }", OTHER)
    other_card = page.locator("#brief-panel .ai-brief-card")
    expect(other_card).to_contain_text("at most 5 per run")
    expect(other_card).not_to_contain_text("Deerfield")


@pytest.mark.parametrize("status", [404, 503])
def test_error_retry_is_bound_to_current_pair(browser_page, live_server, status):
    page = browser_page
    page.route(f"**/api/briefs/{PAIR}", lambda route: route.fulfill(status=status, json={"error": "fake failure"}))
    page.goto(f"{live_server}/#overlap={PAIR}")
    expect(page.locator("#brief-state")).to_contain_text("Could not load")
    expect(page.get_by_role("button", name="Retry brief")).to_be_visible()
    page.unroute(f"**/api/briefs/{PAIR}")
    page.get_by_role("button", name="Retry brief").click()
    expect(page.get_by_role("button", name="Copy brief", exact=True)).to_be_enabled()
    page.evaluate("pair => { location.hash = 'overlap=' + pair; }", OTHER)
    expect(page.locator("#brief-content")).to_contain_text("No estimate")
    expect(page.get_by_role("button", name="Retry brief")).to_be_hidden()


@pytest.mark.parametrize("outcome", ["success", "failure"])
def test_keyboard_retry_keeps_a_visible_focus_target_in_the_brief(browser_page, live_server, outcome):
    """JA11Y-03: a retry hides its own button; focus stays in the brief instead of falling to BODY."""
    page = browser_page
    page.route(f"**/api/briefs/{PAIR}", lambda route: route.fulfill(status=503, json={"error": "fake failure"}))
    page.goto(f"{live_server}/#overlap={PAIR}")
    retry = page.get_by_role("button", name="Retry brief")
    expect(retry).to_be_visible()
    if outcome == "success":
        page.unroute(f"**/api/briefs/{PAIR}")
    retry.focus()
    page.keyboard.press("Enter")
    if outcome == "success":
        expect(page.get_by_role("button", name="Copy brief", exact=True)).to_be_enabled()
        expect(page.locator("#brief-heading")).to_be_focused()
        assert page.locator("#brief-heading").evaluate("node => getComputedStyle(node).outlineStyle") != "none"
        page.keyboard.press("Tab")
        assert page.evaluate("document.querySelector('#brief-panel').contains(document.activeElement)")
    else:
        expect(page.locator("#brief-state")).to_contain_text("Could not load")
        expect(retry).to_be_focused()
    assert page.evaluate("document.activeElement !== document.body")


@pytest.mark.parametrize("phase", ["headers", "json"])
def test_late_brief_cannot_replace_current_pair_or_survive_close(browser_page, live_server, phase):
    page = browser_page
    payload = page.request.get(f"{live_server}/api/briefs/{PAIR}").json()
    page.add_init_script("const oldBrief = " + json.dumps(payload) + "; const phase = " + json.dumps(phase) + ";" + """
      const original = window.fetch;
      window.fetch = (url, options) => {
        if (String(url).includes('/api/briefs/desc-p41__sertp-p107-9bc088')) {
          const hold = value => new Promise(resolve => { window.releaseBrief = () => {
            resolve(value); setTimeout(() => { window.briefSettled = true; }, 0);
          }; });
          const response = {ok:true, headers:new Headers({'X-GridLock-Brief-Status':'cached'}),
            json: () => phase === 'json' ? hold(oldBrief) : Promise.resolve(oldBrief)};
          return phase === 'headers' ? hold(response) : Promise.resolve(response);
        }
        return original(url, options);
      };
    """)
    page.goto(f"{live_server}/#overlap={PAIR}")
    page.wait_for_function("() => typeof window.releaseBrief === 'function'")
    expect(page.locator("#brief-state")).to_contain_text("Loading")
    page.evaluate("pair => { location.hash = 'overlap=' + pair; }", OTHER)
    expect(page.locator("#brief-content")).to_contain_text("No estimate")
    before = page.locator("#brief-content").inner_text()
    page.evaluate("window.releaseBrief()")
    page.wait_for_function("() => window.briefSettled === true")
    assert page.locator("#brief-content").inner_text() == before
    page.locator("#overlap-back").click()
    expect(page.locator("#brief-panel")).to_be_hidden()
    expect(page.locator("#brief-content")).to_be_empty()
    open_brief(page, live_server, OTHER)
    page.evaluate("location.hash = 'overlap=invalid'")
    expect(page.locator("#brief-panel")).to_be_hidden()
    expect(page.locator("#brief-content")).to_be_empty()


def test_hostile_evidence_safe_links_and_view_change_clear(browser_page, live_server):
    page = browser_page
    hostile = '<img src=x onerror="window.injected=true">'
    payload = page.request.get(f"{live_server}/api/briefs/{PAIR}").json()
    payload["what"] = hostile + " desc-p41 shared_endpoint data/raw/file.pdf"
    payload["sources"][0]["url"] = "https://untrusted.example/plan.pdf"
    payload["sources"][1]["doc"] = "Unknown document"
    payload["sources"][1]["url"] = "javascript:alert(1)"
    payload["who_to_contact"].append("Invented Person <person@example.test>")
    page.route(f"**/api/briefs/{PAIR}", lambda route: route.fulfill(json=payload, headers={"X-GridLock-Brief-Status": "cached"}))
    panel = open_brief(page, live_server)
    panel.locator(".brief-facts > summary").click()
    panel.get_by_text("Full project evidence", exact=True).click()
    expect(panel).to_contain_text(hostile)
    assert panel.locator("img").count() == 0
    assert page.evaluate("window.injected === undefined")
    assert "Invented Person" not in panel.inner_text()
    assert not re.search(r"desc-p41|shared_endpoint|data/raw", panel.inner_text())
    expect(panel.get_by_role("link")).to_have_count(1)
    assert panel.get_by_role("link").get_attribute("href").startswith("/api/sources/")
    page.locator("#projects-toggle").click()
    expect(panel).to_be_hidden()
    expect(page.locator("#brief-content")).to_be_empty()


@pytest.mark.parametrize("phase", ["headers", "json"])
def test_leaving_during_pair_fetch_cannot_render_or_select_a_hidden_pair(browser_page, live_server, phase):
    page = browser_page
    payload = page.request.get(f"{live_server}/api/overlaps/{PAIR}").json()
    page.add_init_script("const oldPairPayload = " + json.dumps(payload) + "; const phase = " + json.dumps(phase) + ";" + """
      const original = window.fetch;
      window.fetch = (url, options) => {
        if (String(url).includes('/api/overlaps/desc-p41__sertp-p107-9bc088')) {
          const hold = value => new Promise(resolve => { window.releasePair = () => {
            resolve(value); setTimeout(() => { window.pairSettled = true; }, 0);
          }; });
          const response = {ok:true, status:200,
            json: () => phase === 'json' ? hold(oldPairPayload) : Promise.resolve(oldPairPayload)};
          return phase === 'headers' ? hold(response) : Promise.resolve(response);
        }
        return original(url, options);
      };
    """)
    page.goto(f"{live_server}/#overlap={PAIR}")
    page.wait_for_function("() => typeof window.releasePair === 'function'")
    expect(page.locator("#overlap-state")).to_contain_text("Loading overlap")
    page.locator("#projects-toggle").click()
    expect(page.locator("#overlap-detail")).to_be_hidden()
    page.evaluate("window.releasePair()")
    page.wait_for_function("() => window.pairSettled === true")
    observed = page.evaluate("""async () => ({
      selected: (await import('/web/js/state.js')).state.selectedOverlapId,
      highlighted: document.querySelectorAll('[data-testid="project-feature"][data-selected="true"]').length,
      content: document.querySelector('#overlap-content').textContent,
      mapEntryHidden: document.querySelector('#map-pair-open').hidden
    })""")
    assert observed == {"selected": None, "highlighted": 0, "content": "", "mapEntryHidden": True}
    expect(page.locator("#brief-panel")).to_be_hidden()
    expect(page.locator("#brief-content")).to_be_empty()
