"""Keyboard and failure-path checks for local place and project search."""

from __future__ import annotations

import json

import pytest
from playwright.sync_api import expect, sync_playwright


def focus_search_by_keyboard(page):
    visited = page.evaluate_handle("new Set()")
    try:
        for _ in range(page.locator("*").count() + 1):
            page.keyboard.press("Tab")
            reached = page.evaluate("""visited => {
              const element = document.activeElement;
              if (element.id === 'search-input') return 'search';
              if (visited.has(element)) return 'loop';
              visited.add(element);
              return 'next';
            }""", visited)
            if reached == "search":
                return
            assert reached != "loop", "Tab focus looped before reaching search"
    finally:
        visited.dispose()
    raise AssertionError("Search was not reachable by Tab")


def wait_for_search_center(page, result):
    page.evaluate("""async () => {
      const { state } = await import('/web/js/state.js');
      window.searchMap = state.map;
    }""")
    page.wait_for_function("""([lat, lon]) => {
      const center = window.searchMap.getCenter();
      return center.lat === lat && center.lng === lon && window.searchMap.getZoom() === 11;
    }""", arg=[result["lat"], result["lon"]])


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
@pytest.mark.parametrize("reduced_motion", ["no-preference", "reduce"])
def test_keyboard_search_keeps_source_center_after_delayed_meta(
    live_server, width, height, reduced_motion
):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion=reduced_motion)
        held_meta = []
        page.route("**/api/meta", lambda route: held_meta.append(route))
        with page.expect_request("**/api/meta"):
            page.goto(live_server)
        expect(page.get_by_test_id("loading-state")).to_be_visible()
        expected = page.request.get(f"{live_server}/api/search?q=Savannah").json()[0]
        assert expected["label"] == "Savannah city"
        focus_search_by_keyboard(page)
        page.keyboard.type("Savannah")
        expect(page.locator("#search-options option")).not_to_have_count(0)
        page.keyboard.press("Enter")
        expect(page.get_by_test_id("search-selection")).to_contain_text(expected["label"])
        wait_for_search_center(page, expected)
        assert len(held_meta) == 1
        held_meta[0].continue_()
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded.")
        assert page.evaluate("""() => {
          const center = window.searchMap.getCenter();
          return [center.lat, center.lng, window.searchMap.getZoom()];
        }""") == [expected["lat"], expected["lon"], 11]
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_untouched_first_view_fits_both_states_after_delayed_meta(live_server, width, height):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        held_meta = []
        page.route("**/api/meta", lambda route: held_meta.append(route))
        with page.expect_request("**/api/meta"):
            page.goto(live_server)
        expect(page.get_by_test_id("loading-state")).to_be_visible()
        assert len(held_meta) == 1
        held_meta[0].continue_()
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded.")
        assert page.evaluate("""async () => {
          const { state } = await import('/web/js/state.js');
          const states = state.basemap.features.filter(feature =>
            ['state', 'state_outline'].includes(feature.properties?.kind));
          return states.length === 2 && states.every(feature =>
            state.map.getBounds().contains(L.geoJSON(feature).getBounds()));
        }""")
        browser.close()


@pytest.mark.parametrize("width,height,theme", [(1440, 900, "light"), (390, 844, "dark")])
@pytest.mark.parametrize("reduced_motion", ["no-preference", "reduce"])
def test_keyboard_search_flies_to_source_coordinates_and_respects_reduced_motion(
    live_server, width, height, theme, reduced_motion
):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion=reduced_motion)
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        page.goto(live_server)
        expected = page.request.get(f"{live_server}/api/search?q=Savannah").json()[0]
        assert expected["label"] == "Savannah city"
        page.evaluate("""async () => {
          const { state } = await import('/web/js/state.js');
          const flyTo = state.map.flyTo;
          window.searchFlights = [];
          state.map.flyTo = function (center, zoom, options) {
            window.searchFlights.push({ center, zoom, animate: options.animate });
            return flyTo.call(this, center, zoom, options);
          };
        }""")
        focus_search_by_keyboard(page)
        page.keyboard.type("Savannah")
        expect(page.locator("#search-options option")).not_to_have_count(0)
        page.keyboard.press("Enter")
        expect(page.get_by_test_id("search-selection")).to_contain_text(expected["label"])
        assert page.evaluate("window.searchFlights") == [{
            "center": [expected["lat"], expected["lon"]],
            "zoom": 11,
            "animate": reduced_motion != "reduce",
        }]
        wait_for_search_center(page, expected)
        assert page.evaluate("""async () => {
          const { state } = await import('/web/js/state.js');
          const center = state.map.getCenter();
          return [center.lat, center.lng, state.map.getZoom()];
        }""") == [expected["lat"], expected["lon"], 11]
        browser.close()


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
        wait_for_search_center(page, expected)
        assert page.evaluate("""async () => {
          const { state } = await import('/web/js/state.js');
          const center = state.map.getCenter();
          return [center.lat, center.lng, state.map.getZoom()];
        }""") == [expected["lat"], expected["lon"], 11]
        page.keyboard.press("Tab")
        expect(page.locator("#filters-toggle")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.locator("#more-toggle")).to_be_focused()
        visited = set()
        for _ in range(32):
            page.keyboard.press("Tab")
            focused = page.evaluate("""() => ({
              index: [...document.querySelectorAll('*')].indexOf(document.activeElement),
              id: document.activeElement.id
            })""")
            if focused["id"] == "explore-area":
                break
            assert focused["index"] not in visited, "Keyboard route cycled before Explore this area"
            visited.add(focused["index"])
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
        wait_for_search_center(page, expected)
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
        for value, result in zip(values, expected, strict=True):
            search.fill("Bluffton")
            expect(options).to_have_count(2)
            search.fill(value)
            search.press("Enter")
            expect(page.get_by_test_id("search-selection").locator('[data-src="label"]')).to_have_text("Bluffton town")
            assert value == f'Bluffton town (place {expected.index(result) + 1} of 2)'
            wait_for_search_center(page, result)
            centers.add(tuple(page.evaluate("""async () => {
              const { state } = await import('/web/js/state.js');
              const center = state.map.getCenter();
              return [center.lat, center.lng];
            }""")))
        assert centers == {(item["lat"], item["lon"]) for item in expected}
        browser.close()


@pytest.mark.parametrize("width", [1440, 390])
@pytest.mark.parametrize("query", ["WANSLEY 500 KV", "GTC: MCDONOUGH – SOUTH GRIFFIN"])
def test_duplicate_project_choices_keep_distinct_source_refs(live_server, width, query):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900}, reduced_motion="reduce")
        page.goto(live_server)
        expected = page.request.get(f"{live_server}/api/search", params={"q": query}).json()
        assert len(expected) == 2
        assert len({item["ref"] for item in expected}) == 2
        search = page.get_by_label("Search a city or project")
        search.fill(query)
        options = page.locator("#search-options option")
        expect(options).to_have_count(2)
        values = options.evaluate_all("nodes => nodes.map(node => node.value)")
        assert len(set(values)) == 2, values
        labels = options.evaluate_all("nodes => nodes.map(node => node.label)")
        assert values == labels
        assert all("desc-p" not in value and "sertp-p" not in value for value in values)
        for index, (value, result) in enumerate(zip(values, expected, strict=True), 1):
            assert value == f'{result["label"]} (project {index} of 2)'
            search.fill(query)
            expect(options).to_have_count(2)
            search.fill(value)
            search.press("Enter")
            expect(search).to_have_value(value)
            expect(page.get_by_test_id("search-selection")).to_contain_text(result["label"])
            wait_for_search_center(page, result)
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
