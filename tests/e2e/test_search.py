"""Keyboard and failure-path checks for local place and project search."""

from __future__ import annotations

import json

import pytest
from playwright.sync_api import expect, sync_playwright


def focus_search_by_keyboard(page):
    for _ in range(12):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.id") == "search-input":
            return
    raise AssertionError("Search was not reachable by Tab")


@pytest.mark.parametrize("width,height,theme", [(1440, 900, "light"), (390, 844, "dark")])
def test_savannah_keyboard_search_centers_map_and_explores_40_km(live_server, width, height, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        errors = []
        external = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: external.append(request.url) if not request.url.startswith(live_server) else None)
        page.goto(live_server)
        expected = page.request.get(f"{live_server}/api/search?q=Savannah").json()[0]
        assert expected["label"] == "Savannah city"
        focus_search_by_keyboard(page)
        page.keyboard.type("Savannah")
        expect(page.locator("#search-options option")).not_to_have_count(0)
        page.keyboard.press("Enter")
        expect(page.get_by_test_id("search-selection")).to_contain_text("Savannah city")
        assert page.evaluate("""async () => {
          const { state } = await import('/web/js/state.js');
          const center = state.map.getCenter();
          return [center.lat, center.lng, state.map.getZoom()];
        }""") == [expected["lat"], expected["lon"], 11]
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.id") == "explore-area"
        page.keyboard.press("Enter")
        expect(page.get_by_test_id("area-circle")).to_have_count(1)
        expect(page.get_by_test_id("area-selection")).to_contain_text("40 km around Savannah city")
        expect(page.get_by_test_id("area-circle")).to_have_attribute("data-radius-m", "40000")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
        assert errors == []
        assert external == []
        browser.close()


