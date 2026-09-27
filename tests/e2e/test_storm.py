"""Storm lab from the area explorer, using the local API and map."""

from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

from tests.e2e.test_area import click_empty_map, explore_search, loaded


def open_storm(page):
    page.evaluate("""async () => {
      const {state} = await import('/web/js/state.js');
      state.map.setView([32.18, -81.16], 11, {animate:false});
    }""")
    page.get_by_role("button", name="Explore an area").click()
    click_empty_map(page)
    expect(page.locator("#area-panel")).to_be_visible()
    page.get_by_role("button", name="Invoke storm").click()
    expect(page.locator("#storm-results")).to_be_visible(timeout=30000)


def test_storm_area_result_play_pause_reset_and_clear(live_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="no-preference")
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(live_server)
                   else (external.append(route.request.url), route.abort()))
        loaded(page, live_server)
        with page.expect_response("**/api/storm/estimate?*") as storm_response:
            open_storm(page)
        payload = storm_response.value.json()
        summary = payload["summary"]
        expect(page.locator("#storm-cost")).to_contain_text("Possible repair cost (estimate)")
        expect(page.locator("#storm-cost")).to_contain_text(
            f'${summary["p10_usd"]:,} to ${summary["p90_usd"]:,}, median ${summary["p50_usd"]:,}'
        )
        expect(page.locator("#storm-coverage")).to_have_text(
            f'{summary["assets_exact"]} of {summary["assets_total"]} assets located exactly; '
            f'costs available for {int(summary["coverage_share"] * 100 + 0.5)}%.'
        )
        expect(page.locator("#storm-decision")).to_contain_text("System rule (Jev not configured)")
        expect(page.locator("#storm-assets li")).not_to_have_count(0)
        assert page.locator("#storm-assets li").count() <= 5
        expect(page.locator("#storm-assets li").first).to_contain_text("m/s")
        expect(page.locator("#storm-assets li").first).to_contain_text("mph")
        expect(page.locator("#storm-assets li").first).to_contain_text("Damage chance:")
        expect(page.locator("#storm-assets li").first).to_contain_text("Expected cost:")
        expect(page.get_by_test_id("storm-track")).to_have_count(1)
        expect(page.get_by_test_id("storm-rmax")).to_have_count(1)
        expect(page.get_by_test_id("storm-frame-dot")).to_have_count(len(payload["scenario"]["frames"]))
        slider = page.get_by_label("Storm frame")
        slider.fill("0")
        page.get_by_role("button", name="Resume storm").click()
        expect(slider).not_to_have_value("0", timeout=3500)
        page.get_by_role("button", name="Pause storm").click()
        paused = slider.input_value()
        page.wait_for_timeout(450)
        expect(slider).to_have_value(paused)
        page.get_by_role("button", name="Replay storm").click()
        expect(slider).to_have_value("0")
        page.get_by_role("button", name="Clear area").click()
        expect(page.locator("#storm-results")).to_be_hidden()
        expect(page.get_by_test_id("storm-track")).to_have_count(0)
        expect(page.get_by_test_id("storm-rmax")).to_have_count(0)
        assert errors == external == []
        browser.close()


def test_storm_from_search_area(live_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        loaded(page, live_server)
        explore_search(page, "Savannah")
        expect(page.locator("#area-panel")).to_be_visible()
        page.get_by_role("button", name="Invoke storm").click()
        expect(page.locator("#storm-results")).to_be_visible(timeout=30000)
        expect(page.locator("#storm-cost")).to_contain_text("Possible repair cost (estimate)")
        expect(page.get_by_test_id("storm-track")).to_have_count(1)
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_storm_reduced_motion_accessibility_and_escape(live_server, theme):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(live_server)
                   else (external.append(route.request.url), route.abort()))
        loaded(page, live_server)
        open_storm(page)
        slider = page.get_by_label("Storm frame")
        initial = slider.input_value()
        page.wait_for_timeout(450)
        expect(slider).to_have_value(initial)
        slider.fill("6")
        expect(slider).to_have_value("6")
        axe_source = (Path(__file__).parent / "vendor" / "axe.min.js").read_text(encoding="utf-8")
        violations = page.evaluate(axe_source + "\nwindow.axe.run(document.querySelector('#area-panel'), {runOnly: {type:'tag', values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")["violations"]
        assert not violations, [(item["id"], item["nodes"][0]["target"]) for item in violations]
        page.keyboard.press("Escape")
        expect(page.locator("#area-panel")).to_be_hidden()
        expect(page.get_by_test_id("storm-track")).to_have_count(0)
        assert errors == external == []
        browser.close()


def test_storm_options_request_selected_track(live_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        loaded(page, live_server)
        page.get_by_role("button", name="Explore an area").click()
        click_empty_map(page)
        page.get_by_label("Approach direction").select_option("SW")
        page.get_by_label("Storm strength").select_option("2")
        with page.expect_response("**/api/storm/estimate?*") as response:
            page.get_by_role("button", name="Invoke storm").click()
        assert response.value.request.url.find("direction=SW") > 0
        assert response.value.request.url.find("category=2") > 0
        browser.close()
