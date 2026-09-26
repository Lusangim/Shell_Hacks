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
    expect(panel).to_contain_text("Possible saving (estimate): $54,000 to $161,000")
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
        assert "Template" in copied and "Possible saving (estimate)" in copied
        assert "1% to 3%" in copied and "2026-09-26" in copied
        assert "/api/sources/desc-scrtp-2026-2030#page=41" in copied
        assert "Copy brief" not in copied and "input_hash" not in copied
        assert "These are separate public plan entries" not in copied  # disclosure is closed


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


def test_leaving_during_pair_fetch_cannot_open_a_brief(browser_page, live_server):
    page = browser_page
    payload = page.request.get(f"{live_server}/api/overlaps/{PAIR}").json()
    held = []
    page.route(f"**/api/overlaps/{PAIR}", lambda route: held.append(route))
    page.goto(f"{live_server}/#overlap={PAIR}")
    expect(page.locator("#overlap-state")).to_contain_text("Loading overlap")
    page.locator("#projects-toggle").click()
    expect(page.locator("#overlap-detail")).to_be_hidden()
    assert held
    held[0].fulfill(json=payload)
    expect(page.locator("#overlap-content")).to_contain_text("McIntosh")
    expect(page.locator("#brief-panel")).to_be_hidden()
    expect(page.locator("#brief-content")).to_be_empty()