def test_okatie_project_can_be_chosen_by_keyboard_with_source_coordinate(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        expected = next(item for item in page.request.get(f"{live_server}/api/search?q=Okatie").json()
                        if item["type"] == "project" and item["ref"] == "desc-p11")
        focus_search_by_keyboard(page)
        page.keyboard.type("Okatie")
        expect(page.locator("#search-options option")).not_to_have_count(0)
        page.keyboard.press("ControlOrMeta+A")
        page.keyboard.type(expected["label"])
        page.keyboard.press("Enter")
        expect(page.get_by_test_id("search-selection")).to_contain_text(expected["label"])
        assert page.evaluate("""async () => {
          const { state } = await import('/web/js/state.js');
          const center = state.map.getCenter();
          return [center.lat, center.lng];
        }""") == [expected["lat"], expected["lon"]]
        browser.close()


def test_short_and_no_match_queries_leave_no_stale_offer(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        search = page.get_by_label("Search a city or project")
        search.fill("s")
        expect(page.locator("#search-options option")).to_have_count(0)
        expect(page.get_by_test_id("search-state")).to_contain_text("at least 2 characters")
        search.fill("zzzz-no-such-place")
        expect(page.get_by_test_id("search-state")).to_contain_text("No local matches")
        expect(page.locator("#search-options option")).to_have_count(0)
        expect(page.locator("#explore-area")).to_be_hidden()
        browser.close()


def test_search_error_is_visible_and_a_later_query_recovers(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.route("**/api/search?*", lambda route: route.fulfill(status=503, content_type="application/json", body='{"error":{"code":"unavailable","message":"Unavailable"}}'))
        page.goto(live_server)
        search = page.get_by_label("Search a city or project")
        search.fill("Savannah")
        expect(page.get_by_test_id("search-state")).to_contain_text("Search unavailable")
        expect(page.locator("#search-options option")).to_have_count(0)
        page.unroute("**/api/search?*")
        search.fill("Okatie")
        expect(page.locator("#search-options option")).not_to_have_count(0)
        browser.close()


def test_late_search_response_cannot_replace_new_query(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("""(() => {
          const original = window.fetch;
          window.searchGate = {};
          window.fetch = (url, options) => {
            if (String(url).includes('/api/search?q=Savannah')) {
              return new Promise(resolve => { window.searchGate.release = () => resolve({
                ok: true,
                json: async () => {
                  window.searchGate.consumed = true;
                  return [{type:'place', label:'Stale Savannah', lat:32, lon:-81, ref:null}];
                }
              }); });
            }
            return original(url, options);
          };
        })();""")
        page.goto(live_server)
        search = page.get_by_label("Search a city or project")
        search.fill("Savannah")
        page.wait_for_function("typeof window.searchGate.release === 'function'")
        search.fill("Okatie")
        expect(page.locator("#search-options option")).not_to_have_count(0)
        page.evaluate("window.searchGate.release()")
        page.wait_for_function("window.searchGate.consumed === true")
        expect(page.locator("#search-options option[value='Stale Savannah']")).to_have_count(0)
        expect(page.get_by_test_id("search-state")).to_contain_text("Okatie")
        browser.close()


def test_malicious_search_label_is_text_only(live_server):
    malicious = '<img src=x onerror="window.injected=true">'
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.route("**/api/search?*", lambda route: route.fulfill(status=200, content_type="application/json",
                   body=json.dumps([{"type": "place", "label": malicious, "lat": 32.1, "lon": -81.1, "ref": None}])))
        page.goto(live_server)
        search = page.get_by_label("Search a city or project")
        search.fill("malicious")
        expect(page.locator("#search-options option")).to_have_count(1)
        search.press("Enter")
        expect(page.get_by_test_id("search-selection")).to_contain_text(malicious)
        assert page.locator("img[src='x']").count() == 0
        assert page.evaluate("window.injected === undefined")
        browser.close()


def test_two_bluffton_places_can_each_be_selected_by_keyboard(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        expected = [item for item in page.request.get(f"{live_server}/api/search?q=Bluffton").json()
                    if item["type"] == "place" and item["label"] == "Bluffton town"]
        assert len(expected) == 2
        assert len({(item["lat"], item["lon"]) for item in expected}) == 2
        focus_search_by_keyboard(page)
        search = page.get_by_label("Search a city or project")
        search.fill("Bluffton")
        options = page.locator("#search-options option")
        expect(options).to_have_count(2)
        values = options.evaluate_all("nodes => nodes.map(node => node.value)")
        assert len(set(values)) == 2, values
        centers = set()
        for value in values:
            search.fill("Bluffton")
            expect(options).to_have_count(2)
            search.fill(value)
            search.press("Enter")
            expect(page.get_by_test_id("search-selection").locator('[data-src="label"]')).to_have_text("Bluffton town")
            centers.add(tuple(page.evaluate("""async () => {
              const { state } = await import('/web/js/state.js');
              const center = state.map.getCenter();
              return [center.lat, center.lng];
            }""")))
        assert centers == {(item["lat"], item["lon"]) for item in expected}
        browser.close()


def test_duplicate_project_choices_keep_distinct_source_refs(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        expected = page.request.get(f"{live_server}/api/search?q=WANSLEY%20500%20KV").json()
        assert len(expected) == 2
        assert len({item["ref"] for item in expected}) == 2
        search = page.get_by_label("Search a city or project")
        search.fill("WANSLEY 500 KV")
        options = page.locator("#search-options option")
        expect(options).to_have_count(2)
        values = options.evaluate_all("nodes => nodes.map(node => node.value)")
        assert len(set(values)) == 2, values
        assert all(any(item["ref"] in value for value in values) for item in expected)
        browser.close()


def test_old_label_cannot_be_selected_when_current_query_has_no_match(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.route("**/api/search?*", lambda route: route.fulfill(status=200, content_type="application/json", body="[]")
                   if "Bluffton%20town" in route.request.url else route.continue_())
        page.goto(live_server)
        search = page.get_by_label("Search a city or project")
        search.fill("Bluffton")
        expect(page.locator("#search-options option")).to_have_count(2)
        search.fill("zzzz-no-such-place")
        expect(page.get_by_test_id("search-state")).to_contain_text("No local matches")
        search.fill("Bluffton town")
        expect(page.get_by_test_id("search-state")).to_contain_text("No local matches")
        search.press("Enter")
        expect(page.get_by_test_id("search-selection")).to_be_hidden()
        expect(page.locator("#explore-area")).to_be_hidden()
        browser.close()
