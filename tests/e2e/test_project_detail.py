"""Project detail stays source-backed from map and keyboard entry."""

from __future__ import annotations

import pytest
from playwright.sync_api import expect, sync_playwright


def open_project_from_panel(page, project_id: str, name: str):
    for _ in range(12):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.id") == "projects-toggle":
            break
    else:
        raise AssertionError("Projects control was not reachable by Tab")
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.id") == "project-filter"
    page.keyboard.type(name)
    button = page.locator(f'[data-testid="project-row"][data-project-ref="{project_id}"] button')
    expect(button).to_be_visible()
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement === document.querySelector('[data-project-ref=\"%s\"] button')" % project_id)
    page.keyboard.press("Enter")
    expect(page.get_by_test_id("project-detail")).to_be_visible()


def test_project_panel_keyboard_shows_plan_cost_local_page_and_no_overlap(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(live_server)
        project = next(item for item in page.request.get(f"{live_server}/api/projects").json()["features"]
                       if item["properties"]["id"] == "desc-p1")
        props = project["properties"]
        open_project_from_panel(page, "desc-p1", props["name"])
        detail = page.get_by_test_id("project-detail")
        expect(detail.locator('#project-detail-heading')).to_have_text(props["name"])
        expect(detail.locator('[data-src="description"]')).to_have_text(props["description"])
        expect(detail.locator('[data-src="accuracy"]')).to_contain_text("approximate")
        expect(detail.locator('[data-src="cost_usd"]')).to_contain_text("$15,775,885")
        expect(detail).to_contain_text("no overlap within 40 km")
        source = detail.get_by_role("link", name=f"{props['source']['doc']}, p. 1")
        expect(source).to_have_attribute("href", "/api/sources/desc-scrtp-2026-2030#page=1")
        assert page.request.get(f"{live_server}/api/sources/desc-scrtp-2026-2030").status == 200
        expect(page.locator("#no-overlap")).to_contain_text("projects have no overlap within 40 km")
        page.get_by_role("button", name="Back to projects").click()
        expect(page.locator('[data-testid="project-row"][data-project-ref="desc-p1"]')).to_be_visible()
        browser.close()


def test_map_click_opens_project_without_losing_overlap_selection(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(live_server)
        projects = page.request.get(f"{live_server}/api/projects").json()["features"]
        pairs = page.request.get(f"{live_server}/api/overlaps").json()
        paired_ids = list({project_id for pair in pairs for project_id in (pair["a"], pair["b"])})
        project_id = page.wait_for_function("""ids => {
          const paths = Array.from(document.querySelectorAll('[data-testid="project-feature"]'));
          return paths.map(path => {
            const box = path.getBoundingClientRect();
            const x = box.left + box.width / 2;
            const y = box.top + box.height / 2;
            return {id: path.dataset.projectId, hit: document.elementFromPoint(x, y) === path,
              x, y};
          }).find(item => ids.includes(item.id) && item.hit && item.x > 450
            && item.x < innerWidth - 20 && item.y > 20 && item.y < innerHeight - 20)?.id;
        }""", arg=paired_ids, timeout=5000).json_value()
        assert project_id is not None
        feature = page.locator(f'[data-testid="project-feature"][data-project-id="{project_id}"]')
        expect(feature).to_be_visible()
        feature.click()
        detail = page.get_by_test_id("project-detail")
        expect(detail).to_be_visible()
        props = next(item["properties"] for item in projects if item["properties"]["id"] == project_id)
        expect(detail.locator('#project-detail-heading')).to_have_text(props["name"])
        expected_pair = next(pair for pair in pairs if pair["a"] == project_id or pair["b"] == project_id)
        expect(page.locator(f'[data-testid="overlap-row"][data-overlap-id="{expected_pair["id"]}"] button')).to_have_attribute("aria-pressed", "true")
        assert page.locator('[data-testid="project-feature"][data-project-id="%s"]' % project_id).count() == 1
        browser.close()


def test_unstated_sertp_cost_uses_local_source_link(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        props = next(item["properties"] for item in page.request.get(f"{live_server}/api/projects").json()["features"]
                     if item["properties"]["id"] == "sertp-p169-30def7")
        open_project_from_panel(page, props["id"], props["name"])
        detail = page.get_by_test_id("project-detail")
        expect(detail.locator('[data-src="cost_usd"]')).to_have_text("not stated")
        expect(detail.get_by_role("link")).to_have_attribute("href", "/api/sources/sertp-2025-rtp#page=169")
        browser.close()


@pytest.mark.parametrize("width,height,theme", [
    (1440, 900, "light"), (1440, 900, "dark"),
    (768, 844, "light"), (768, 844, "dark"),
    (390, 844, "light"), (390, 844, "dark"),
    (320, 844, "light"), (320, 844, "dark"),
])
def test_detail_is_readable_on_desktop_and_phone_with_visible_focus(live_server, width, height, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(live_server)
        open_project_from_panel(page, "desc-p1", "Summerville")
        detail = page.get_by_test_id("project-detail")
        expect(detail).to_be_visible()
        link = detail.get_by_role("link")
        page.keyboard.press("Tab")
        assert link.evaluate("element => document.activeElement === element")
        assert link.evaluate("element => getComputedStyle(element).outlineStyle") != "none"
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
        assert errors == []
        browser.close()


def test_missing_page_stays_plain_source_text_and_malicious_fields_are_safe(live_server):
    malicious = '<img src=x onerror="window.injected=true">'
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()

        def mutate(route):
            payload = route.fetch().json()
            props = next(item["properties"] for item in payload["features"] if item["properties"]["id"] == "desc-p1")
            props["name"] = malicious
            props["description"] = malicious
            props["source"]["page"] = None
            props["source"]["url"] = "https://untrusted.example/plan.pdf"
            route.fulfill(json=payload)

        page.route("**/api/projects", mutate)
        page.goto(live_server)
        open_project_from_panel(page, "desc-p1", malicious)
        detail = page.get_by_test_id("project-detail")
        expect(detail.locator('#project-detail-heading')).to_have_text(malicious)
        expect(detail.locator('[data-src="description"]')).to_have_text(malicious)
        expect(detail.locator('[data-src="source"]')).to_contain_text("SCRTP Planned Facilities")
        expect(detail.get_by_role("link")).to_have_count(0)
        assert page.locator("img[src='x']").count() == 0
        assert page.evaluate("window.injected === undefined")
        browser.close()


def test_project_list_empty_and_failed_load_are_distinct(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.route("**/api/projects", lambda route: route.fulfill(status=200, content_type="application/json", body='{"type":"FeatureCollection","features":[]}'))
        page.route("**/api/overlaps", lambda route: route.fulfill(status=200, content_type="application/json", body="[]"))
        page.goto(live_server)
        page.get_by_role("button", name="Projects", exact=True).click()
        expect(page.get_by_test_id("projects-state")).to_contain_text("No projects in the loaded plans")
        page.unroute("**/api/projects")
        page.route("**/api/projects", lambda route: route.fulfill(status=503, content_type="application/json", body='{"error":{"code":"unavailable","message":"Unavailable"}}'))
        page.reload()
        page.get_by_role("button", name="Projects", exact=True).click()
        expect(page.get_by_test_id("projects-state")).to_contain_text("Could not load public plan data")
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_production_phone_keeps_two_rows_map_and_projects_target(live_server, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").nth(1)).to_be_visible()
        layout = page.evaluate("""() => {
          const rows = Array.from(document.querySelectorAll('[data-testid="overlap-row"]'));
          const body = document.querySelector('.panel-body').getBoundingClientRect();
          const target = document.querySelector('#projects-toggle').getBoundingClientRect();
          const zoom = document.querySelector('.leaflet-control-zoom-in').getBoundingClientRect();
          return {
            rowTop: rows[0].getBoundingClientRect().top,
            rowBottom: rows[1].getBoundingClientRect().bottom,
            panelBottom: body.bottom,
            targetWidth: target.width, targetHeight: target.height,
            mapControlVisible: zoom.width >= 24 && zoom.height >= 24 && zoom.bottom < innerHeight
              && zoom.right <= innerWidth && zoom.bottom <= document.querySelector('.panel').getBoundingClientRect().top,
            overflow: document.documentElement.scrollWidth - innerWidth,
          };
        }""")
        assert layout["rowTop"] >= 0 and layout["rowBottom"] <= layout["panelBottom"], layout
        assert layout["rowBottom"] <= 844, layout
        assert layout["targetWidth"] >= 44 and layout["targetHeight"] >= 44, layout
        assert layout["mapControlVisible"], layout
        assert layout["overflow"] <= 1, layout
        assert errors == []
        browser.close()
