"""Measured control contrast and initial layout stability regressions."""

import json

import pytest
from playwright.sync_api import expect, sync_playwright

from tests.e2e.test_timeline import set_year


SHIFT_OBSERVER = """() => {
  window.initialShifts = [];
  new PerformanceObserver(list => {
    for (const entry of list.getEntries()) {
      if (entry.hadRecentInput) continue;
      window.initialShifts.push({value: entry.value, sources: entry.sources.map(source => ({
        node: source.node?.id || source.node?.getAttribute?.('class') || source.node?.nodeName,
        previous: source.previousRect.toJSON(), current: source.currentRect.toJSON()
      }))});
    }
  }).observe({type: 'layout-shift', buffered: true});
}"""


ZOOM_CONTRAST = """element => {
  const rgb = value => value.match(/[\\d.]+/g).map(Number);
  const luminance = value => rgb(value).slice(0, 3).map(channel => {
    channel /= 255;
    return channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4;
  }).reduce((sum, channel, index) => sum + channel * [.2126, .7152, .0722][index], 0);
  const ratio = (a, b) => (Math.max(luminance(a), luminance(b)) + .05)
    / (Math.min(luminance(a), luminance(b)) + .05);
  let backing = element.parentElement;
  while (backing && rgb(getComputedStyle(backing).backgroundColor)[3] === 0)
    backing = backing.parentElement;
  const style = getComputedStyle(element);
  const background = getComputedStyle(backing).backgroundColor;
  return {border: style.borderBottomColor, background, fill: style.backgroundColor,
    ratio: Math.min(ratio(style.borderBottomColor, background),
      ratio(style.borderBottomColor, style.backgroundColor))};
}"""


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_zoom_border_contrast_and_touch_target(live_server, width, height, theme):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        page.goto(live_server)
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded")
        zoom = page.locator(".leaflet-control-zoom-in")
        colors = zoom.evaluate(ZOOM_CONTRAST)
        print(f"zoom {width} {theme}: {json.dumps(colors)}")
        assert colors["ratio"] >= 3, colors
        box = zoom.bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44, box
        browser.close()


SURFACE_CONTRAST = r"""(element, kind) => {
  const rgb = value => value.match(/[\d.]+/g).map(Number).slice(0, 3);
  const luminance = color => color.map(channel => {
    channel /= 255;
    return channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4;
  }).reduce((sum, channel, index) => sum + channel * [.2126, .7152, .0722][index], 0);
  const ratio = (a, b) => (Math.max(luminance(a), luminance(b)) + .05)
    / (Math.min(luminance(a), luminance(b)) + .05);
  const style = getComputedStyle(element);
  let opacity = kind === 'stroke' ? Number(style.strokeOpacity) : 1;
  for (let node = element; node; node = node.parentElement) opacity *= Number(getComputedStyle(node).opacity);
  let backing = element;
  while (backing && getComputedStyle(backing).backgroundColor === 'rgba(0, 0, 0, 0)')
    backing = backing.parentElement;
  const background = rgb(kind === 'stroke'
    ? getComputedStyle(document.documentElement).getPropertyValue('--map-land')
      .trim().replace(/^#(..)(..)(..)$/, (_, r, g, b) => `rgb(${parseInt(r,16)},${parseInt(g,16)},${parseInt(b,16)})`)
    : getComputedStyle(backing).backgroundColor);
  const color = rgb(kind === 'stroke' ? style.stroke : kind === 'border' ? style.borderTopColor : style.color);
  const painted = color.map((channel, i) => channel * opacity + background[i] * (1 - opacity));
  return {ratio: ratio(painted, background), color, background, opacity,
    strokeWidth: style.strokeWidth, dash: style.strokeDasharray};
}"""


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_phone_sheet_border_meets_control_contrast(live_server, theme):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844}, color_scheme=theme)
        page.goto(live_server)
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded")
        colors = page.locator("#sheet-toggle").evaluate(SURFACE_CONTRAST, "border")
        print(f"sheet border {theme}: {json.dumps(colors)}")
        assert colors["ratio"] >= 3, colors
        browser.close()


