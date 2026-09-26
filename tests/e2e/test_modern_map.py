"""Offline map, view controls and opt-in basemap behaviour."""

from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright


@pytest.fixture
def browser_page(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(live_server) else route.abort())
        yield page
        browser.close()


def configure(page, *, available=False, google=False):
    page.route("**/api/map-config", lambda route: route.fulfill(json={
        "offline_available": available, "google_enabled": google,
        "google_key": "synthetic-browser-key" if google else None,
    }))


def loaded(page, url):
    page.goto(url)
    page.get_by_test_id("overlap-row").first.wait_for()


def map_value(page, expression):
    return page.evaluate("async () => { const {state} = await import('/web/js/state.js'); return " + expression + "; }")


@pytest.mark.parametrize("width,height,theme", [(1440, 900, "light"), (390, 844, "dark")])
def test_real_api_serves_offline_vector_map(browser_page, live_server, width, height, theme):
    """Use the integrated config and Range routes without browser response stubs."""
    page = browser_page
    page.set_viewport_size({"width": width, "height": height})
    page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
    errors, requests, ranges = [], [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("request", lambda request: requests.append(request.url))
    page.on("response", lambda response: ranges.append(response.status)
            if response.url.endswith("/basemap/gasc.pmtiles") else None)
    config = page.request.get(f"{live_server}/api/map-config").json()
    assert config["offline_available"] is True
    assert config["google_enabled"] is False
    assert config["google_key"] is None
    loaded(page, live_server)
    expect(page.get_by_test_id("basemap-status")).to_have_text("Offline street map")
    page.locator("canvas.leaflet-tile-loaded").first.wait_for()
    assert ranges and set(ranges) == {206}
    expect(page.get_by_role("group", name="Base map")).to_be_hidden()
    expect(page.get_by_test_id("state-label")).to_have_count(2)
    expect(page.get_by_test_id("project-feature").first).to_be_attached()
    assert not errors, errors
    assert all(url.startswith(live_server) for url in requests)


def test_initial_both_state_fit_and_actual_wheel_keyboard_zoom(browser_page, live_server):
    page = browser_page
    configure(page)
    loaded(page, live_server)
    assert map_value(page, "state.map.getBounds().contains([[30.35,-85.61],[35.22,-78.49]])"), map_value(page, "state.map.getBounds().toBBoxString()")
    expect(page.get_by_test_id("state-label")).to_have_count(2)
    assert map_value(page, "[state.map.getMinZoom(),state.map.getMaxZoom()]") == [6, 17]
    before = map_value(page, "state.map.getZoom()")
    page.mouse.move(1000, 350)
    page.mouse.wheel(0, -550)
    page.wait_for_function("async z => (await import('/web/js/state.js')).state.map.getZoom() > z", arg=before)
    page.locator("#map").focus()
    before = map_value(page, "state.map.getZoom()")
    page.keyboard.press("+")
    page.wait_for_function("async z => (await import('/web/js/state.js')).state.map.getZoom() > z", arg=before)


def test_panel_scroll_does_not_change_map(browser_page, live_server):
    page = browser_page
    configure(page)
    loaded(page, live_server)
    before = map_value(page, "[state.map.getZoom(),state.map.getCenter().lat,state.map.getCenter().lng]")
    panel = page.locator("#panel-body")
    panel.hover()
    page.mouse.wheel(0, 500)
    page.wait_for_function("() => document.getElementById('panel-body').scrollTop > 0")
    assert map_value(page, "[state.map.getZoom(),state.map.getCenter().lat,state.map.getCenter().lng]") == before


def test_missing_archive_fallback_no_key_and_no_external_requests(browser_page, live_server):
    page = browser_page
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    configure(page)
    loaded(page, live_server)
    expect(page.get_by_test_id("basemap-status")).to_contain_text("Outline map")
    expect(page.get_by_role("group", name="Base map")).to_be_hidden()
    expect(page.get_by_test_id("basemap-feature").first).to_be_attached()
    expect(page.get_by_test_id("project-feature").first).to_be_attached()
    assert all(url.startswith(live_server) for url in requests)
    assert not any("google" in url.lower() for url in requests)


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_real_local_vector_archive_and_line_contrast(browser_page, live_server, theme, width, height, record_property):
    page = browser_page
    page.set_viewport_size({"width": width, "height": height})
    page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
    errors, requests = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("request", lambda request: requests.append(request.url))
    configure(page, available=True)
    archive = Path.home() / "dev" / "gridlock-assets" / "gasc-z13.pmtiles"
    assert archive.is_file(), "Approved offline archive is required for the vector-render check"
    ranges = []

    def serve_range(route):
        raw = route.request.headers["range"].removeprefix("bytes=")
        start, end = map(int, raw.split("-"))
        size = archive.stat().st_size
        end = min(end, size - 1)
        with archive.open("rb") as source:
            source.seek(start)
            body = source.read(end - start + 1)
        ranges.append((start, end))
        route.fulfill(status=206, body=body, headers={
            "Content-Range": f"bytes {start}-{end}/{size}", "Accept-Ranges": "bytes",
            "Content-Type": "application/octet-stream",
        })

    page.route("**/basemap/gasc.pmtiles", serve_range)
    loaded(page, live_server)
    expect(page.get_by_test_id("basemap-status")).to_contain_text("Offline street map")
    page.locator("canvas.leaflet-tile-loaded").first.wait_for()
    assert len(ranges) > 1
    assert page.locator(".leaflet-attribution-flag").count() == 0
    expect(page.locator(".leaflet-control-attribution")).to_contain_text("OpenStreetMap")
    expect(page.locator(".leaflet-control-attribution")).to_contain_text("Protomaps")
    ratios = page.evaluate("""() => {
      const css = getComputedStyle(document.documentElement);
      const luminance = hex => { const rgb = hex.trim().slice(1).match(/../g).map(x => parseInt(x,16)/255).map(x => x <= .04045 ? x/12.92 : ((x+.055)/1.055)**2.4); return rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722; };
      const land = luminance(css.getPropertyValue('--map-land'));
      return ['--dominion','--georgia-power','--meag-power','--gtc','--minor'].map(name => {
        const line = luminance(css.getPropertyValue(name)); return [name,(Math.max(land,line)+.05)/(Math.min(land,line)+.05)];
      });
    }""")
    assert all(ratio >= 3 for _, ratio in ratios), ratios
    record_property("utility_contrast", str(ratios))
    record_property("initial_zoom", map_value(page, "state.map.getZoom()"))
    record_property("minimum_zoom", map_value(page, "state.map.getMinZoom()"))
    assert not errors, errors
    assert all(url.startswith(live_server) for url in requests)
    page.screenshot(path=str(Path.home() / "dev" / "gridlock-runs" / f"modern-map-{width}-{theme}.png"))


def test_phone_controls_and_keyboard_selection(browser_page, live_server):
    page = browser_page
    page.set_viewport_size({"width": 390, "height": 844})
    configure(page)
    loaded(page, live_server)
    assert map_value(page, "state.map.getBounds().contains([[30.35,-85.61],[35.22,-78.49]])"), map_value(page, "state.map.getBounds().toBBoxString()")
    expect(page.get_by_test_id("state-label")).to_have_count(2)
    assert map_value(page, "state.map.getZoom()") >= 5
    assert page.locator("#map").bounding_box()["width"] == 390
    second_row = page.get_by_test_id("overlap-row").nth(1).bounding_box()
    assert second_row["y"] + second_row["height"] <= 844
    for control in page.locator(".leaflet-control-zoom a").all():
        box = control.bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44
        assert box["y"] + box["height"] < page.locator(".panel").bounding_box()["y"]
    page.get_by_test_id("overlap-row").first.get_by_role("button").focus()
    page.keyboard.press("Enter")
    expect(page.locator('[data-testid="project-feature"][data-selected="true"]')).to_have_count(2)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.screenshot(path=str(Path.home() / "dev" / "gridlock-runs" / "modern-map-phone.png"))


def test_google_is_lazy_and_failed_selection_returns_offline(browser_page, live_server):
    page = browser_page
    configure(page, google=True)
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    # Fail the local plugin load, before any Google script can be requested.
    page.route("**/web/vendor/googlemutant/Leaflet.GoogleMutant.js", lambda route: route.abort())
    loaded(page, live_server)
    switch = page.get_by_role("group", name="Base map")
    expect(switch).to_be_visible()
    assert not any("google" in url.lower() for url in requests)
    switch.get_by_role("button", name="Google Maps", exact=True).click()
    expect(page.get_by_test_id("basemap-status")).to_contain_text("Google map unavailable")
    expect(switch.get_by_role("button", name="Map", exact=True)).to_have_attribute("aria-pressed", "true")
    assert all(url.startswith(live_server) for url in requests)


def test_fake_google_switch_satellite_offline_and_phone_targets(browser_page, live_server):
    page = browser_page
    page.set_viewport_size({"width": 390, "height": 844})
    configure(page, google=True)
    page.add_init_script("window.google = {maps:{Map:class {}}}")
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    page.route("**/web/vendor/googlemutant/Leaflet.GoogleMutant.js", lambda route: route.fulfill(
        content_type="text/javascript", body="""
          L.gridLayer.googleMutant = options => {
            window.fakeGoogleType = options.type;
            return new (L.Layer.extend({onAdd() { this.fire('tileload'); }, onRemove() {}}))();
          };
        """))
    loaded(page, live_server)
    group = page.get_by_role("group", name="Base map")
    for button in group.get_by_role("button").all():
        box = button.bounding_box()
        assert box["height"] >= 44 and box["width"] >= 44
    group.get_by_role("button", name="Google Maps", exact=True).click()
    expect(page.get_by_test_id("basemap-status")).to_have_text("Google Maps")
    assert page.evaluate("window.fakeGoogleType") == "roadmap"
    group.get_by_role("button", name="Satellite", exact=True).click()
    expect(page.get_by_test_id("basemap-status")).to_have_text("Satellite map")
    assert page.evaluate("window.fakeGoogleType") == "hybrid"
    group.get_by_role("button", name="Map", exact=True).click()
    expect(page.get_by_test_id("basemap-status")).to_contain_text("Outline map")
    page.evaluate("() => { Object.defineProperty(navigator, 'onLine', {value:false}); dispatchEvent(new Event('offline')); }")
    expect(group).to_be_hidden()
    assert all(url.startswith(live_server) for url in requests)


def test_delayed_google_plugin_preserves_latest_satellite_selection(browser_page, live_server):
    """T16-WEB-SEC-01: shared initialization must not capture the first choice."""
    page = browser_page
    configure(page, google=True)
    page.add_init_script("window.google = {maps:{Map:class {}}}")
    pending, requests = [], []
    page.on("request", lambda request: requests.append(request.url))
    page.route("**/web/vendor/googlemutant/Leaflet.GoogleMutant.js", lambda route: pending.append(route))
    loaded(page, live_server)
    group = page.get_by_role("group", name="Base map")
    group.get_by_role("button", name="Google Maps", exact=True).click()
    expect(page.get_by_test_id("basemap-status")).to_have_text("Loading Google map.")
    group.get_by_role("button", name="Satellite", exact=True).click()
    assert len(pending) == 1
    pending[0].fulfill(content_type="text/javascript", body="""
      L.gridLayer.googleMutant = options => {
        window.fakeGoogleType = options.type;
        return new (L.Layer.extend({onAdd() { this.fire('tileload'); }, onRemove() {}}))();
      };
    """)
    expect(page.get_by_test_id("basemap-status")).to_have_text("Satellite map", timeout=3000)
    expect(group.get_by_role("button", name="Satellite", exact=True)).to_have_attribute("aria-pressed", "true")
    assert page.evaluate("window.fakeGoogleType") == "hybrid"
    assert all(url.startswith(live_server) for url in requests)


@pytest.mark.parametrize("choice,release", [("map", "success"), ("map", "failure"), ("offline", "success")])
def test_cancelled_google_load_cannot_change_offline_choice(browser_page, live_server, choice, release):
    page = browser_page
    configure(page, google=True)
    pending, requests = [], []
    page.on("request", lambda request: requests.append(request.url))
    page.route("**/web/vendor/googlemutant/Leaflet.GoogleMutant.js", lambda route: pending.append(route))
    loaded(page, live_server)
    group = page.get_by_role("group", name="Base map")
    group.get_by_role("button", name="Google Maps", exact=True).click()
    expect(page.get_by_test_id("basemap-status")).to_have_text("Loading Google map.")
    if choice == "map":
        group.get_by_role("button", name="Map", exact=True).click()
    else:
        page.evaluate("() => { Object.defineProperty(navigator, 'onLine', {value:false}); dispatchEvent(new Event('offline')); }")
    expect(page.get_by_test_id("basemap-status")).to_have_text("Outline map: offline street map unavailable.")
    assert len(pending) == 1
    if release == "success":
        pending[0].fulfill(content_type="text/javascript", body="window.delayedPluginFinished = true;")
        page.wait_for_function("() => window.delayedPluginFinished === true")
    else:
        with page.expect_event("requestfailed"):
            pending[0].abort()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_test_id("basemap-status")).to_have_text("Outline map: offline street map unavailable.")
    assert all(url.startswith(live_server) for url in requests)
