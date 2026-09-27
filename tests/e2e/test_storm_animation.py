"""The selected hypothetical storm animates on the map and reports in the detail pane."""

from pathlib import Path
from collections import Counter

import pytest
from playwright.sync_api import expect, sync_playwright

from tests.e2e.test_area import click_empty_map, loaded


AXE = (Path(__file__).parent / "vendor" / "axe.min.js").read_text(encoding="utf-8")


def select_storm(page):
    page.evaluate("""async () => {
      const {state} = await import('/web/js/state.js');
      state.map.setView([32.18, -81.16], 11, {animate:false});
    }""")
    page.get_by_role("button", name="Explore an area").click()
    click_empty_map(page)
    expect(page.locator("#area-panel")).to_be_visible()
    page.get_by_label("Approach direction").select_option("SW")
    page.get_by_label("Storm strength").select_option("2")
    with page.expect_response("**/api/storm/estimate?*") as result:
        page.get_by_role("button", name="Invoke storm").click()
    payload = result.value.json()
    assert payload["scenario"]["id"] == "synthetic"
    assert "direction=SW" in result.value.request.url
    assert "category=2" in result.value.request.url
    expect(page.get_by_test_id("storm-symbol")).to_have_count(1)
    return payload


def position(page):
    box = page.get_by_test_id("storm-symbol").bounding_box()
    assert box is not None
    return box["x"], box["y"]


def audit(page, selector):
    return page.evaluate(AXE + f"\nwindow.axe.run(document.querySelector('{selector}'), {{runOnly: {{type:'tag', values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}}}})")["violations"]


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_storm_moves_pauses_replays_and_reports(live_server, theme):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="no-preference")
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(live_server)
                   else (external.append(route.request.url), route.abort()))
        loaded(page, live_server)
        payload = select_storm(page)
        expect(page.get_by_test_id("storm-asset")).to_have_count(len(payload["assets"]))
        map_box = page.locator("#map").bounding_box()
        x, y = position(page)
        assert map_box["x"] <= x <= map_box["x"] + map_box["width"]
        assert map_box["y"] <= y <= map_box["y"] + map_box["height"]
        page.wait_for_timeout(2100)
        first = position(page)
        page.wait_for_timeout(500)
        second = position(page)
        assert first != second
        page.get_by_role("button", name="Pause storm").click()
        paused = position(page)
        page.wait_for_timeout(400)
        assert position(page) == paused
        assert audit(page, "#storm-lab") == []
        page.get_by_role("button", name="Skip to results").click()
        detail = page.locator("#storm-detail")
        expect(detail).to_be_visible()
        summary = payload["summary"]
        expect(detail).to_contain_text(f'${summary["p10_usd"]:,} to ${summary["p90_usd"]:,}')
        expect(detail).to_contain_text(f'{summary["assets_with_cost"]} of {summary["assets_total"]} assets with a cost basis')
        counts = Counter(asset["class"] for asset in payload["assets"])
        expect(detail).to_contain_text(
            f'{counts["line_wood"]} wood lines, {counts["line_steel"]} steel lines, {counts["substation"]} substations')
        expect(detail).to_contain_text("System rule (Jev not configured)")
        assert audit(page, "#storm-detail") == []
        page.get_by_role("button", name="Replay storm").click()
        expect(detail).to_be_hidden()
        expect(page.get_by_label("Storm frame")).to_have_value("0")
        page.get_by_role("button", name="Skip to results").click()
        page.get_by_test_id("overlap-row").first.locator("button").click()
        expect(detail).to_be_hidden()
        expect(page.locator("#overlap-detail")).to_be_visible()
        assert errors == external == []
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_reduced_motion_shows_result_and_clear_removes_layers(live_server, theme):
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
        select_storm(page)
        expect(page.locator("#storm-detail")).to_be_visible()
        before = position(page)
        page.wait_for_timeout(400)
        assert position(page) == before
        assert audit(page, "#storm-lab") == []
        assert audit(page, "#storm-detail") == []
        page.get_by_role("button", name="Clear area").click()
        expect(page.get_by_test_id("storm-symbol")).to_have_count(0)
        expect(page.get_by_test_id("storm-track")).to_have_count(0)
        expect(page.get_by_test_id("storm-rmax")).to_have_count(0)
        expect(page.locator("#storm-detail")).to_be_hidden()
        expect(page.locator("aside.detail-pane")).to_be_hidden()
        assert errors == external == []
        browser.close()
