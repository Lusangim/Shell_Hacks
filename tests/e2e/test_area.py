"""Area explorer parity, history, accessibility, and deterministic request races."""

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import expect, sync_playwright

from tests.e2e.test_search import focus_search_by_keyboard, wait_for_search_center


def loaded(page, url):
    page.goto(url)
    expect(page.locator("#status")).to_contain_text("ranked opportunities")


def click_empty_map(page, skip=0):
    points = page.evaluate("""() => {
      const rect = document.querySelector('#map').getBoundingClientRect();
      const points = [];
      for (const y of [.3, .4, .5, .25, .6]) for (const x of [.72, .82, .92, .62]) {
        const px = Math.round(rect.left + rect.width * x), py = Math.round(rect.top + rect.height * y);
        const target = document.elementFromPoint(px, py);
        if (document.querySelector('#map').contains(target) &&
            !target.closest('.leaflet-interactive, .leaflet-control, .map-pair-open, .basemap-controls'))
          points.push({x:px, y:py});
      }
      return points;
    }""")
    assert len(points) > skip, "No empty map point available"
    point = points[skip]
    centre = page.evaluate("""async point => {
      const {state} = await import('/web/js/state.js');
      const rect = document.querySelector('#map').getBoundingClientRect();
      const latlng = state.map.containerPointToLatLng([point.x - rect.left, point.y - rect.top]);
      return [latlng.lat, latlng.lng];
    }""", point)
    page.mouse.click(**point)
    return centre


def explore_search(page, name="Savannah"):
    search = page.get_by_label("Search a city or project")
    search.fill(name)
    expect(page.locator("#search-options option")).not_to_have_count(0)
    search.press("Enter")
    expect(page.get_by_test_id("search-selection")).to_be_visible()
    search.press("Tab")
    expect(page.locator("#explore-area")).to_be_focused()
    page.keyboard.press("Enter")


def parity(page, payload):
    expect(page.locator("#area-state")).to_have_text(
        f'{len(payload["projects"])} projects in area; {len(payload["overlaps"])} overlaps with at least one project in area.'
    )
    for field, selector in [("counts_by_utility", "#area-utilities"), ("counts_by_band", "#area-bands")]:
        actual = page.locator(selector + " [data-count-key]").evaluate_all(
            "nodes => Object.fromEntries(nodes.map(node => [node.dataset.countKey, Number(node.querySelector('dd').textContent)]))"
        )
        assert actual == payload[field]
    expect(page.locator("#area-projects li")).to_have_count(len(payload["projects"]))
    expect(page.locator("#area-overlaps li")).to_have_count(len(payload["overlaps"]))
    names = page.locator('#area-projects [data-src="name"]').all_text_contents()
    sources = page.locator('#area-projects [data-src="source"]').all_text_contents()
    assert names == [feature["properties"]["name"] for feature in payload["projects"]]
    assert sources == [f'{feature["properties"]["source"]["doc"]}, p. {feature["properties"]["source"]["page"]}'
                       for feature in payload["projects"]]