@pytest.mark.parametrize("motion", ["no-preference", "reduce"])
def test_phone_sheet_has_no_layout_property_transition(live_server, motion):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion=motion)
        page.goto(live_server)
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded")
        page.locator("#sheet-toggle").click()
        transition = page.locator(".panel").evaluate("element => ({property: getComputedStyle(element).transitionProperty, duration: getComputedStyle(element).transitionDuration})")
        print(f"sheet motion {motion}: {json.dumps(transition)}")
        assert transition["duration"] == "0s" or set(transition["property"].split(", ")) <= {"transform", "opacity"}, transition
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_phone_skip_attribution_and_source_targets(live_server, theme):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844}, color_scheme=theme)
        page.goto(live_server)
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded")
        page.locator(".skip-link").focus()
        sizes = [{"name": "skip", **page.locator(".skip-link").bounding_box()}]
        for link in page.locator(".leaflet-control-attribution a").all():
            sizes.append({"name": link.text_content(), **link.bounding_box()})
            assert link.evaluate("""element => {
              const box = element.getBoundingClientRect();
              return [box.top + 2, box.bottom - 2].every(y =>
                element.contains(document.elementFromPoint(box.x + box.width / 2, y)));
            }"""), "Attribution target is covered by another control"
        page.locator("#sheet-toggle").click()
        page.locator("#unknown-locations").evaluate("element => { element.open = true; }")
        for link in page.locator('#unknown-list a[data-src="source"]').all():
            sizes.append({"name": "source", **link.bounding_box()})
        assert any(size["name"] == "source" for size in sizes)
        print(f"phone targets {theme}: {json.dumps(sizes[:3])}; source minimum height={min(size['height'] for size in sizes[3:])}")
        assert all(size["width"] >= 44 and size["height"] >= 44 for size in sizes), sizes
        source = page.locator('#unknown-list a[data-src="source"]').first
        source.focus()
        expect(source).to_be_focused()
        source_box = source.bounding_box()
        assert 0 <= source_box["y"] and source_box["y"] + source_box["height"] <= 844
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_late_year_text_keeps_contrast(live_server, width, height, theme):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, color_scheme=theme)
        page.goto(live_server)
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded")
        if width == 390:
            page.locator("#sheet-toggle").click()
        set_year(page, 2035)
        row = page.locator('.overlap-row[data-timeline="outside"]').first
        measures = {selector: row.locator(selector).first.evaluate(SURFACE_CONTRAST, "text")
                    for selector in (".row-name", ".row-accuracy", "[data-src=utility]", ".row-band")}
        print(f"late text {width} {theme}: {json.dumps(measures)}")
        assert all(value["ratio"] >= 4.5 for value in measures.values()), measures
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_late_year_map_strokes_keep_contrast_and_year_encoding(live_server, width, height, theme):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, color_scheme=theme)
        page.goto(live_server)
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded")
        set_year(page, 2035)
        paths = page.get_by_test_id("project-feature")
        measures = [path.evaluate(SURFACE_CONTRAST, "stroke") for path in paths.all()]
        minimum = min(value["ratio"] for value in measures)
        print(f"late strokes {width} {theme}: minimum={minimum:.6f}; count={len(measures)}")
        assert minimum >= 3, sorted(measures, key=lambda value: value["ratio"])[:3]
        entering = page.locator('[data-testid="project-feature"][data-timeline="entering"]').first
        project_id = entering.get_attribute("data-project-id")
        entering = page.locator(f'[data-testid="project-feature"][data-project-id="{project_id}"]')
        before = entering.evaluate(SURFACE_CONTRAST, "stroke")
        page.locator("#timeline-all").click()
        after = entering.evaluate(SURFACE_CONTRAST, "stroke")
        assert before["strokeWidth"] != after["strokeWidth"], (before, after)
        assert before["dash"] == after["dash"], (before, after)
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("view", ["default", "area"])
def test_initial_layout_shift_stays_below_contract(live_server, width, height, theme, view):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        page.add_init_script(f"({SHIFT_OBSERVER})()")
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(live_server)
                   else (external.append(route.request.url), route.abort()))
        suffix = "?area=32.08,-81.10&radius_km=40" if view == "area" else ""
        page.goto(live_server + suffix)
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded")
        if view == "area":
            expect(page.locator("#area-state")).to_contain_text("projects in area")
        elif width == 390:
            second_row = page.get_by_test_id("overlap-row").nth(1).bounding_box()
            assert second_row["y"] + second_row["height"] <= height
            assert page.locator(".panel").bounding_box()["y"] > 0
        page.wait_for_timeout(800)
        shifts = page.evaluate("window.initialShifts")
        total = sum(entry["value"] for entry in shifts)
        print(f"shift {view} {width} {theme}: {total:.6f} {json.dumps(shifts)}")
        assert total < .1, shifts
        assert errors == []
        assert external == []
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_phone_area_reload_keeps_restored_sheet_stable(live_server, theme):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844}, color_scheme=theme)
        page.add_init_script(f"({SHIFT_OBSERVER})()")
        page.goto(live_server + "?area=32.08,-81.10&radius_km=40")
        expect(page.locator("#area-state")).to_contain_text("projects in area")
        page.reload()
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded")
        expect(page.locator("#area-state")).to_contain_text("projects in area")
        expect(page.locator("#sheet-toggle")).to_have_attribute("aria-expanded", "true")
        assert page.locator("html").get_attribute("data-area-layout") is None
        page.wait_for_timeout(800)
        shifts = page.evaluate("window.initialShifts")
        assert sum(entry["value"] for entry in shifts) < .1, shifts
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("query,normalized_area", [
    ("area=not-coordinates", False), ("area=91,-81", False),
    ("area=32,-81&radius_km=81", True),
])
def test_invalid_area_url_releases_reserved_phone_layout(live_server, theme, query, normalized_area):
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844}, color_scheme=theme)
        page.goto(live_server + "?" + query)
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded")
        expect(page.locator("#area-panel")).to_be_hidden()
        expect(page.locator("#sheet-toggle")).to_have_attribute("aria-expanded", "false")
        assert page.locator("html").get_attribute("data-area-layout") is None
        assert "expanded" not in page.locator(".panel").get_attribute("class")
        assert abs(page.locator(".panel").bounding_box()["height"] - 844 * .58) < 1
        page.reload()
        expect(page.locator("#status")).to_contain_text("ranked opportunities loaded")
        assert page.locator("html").get_attribute("data-area-layout") is None
        if normalized_area:
            # Existing filters retain the valid centre and remove only the invalid radius.
            expect(page.locator("#area-state")).to_contain_text("projects in area")
            expect(page.locator("#area-radius")).to_have_value("40")
            expect(page.locator("#sheet-toggle")).to_have_attribute("aria-expanded", "true")
        else:
            expect(page.locator("#area-panel")).to_be_hidden()
            expect(page.locator("#sheet-toggle")).to_have_attribute("aria-expanded", "false")
            assert abs(page.locator(".panel").bounding_box()["height"] - 844 * .58) < 1
        browser.close()
