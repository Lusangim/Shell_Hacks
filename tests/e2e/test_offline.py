"""Local-only demo path and source-backed basemap context."""

from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.e2e.test_modern_map import browser_page, configure, loaded, map_value


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_local_archive_county_boundaries(browser_page, live_server, theme, width, height, record_property):
    page = browser_page
    page.set_viewport_size({"width": width, "height": height})
    page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
    loaded(page, live_server)
    expect(page.get_by_test_id("basemap-status")).to_have_text("Offline street map")
    evidence = page.evaluate("""async () => {
      const source = new protomapsL.PmtilesSource('/basemap/gasc.pmtiles');
      // Source tile at the Savannah / Jasper / Chatham county border.
      const tile = await source.get({z:9, x:140, y:207}, 256);
      const boundaries = (tile.get('boundaries') || []).map(f => ({props:f.props, points:f.numVertices}));
      return boundaries;
    }""")
    record_property("boundaries", str(evidence))
    assert any(item["props"].get("kind_detail") == 6 for item in evidence), evidence
    page.evaluate("""async () => {
      const {state} = await import('/web/js/state.js');
      window.countyPaints = [];
      state.map.eachLayer(layer => {
        for (const rule of layer.paintRules || []) {
          if (rule.dataLayer !== 'boundaries') continue;
          const original = rule.symbolizer.draw;
          rule.symbolizer.draw = function(ctx, geometry, zoom, feature) {
            const county = feature.props.kind_detail === 6 && zoom === 9;
            const box = ctx.canvas.getBoundingClientRect();
            const visible = box.right > 0 && box.left < innerWidth && box.bottom > 0 && box.top < innerHeight;
            const probe = county && visible && window.countyPaints.length < 3;
            const before = probe ? ctx.getImageData(0, 0, ctx.canvas.width, ctx.canvas.height).data : null;
            original.call(this, ctx, geometry, zoom, feature);
            if (probe) {
              const after = ctx.getImageData(0, 0, ctx.canvas.width, ctx.canvas.height).data;
              const changed = after.some((value, index) => value !== before[index]);
              window.countyPaints.push({color:ctx.strokeStyle, width:ctx.lineWidth, alpha:ctx.globalAlpha, changed});
            }
          };
        }
      });
      state.map.setView([32.45, -81.2], 9, {animate:false});
      if (innerWidth < 700) state.map.panBy([0, 210], {animate:false});
    }""")
    page.wait_for_function("() => window.countyPaints.some(paint => paint.changed)")
    page.wait_for_function("""async () => {
      const {state} = await import('/web/js/state.js');
      const layers = Object.values(state.map._layers).filter(layer => layer.paintRules);
      return layers.length === 1 && !layers[0].isLoading()
        && Object.values(layers[0]._tiles).every(tile => !tile.current || tile.active);
    }""")
    paints = page.evaluate("window.countyPaints")
    assert all(paint["width"] > 0 and paint["alpha"] > 0 for paint in paints), paints
    assert paints[0]["color"] == ("#5b6374" if theme == "dark" else "#adadad")
    record_property("county_paints", str(paints))
    page.screenshot(path=str(Path.home() / "dev" / "gridlock-runs" / f"T3.5-county-{width}-{theme}.png"))


@pytest.mark.parametrize("available", [True, False])
@pytest.mark.parametrize("width,height,theme", [(1440, 900, "light"), (390, 844, "dark")])
def test_offline_demo_path_remains_usable(browser_page, live_server, available, width, height, theme):
    page = browser_page
    page.set_viewport_size({"width": width, "height": height})
    page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
    configure(page, available=available)
    errors, external = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
    page.on("request", lambda request: external.append(request.url) if not request.url.startswith(live_server) else None)
    loaded(page, live_server)
    expect(page.get_by_test_id("basemap-status")).to_contain_text("Offline street map" if available else "Outline map")
    if available:
        page.locator("canvas.leaflet-tile-loaded").first.wait_for()
    else:
        expect(page.locator('path[data-testid="basemap-feature"]').first).to_be_visible()
    if width == 390:
        page.get_by_role("button", name="Expand opportunities").click()
        expect(page.get_by_test_id("bottom-sheet")).to_have_class("panel expanded")
    page.locator("#filters-toggle").click()
    with page.expect_response(lambda response: "/api/overlaps?" in response.url and response.ok):
        page.locator("#filter-band").select_option("touching")
    expected = page.request.get(f"{live_server}/api/overlaps?band=touching").json()
    expect(page.get_by_test_id("overlap-row")).to_have_count(len(expected))
    page.locator("#filters-toggle").click()
    page.get_by_test_id("overlap-row").first.get_by_role("button").click()
    detail = page.get_by_test_id("overlap-detail")
    expect(detail).to_be_visible()
    sources = detail.locator('a[href*="/sources/"]')
    expect(sources.first).to_be_visible()
    for href in sources.evaluate_all("links => links.map(link => link.href)"):
        response = page.request.get(href.split("#")[0])
        assert response.ok and response.headers["content-type"] == "application/pdf"
    page.locator("#search-input").fill("Savannah")
    expect(page.locator("#search-options option")).not_to_have_count(0)
    page.locator("#search-input").press("Enter")
    expect(page.get_by_test_id("search-selection")).to_contain_text("Savannah city")
    page.locator("#explore-area").click()
    expect(page.get_by_test_id("area-circle")).to_have_attribute("data-radius-m", "40000")
    page.locator(".legend summary").click()
    with page.expect_download() as received:
        page.get_by_role("button", name="Export CSV", exact=True).click()
    assert received.value.suggested_filename == "gridlock-overlaps.csv"
    assert len(Path(received.value.path()).read_bytes()) > 100
    if width == 390:
        page.get_by_role("button", name="Collapse opportunities").click()
        expect(page.get_by_test_id("bottom-sheet")).to_have_class("panel")
    assert map_value(page, "state.map.getZoom()") == 11
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    assert not errors, errors
    assert not external, external


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_stored_dark_theme_is_applied_before_first_visible_frame(browser_page, live_server, width, height):
    page = browser_page
    page.set_viewport_size({"width": width, "height": height})
    configure(page)
    page.add_init_script("""localStorage.setItem('gridlock-theme', 'dark');
      window.themeFrames = [];
      function sample() {
        if (document.body && getComputedStyle(document.body).backgroundColor !== 'rgba(0, 0, 0, 0)') {
          window.themeFrames.push({theme:document.documentElement.dataset.theme, background:getComputedStyle(document.body).backgroundColor});
        }
        requestAnimationFrame(sample);
      }
      requestAnimationFrame(sample);
    """)
    loaded(page, live_server)
    page.reload()
    page.get_by_test_id("overlap-row").first.wait_for()
    page.wait_for_function("() => window.themeFrames.length > 1")
    assert all(frame == {"theme": "dark", "background": "rgb(22, 25, 28)"} for frame in page.evaluate("window.themeFrames"))
    expect(page.get_by_role("button", name="Switch to light theme")).to_be_visible()
    axe_source = (Path(__file__).parent / "vendor" / "axe.min.js").read_text(encoding="utf-8")
    violations = page.evaluate(axe_source + "\nwindow.axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")["violations"]
    assert not violations, [(item["id"], item["nodes"][0]["target"]) for item in violations]
