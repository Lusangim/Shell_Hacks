"""Overlap detail journeys use real public-plan records and local citations."""

from __future__ import annotations

import pytest
from playwright.sync_api import expect, sync_playwright


MCINTOSH = "desc-p41__sertp-p107-9bc088"
NO_COST = "sertp-p68-a0289a__sertp-p72-81610d"
PROXY = "sertp-p124-e36f41__sertp-p133-9ca229"


def open_row(page, overlap_id):
    button = page.locator(f'[data-testid="overlap-row"][data-overlap-id="{overlap_id}"] button')
    expect(button).to_be_visible()
    button.click()
    expect(page.get_by_test_id("overlap-detail")).to_be_visible()


def test_mcintosh_row_shows_source_pages_evidence_savings_and_map_selection(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        external = []
        page.on("request", lambda request: external.append(request.url) if not request.url.startswith(live_server) else None)
        page.goto(live_server)
        expected = page.request.get(f"{live_server}/api/overlaps/{MCINTOSH}").json()
        open_row(page, MCINTOSH)
        detail = page.get_by_test_id("overlap-detail")
        expect(detail.locator('[data-src="name"]')).to_have_count(2)
        assert detail.locator('[data-src="name"]').all_text_contents() == [
            expected["project_a"]["properties"]["name"], expected["project_b"]["properties"]["name"]]
        expect(detail.locator('[data-src="utility"]')).to_have_count(2)
        expect(detail.locator('[data-src="touch_reason"]')).to_contain_text("shared_endpoint")
        expect(detail.locator('[data-src="touch_detail"]')).to_have_text(expected["overlap"]["touch_detail"])
        expect(detail.locator('[data-src="can_share"]')).to_have_text(expected["overlap"]["can_share"])
        expect(detail).to_contain_text("possibly touching")
        expect(detail).to_contain_text("$54k to $161k")
        expect(detail.locator('[data-src="savings_basis"]')).to_have_text(expected["savings"]["basis"])
        expect(detail).to_contain_text("2026-09-26")
        expect(detail).to_contain_text("1% to 3%")
        expect(detail.get_by_role("link")).to_have_count(2)
        expect(detail.get_by_role("link").nth(0)).to_have_attribute("href", "/api/sources/desc-scrtp-2026-2030#page=41")
        expect(detail.get_by_role("link").nth(1)).to_have_attribute("href", "/api/sources/sertp-2025-rtp#page=107")
        expect(page.locator('[data-testid="project-feature"][data-selected="true"]')).to_have_count(2)
        assert page.url.endswith(f"#overlap={MCINTOSH}")
        assert external == []
        page.reload()
        expect(page.get_by_test_id("overlap-detail").locator('[data-src="touch_detail"]')).to_have_text(expected["overlap"]["touch_detail"])
        page.get_by_role("button", name="Back to ranked overlaps").click()
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        browser.close()


def test_no_cost_and_proxy_basis_are_distinct_and_source_backed(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        open_row(page, NO_COST)
        detail = page.get_by_test_id("overlap-detail")
        expect(detail).to_contain_text("No screening range")
        expected_no_cost = page.request.get(f"{live_server}/api/overlaps/{NO_COST}").json()
        expect(detail.locator('[data-src="savings_basis"]')).to_have_text(expected_no_cost["savings"]["basis"])
        page.get_by_role("button", name="Back to ranked overlaps").click()
        open_row(page, PROXY)
        expected_proxy = page.request.get(f"{live_server}/api/overlaps/{PROXY}").json()
        expect(detail.locator('[data-src="savings_basis"]')).to_have_text(expected_proxy["savings"]["basis"])
        expect(detail).to_contain_text("proxy")
        expect(detail).to_contain_text("2026-09-26")
        browser.close()


def test_valid_unknown_stale_and_filtered_links_have_distinct_states(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}/#overlap={MCINTOSH}")
        expect(page.get_by_test_id("overlap-detail")).to_contain_text("McIntosh")
        page.goto(f"{live_server}/#overlap=not-a-pair")
        expect(page.get_by_test_id("overlap-state")).to_contain_text("Unknown overlap link")
        page.goto(f"{live_server}/#overlap=desc-p41__sertp-p999-deadbe")
        expect(page.get_by_test_id("overlap-state")).to_contain_text("stale")
        page.route("**/api/overlaps", lambda route: route.fulfill(status=200, content_type="application/json", body="[]"))
        page.goto(f"{live_server}/?filtered=1#overlap={MCINTOSH}")
        expect(page.get_by_test_id("overlap-detail")).to_contain_text("McIntosh")
        expect(page.get_by_test_id("overlap-state")).to_contain_text("outside the current filters")
        browser.close()


def test_history_back_and_forward_restore_pair_selection(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        first = page.get_by_test_id("overlap-row").first.get_attribute("data-overlap-id")
        second = page.get_by_test_id("overlap-row").nth(1).get_attribute("data-overlap-id")
        open_row(page, first)
        page.get_by_role("button", name="Back to ranked overlaps").click()
        open_row(page, second)
        page.go_back()
        expect(page.get_by_test_id("overlap-detail")).to_be_hidden()
        page.go_back()
        expect(page.get_by_test_id("overlap-detail")).to_be_visible()
        assert page.url.endswith(f"#overlap={first}")
        page.go_forward()
        expect(page.get_by_test_id("overlap-detail")).to_be_hidden()
        page.go_forward()
        assert page.url.endswith(f"#overlap={second}")
        expect(page.get_by_test_id("overlap-detail")).to_be_visible()
        browser.close()


def test_map_highlight_has_a_separate_pair_entry(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(live_server)
        paired = page.request.get(f"{live_server}/api/overlaps").json()
        ids = list({project_id for pair in paired for project_id in (pair["a"], pair["b"])})
        project_id = page.evaluate("""ids => Array.from(document.querySelectorAll('[data-testid="project-feature"]'))
          .map(path => {
            const box = path.getBoundingClientRect();
            const x = box.left + box.width/2, y = box.top + box.height/2;
            return {id:path.dataset.projectId, x, y, hit:document.elementFromPoint(x,y) === path};
          }).find(item => ids.includes(item.id) && item.hit && item.x > 450
            && item.x < innerWidth - 20 && item.y > 20 && item.y < innerHeight - 20)?.id""", ids)
        assert project_id
        page.locator(f'[data-testid="project-feature"][data-project-id="{project_id}"]').click()
        expect(page.get_by_test_id("project-detail")).to_be_visible()
        button = page.get_by_role("button", name="Open highlighted pair")
        expect(button).to_be_visible()
        button.click()
        expect(page.get_by_test_id("overlap-detail")).to_be_visible()
        expect(page.locator('[data-testid="project-feature"][data-selected="true"]')).to_have_count(2)
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_keyboard_phone_detail_has_focus_no_overflow_or_console_error(live_server, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        page.locator("#search-input").focus()
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.classList.contains('overlap-button')"), "Ranked overlap not reachable from search by Tab"
        page.keyboard.press("Enter")
        detail = page.get_by_test_id("overlap-detail")
        expect(detail).to_be_visible()
        back = page.get_by_role("button", name="Back to ranked overlaps")
        assert back.evaluate("element => document.activeElement === element")
        assert back.evaluate("element => getComputedStyle(element).outlineStyle") != "none"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        back.click()
        assert page.evaluate("document.activeElement.classList.contains('overlap-button')")
        assert errors == []
        browser.close()


def test_hostile_detail_text_is_rendered_as_text_only(live_server):
    hostile = '<img src=x onerror="window.injected=true">'
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()

        def mutate(route):
            payload = route.fetch().json()
            payload["overlap"]["touch_detail"] = hostile
            payload["overlap"]["pair_note"] = hostile
            payload["project_a"]["properties"]["name"] = hostile
            payload["project_a"]["properties"]["source"]["url"] = "https://untrusted.example/plan.pdf"
            route.fulfill(json=payload)

        page.route(f"**/api/overlaps/{MCINTOSH}", mutate)
        page.goto(f"{live_server}/#overlap={MCINTOSH}")
        detail = page.get_by_test_id("overlap-detail")
        expect(detail.locator('[data-src="touch_detail"]')).to_have_text(hostile)
        expect(detail.locator('[data-src="pair_note"]')).to_have_text(hostile)
        expect(detail.locator('[data-src="name"]').first).to_have_text(hostile)
        assert page.locator("img[src='x']").count() == 0
        assert page.evaluate("window.injected === undefined")
        assert detail.get_by_role("link").first.get_attribute("href").startswith("/api/sources/")
        browser.close()


def test_delayed_old_detail_cannot_replace_new_selection(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("""(() => {
          const original = window.fetch;
          window.oldPairGate = {};
          window.fetch = (url, options) => {
            if (String(url).includes('/api/overlaps/desc-p41__sertp-p107-9bc088')) {
              document.documentElement.dataset.oldPairPending = 'true';
              return new Promise(resolve => { window.oldPairGate.release = () => resolve({
                ok: true,
                json: async () => { window.oldPairGate.consumed = true;
                  document.documentElement.dataset.oldPairConsumed = 'true';
                  return {overlap:{id:'desc-p41__sertp-p107-9bc088'}}; }
              }); });
            }
            return original(url, options);
          };
        })();""")
        page.goto(live_server)
        open_row(page, MCINTOSH)
        expect(page.locator("html[data-old-pair-pending='true']")).to_have_count(1)
        page.get_by_role("button", name="Back to ranked overlaps").click()
        other = page.get_by_test_id("overlap-row").nth(1).get_attribute("data-overlap-id")
        assert other != MCINTOSH
        page.get_by_test_id("overlap-row").nth(1).locator("button").click()
        expect(page.get_by_test_id("overlap-detail")).to_contain_text("DRESDEN")
        page.evaluate("window.oldPairGate.release()")
        page.wait_for_timeout(100)
        assert page.evaluate("window.oldPairGate.consumed !== true")
        assert page.url.endswith(f"#overlap={other}")
        expect(page.get_by_test_id("overlap-detail")).to_contain_text("DRESDEN")
        browser.close()