def test_map_click_requires_area_mode(live_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        loaded(page, live_server)
        button = page.get_by_role("button", name="Explore an area")
        expect(button).to_have_attribute("aria-pressed", "false")
        click_empty_map(page)
        expect(page.locator("#area-panel")).to_be_hidden()
        expect(page.get_by_test_id("area-circle")).to_have_count(0)
        assert "area" not in parse_qs(urlparse(page.url).query)
        button.click()
        expect(button).to_have_attribute("aria-pressed", "true")
        expect(page.locator("#status")).to_have_text("Click the map to choose the centre of a 40 km area. Esc cancels.")
        assert page.locator("#map").evaluate("el => getComputedStyle(el).cursor") == "crosshair"
        expected_centre = click_empty_map(page)
        expect(page.locator("#area-state")).to_contain_text("projects in area;")
        expect(page.get_by_test_id("area-circle")).to_have_attribute("data-radius-m", "40000")
        expect(button).to_have_attribute("aria-pressed", "false")
        lat, lon = map(float, parse_qs(urlparse(page.url).query)["area"][0].split(","))
        assert abs(lat - expected_centre[0]) < 0.00001
        assert abs(lon - expected_centre[1]) < 0.00001
        browser.close()


@pytest.mark.parametrize("cancel", ["button", "Escape"])
def test_area_mode_cancels_without_selection(live_server, cancel):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(reduced_motion="reduce")
        loaded(page, live_server)
        button = page.get_by_role("button", name="Explore an area")
        button.click()
        if cancel == "button":
            button.click()
        else:
            page.keyboard.press("Escape")
        expect(button).to_have_attribute("aria-pressed", "false")
        expect(page.locator("#area-panel")).to_be_hidden()
        expect(page.get_by_test_id("area-circle")).to_have_count(0)
        click_empty_map(page)
        expect(page.locator("#area-panel")).to_be_hidden()
        assert "area" not in parse_qs(urlparse(page.url).query)
        browser.close()


def test_project_click_keeps_its_behavior_while_area_mode_is_on(live_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        loaded(page, live_server)
        button = page.get_by_role("button", name="Explore an area")
        button.click()
        page.get_by_test_id("project-feature").first.click(force=True)
        expect(page.locator("#project-detail")).to_be_visible()
        expect(page.locator("#area-panel")).to_be_hidden()
        expect(page.get_by_test_id("area-circle")).to_have_count(0)
        expect(button).to_have_attribute("aria-pressed", "true")
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_area_mode_button_keyboard_and_axe(live_server, width, height, theme):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        loaded(page, live_server)
        button = page.get_by_role("button", name="Explore an area", exact=True)
        assert button.get_attribute("title")
        box = button.bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44
        if width <= 700:
            # On phones the button takes the free top-left corner, the first of the map's own controls.
            page.locator("#map").focus()
        else:
            page.locator(".leaflet-control-zoom-out").focus()
        page.keyboard.press("Tab")
        expect(button).to_be_focused()
        outline = button.evaluate("el => getComputedStyle(el).outline")
        assert outline != "none" and not outline.startswith("0px"), outline
        page.keyboard.press("Enter")
        expect(button).to_have_attribute("aria-pressed", "true")
        expect(page.locator("#status")).to_have_attribute("aria-live", "polite")
        axe_source = (Path(__file__).parent / "vendor" / "axe.min.js").read_text(encoding="utf-8")
        violations = page.evaluate(axe_source + "\nwindow.axe.run(document, {runOnly: {type:'tag', values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")["violations"]
        assert not violations, [(item["id"], item["nodes"][0]["target"]) for item in violations]
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_keyboard_area_payload_parity_radius_and_escape_offline(live_server, width, height, theme):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(live_server)
                   else (external.append(route.request.url), route.abort()))
        loaded(page, live_server)
        focus_search_by_keyboard(page)
        place = page.request.get(f"{live_server}/api/search?q=Savannah").json()[0]
        explore_search(page)
        wait_for_search_center(page, place)
        payload = page.request.get(f'{live_server}/api/area?lat={place["lat"]}&lon={place["lon"]}&radius_km=40').json()
        parity(page, payload)
        assert parse_qs(urlparse(page.url).query)["area"] == [f'{place["lat"]},{place["lon"]}']
        expect(page.locator("#status")).to_have_text("40 km area selected.")
        expect(page.get_by_test_id("area-center")).to_have_count(1)
        expect(page.get_by_test_id("area-circle")).to_have_attribute("data-radius-m", "40000")
        expect(page.locator("#area-caveat")).to_contain_text("unknown locations")
        radius = page.get_by_label("Area radius")
        radius.focus()
        radius.press("Home")
        expect(radius).to_have_value("1")
        expect(page.get_by_test_id("area-circle")).to_have_attribute("data-radius-m", "1000")
        radius.press("End")
        expect(radius).to_have_value("80")
        expect(page.locator("#area-state")).to_contain_text("projects in area;")
        assert parse_qs(urlparse(page.url).query)["radius_km"] == ["80"]
        axe_source = (Path(__file__).parent / "vendor" / "axe.min.js").read_text(encoding="utf-8")
        violations = page.evaluate(axe_source + "\nwindow.axe.run(document, {runOnly: {type:'tag', values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")["violations"]
        assert not violations, [(item["id"], item["nodes"][0]["target"]) for item in violations]
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        page.keyboard.press("Escape")
        expect(page.locator("#area-panel")).to_be_hidden()
        expect(page.get_by_test_id("area-circle")).to_have_count(0)
        expect(page.get_by_test_id("area-center")).to_have_count(0)
        expect(page.locator("#explore-area")).to_be_focused()
        assert "area" not in parse_qs(urlparse(page.url).query)
        assert "radius_km" not in parse_qs(urlparse(page.url).query)
        assert errors == external == []
        browser.close()


def test_mouse_area_keeps_pair_and_map_view(live_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        loaded(page, live_server)
        page.locator(".overlap-button").first.click()
        expect(page.locator("#overlap-content")).not_to_be_empty()
        before = page.evaluate("""async () => {const {state}=await import('/web/js/state.js');
          return {id:state.selectedOverlapId, zoom:state.map.getZoom(), center:state.map.getCenter(), hash:location.hash};} """)
        page.get_by_role("button", name="Explore an area").click()
        click_empty_map(page)
        expect(page.locator("#area-state")).to_contain_text("projects in area;")
        params = parse_qs(urlparse(page.url).query)
        lat, lon = params["area"][0].split(",")
        parity(page, page.request.get(f"{live_server}/api/area?lat={lat}&lon={lon}&radius_km=40").json())
        after = page.evaluate("""async () => {const {state}=await import('/web/js/state.js');
          return {id:state.selectedOverlapId, zoom:state.map.getZoom(), center:state.map.getCenter(), hash:location.hash};} """)
        assert after == before
        expect(page.locator("#overlap-detail")).to_be_visible()
        page.keyboard.press("Escape")
        expect(page.locator("#map")).to_be_focused()
        assert urlparse(page.url).fragment == before["hash"][1:]
        browser.close()


def test_area_url_reload_filters_year_and_history(live_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(reduced_motion="reduce")
        loaded(page, live_server + "/?band=lt_40km&year=2029#overlap=desc-p11__sertp-p105-70a041")
        explore_search(page)
        expect(page.locator("#area-state")).to_contain_text("projects in area;")
        page.get_by_label("Area radius").fill("25")
        page.get_by_label("Area radius").dispatch_event("input")
        selected = parse_qs(urlparse(page.url).query)
        page.locator("#filters-toggle").click()
        page.get_by_label("Distance band", exact=True).select_option("lt_8km")
        page.locator("#timeline-year").fill("2030")
        page.locator("#timeline-year").dispatch_event("input")
        assert parse_qs(urlparse(page.url).query)["area"] == selected["area"]
        assert parse_qs(urlparse(page.url).query)["radius_km"] == ["25"]
        page.reload()
        expect(page.get_by_test_id("area-circle")).to_have_attribute("data-radius-m", "25000")
        expect(page.locator("#area-state")).to_contain_text("projects in area;")
        assert parse_qs(urlparse(page.url).query)["band"] == ["lt_8km"]
        assert parse_qs(urlparse(page.url).query)["year"] == ["2030"]
        page.keyboard.press("Escape")
        expect(page.locator("#area-panel")).to_be_hidden()
        page.go_back()
        expect(page.get_by_test_id("area-circle")).to_have_attribute("data-radius-m", "25000")
        page.go_forward()
        expect(page.locator("#area-panel")).to_be_hidden()
        page.locator("#filters-toggle").click()
        page.get_by_label("Distance band", exact=True).select_option("touching")
        page.locator("#timeline-year").fill("2031")
        page.locator("#timeline-year").dispatch_event("input")
        assert "area" not in parse_qs(urlparse(page.url).query)
        assert "radius_km" not in parse_qs(urlparse(page.url).query)
        browser.close()


@pytest.mark.parametrize("failure", [422, 503])
def test_area_failure_retry_is_bound_to_current_center(live_server, failure):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(reduced_motion="reduce")
        page.route("**/api/area?*", lambda route: route.fulfill(status=failure, json={"error": {"code": "unavailable", "message": "Unavailable"}}))
        loaded(page, live_server)
        explore_search(page)
        expect(page.locator("#area-state")).to_contain_text("Could not load")
        explore_search(page, "Okatie")
        expect(page.locator("#area-state")).to_contain_text("Could not load")
        selected = parse_qs(urlparse(page.url).query)["area"][0]
        page.unroute("**/api/area?*")
        with page.expect_response("**/api/area?*") as response:
            page.get_by_role("button", name="Retry area").click()
        params = parse_qs(urlparse(response.value.url).query)
        assert selected == f'{params["lat"][0]},{params["lon"][0]}'
        parity(page, response.value.json())
        browser.close()


@pytest.mark.parametrize("second", ["map", "search", "clear"])
def test_late_area_response_cannot_replace_new_map_or_search_selection(live_server, second):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(reduced_motion="reduce")
        page.add_init_script("""(() => {const original=window.fetch; window.areaGate={};
          window.fetch=(url, options) => {
            if(String(url).startsWith('/api/area?') && !window.areaGate.release) {
              return new Promise(resolve => {window.areaGate.release=()=>resolve({ok:true,json:async()=>{
                window.areaGate.consumed=true;return {center:{lat:0,lon:0},radius_km:40,projects:[],overlaps:[],counts_by_utility:{},counts_by_band:{}};
              }});});
            } return original(url,options);
          };})();""")
        loaded(page, live_server)
        page.get_by_role("button", name="Explore an area").click()
        click_empty_map(page)
        page.wait_for_function("typeof window.areaGate.release === 'function'")
        expect(page.locator("#area-state")).to_contain_text("Loading")
        if second == "search":
            explore_search(page)
        elif second == "map":
            page.get_by_role("button", name="Explore an area").click()
            click_empty_map(page, skip=1)
        else:
            page.keyboard.press("Escape")
        if second != "clear":
            expect(page.locator("#area-state")).to_contain_text("projects in area;")
        before = page.locator("#area-state").inner_text()
        page.evaluate("window.areaGate.release()")
        page.wait_for_function("window.areaGate.consumed === true")
        expect(page.locator("#area-state")).to_have_text(before)
        if second == "search":
            expect(page.get_by_test_id("area-selection")).to_contain_text("Savannah city")
        elif second == "clear":
            expect(page.locator("#area-panel")).to_be_hidden()
            expect(page.get_by_test_id("area-circle")).to_have_count(0)
        browser.close()


def test_area_before_delayed_shell_preserves_existing_url_state(live_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(reduced_motion="reduce")
        held = []
        page.route("**/api/meta", lambda route: held.append(route))
        with page.expect_request("**/api/meta"):
            page.goto(live_server + "/?band=lt_8km&year=2029")
        explore_search(page)
        expect(page.locator("#area-state")).to_contain_text("projects in area;")
        params = parse_qs(urlparse(page.url).query)
        assert params["band"] == ["lt_8km"]
        assert params["year"] == ["2029"]
        held[0].continue_()
        expect(page.locator("#status")).to_contain_text("match filters")
        assert parse_qs(urlparse(page.url).query)["area"] == params["area"]
        browser.close()


def test_empty_area_and_untrusted_source_are_honest_text(live_server):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(reduced_motion="reduce")
        malicious = '<img src=x onerror="window.injected=true">'
        page.route("**/api/area?*", lambda route: route.fulfill(json={
            "center": {"lat": 32, "lon": -81}, "radius_km": 40,
            "projects": [], "overlaps": [], "counts_by_utility": {malicious: 0}, "counts_by_band": {},
        }))
        loaded(page, live_server)
        explore_search(page)
        expect(page.locator("#area-state")).to_contain_text("0 projects in area; 0 overlaps")
        expect(page.locator("#area-caveat")).to_contain_text("unknown locations")
        expect(page.locator("#area-utilities")).to_contain_text(malicious)
        assert page.locator("img[src=x]").count() == 0
        assert page.evaluate("window.injected === undefined")
        browser.close()
