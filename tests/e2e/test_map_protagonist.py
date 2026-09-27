"""Founder map-first shell and disclosure regression checks."""

from playwright.sync_api import expect, sync_playwright


def test_three_panes_and_more_disclosure(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(live_server)
        row = page.get_by_test_id("overlap-row").first
        expect(row).to_be_visible()
        expect(page.locator(".app-bar #search-input")).to_be_visible()
        more = page.get_by_role("button", name="More", exact=True)
        expect(more).to_have_attribute("aria-controls", "more-menu")
        more.click()
        expect(more).to_have_attribute("aria-expanded", "true")
        expect(page.locator("#more-menu #export-csv")).to_be_visible()
        page.keyboard.press("Escape")
        expect(more).to_be_focused()
        expect(more).to_have_attribute("aria-expanded", "false")
        row.locator("button").click()
        expect(page.locator("#overlap-detail")).to_be_visible()
        expect(page.get_by_test_id("overlap-row").nth(1)).to_be_visible()
        left = page.locator(".panel").bounding_box()
        center = page.locator(".map-region").bounding_box()
        right = page.locator(".detail-pane").bounding_box()
        assert left["x"] + left["width"] <= center["x"] + 1
        assert center["x"] + center["width"] <= right["x"] + 1
        page.screenshot(path="C:/Users/lucia/dev/gridlock-runs/codex/redesign-shell.png")
        browser.close()


def test_filters_tab_exit_keeps_phone_focus_visible(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        page.locator("#filters-toggle").click()
        page.locator("#filter-clear").focus()
        page.keyboard.press("Tab")
        expect(page.locator("#filter-panel")).to_be_hidden()
        assert page.evaluate("document.activeElement.getClientRects().length > 0")
        browser.close()


def test_map_project_back_returns_to_visible_list(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        project_id = page.wait_for_function("""() => [...document.querySelectorAll('[data-testid="project-feature"]')]
          .find(el => { const r=el.getBoundingClientRect(); return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===el; })?.dataset.projectId""").json_value()
        page.locator(f'[data-testid="project-feature"][data-project-id="{project_id}"]').click()
        expect(page.locator("#project-detail")).to_be_visible()
        page.locator("#project-back").click()
        expect(page.locator("#opportunities")).to_be_focused()
        expect(page.locator("#opportunities")).to_be_visible()
        browser.close()


def test_more_tab_exit_and_projects_return_keep_focus_visible(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        more = page.get_by_role("button", name="More", exact=True)
        more.click()
        page.locator("#theme-toggle").focus()
        page.keyboard.press("Tab")
        expect(page.locator("#more-menu")).to_be_hidden()
        more.click()
        page.locator("#projects-toggle").click()
        expect(page.locator("#project-filter")).to_be_focused()
        more.click()
        page.locator("#projects-toggle").click()
        expect(page.locator("#opportunities")).to_be_focused()
        expect(page.locator("#more-menu")).to_be_hidden()
        browser.close()


def test_phone_detail_yields_to_keyboard_map_controls(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(live_server)
        page.get_by_test_id("overlap-row").first.locator("button").click()
        expect(page.locator("#overlap-content")).not_to_be_empty()
        slider = page.locator("#timeline-year")
        slider.focus()
        expect(page.locator(".detail-pane")).to_be_hidden()
        expect(slider).to_be_focused()
        assert slider.evaluate("el => { const r=el.getBoundingClientRect(); return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2) === el; }")
        browser.close()


def test_pair_facts_disclosures_and_explicit_brief(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(live_server)
        row = page.get_by_test_id("overlap-row").first
        expect(row).to_be_visible()
        pair_id = row.get_attribute("data-overlap-id")
        payload = page.request.get(f"{live_server}/api/overlaps/{pair_id}").json()
        row.locator("button").click()
        expect(page.locator("#overlap-detail-heading")).to_have_text(f'Pair {payload["overlap"]["rank"]}')
        expect(page.locator(".pair-facts dt")).to_have_text([
            "Proximity", "Distance", "Years (in service)", "Coordination window", "Score", "Possible saving"])
        expect(page.locator("#pair-summary [data-src='summary_name']")).to_have_text([
            payload["project_a"]["properties"]["name"], payload["project_b"]["properties"]["name"]])
        expect(page.locator("#overlap-content .detail-block")).to_have_count(7)
        page.wait_for_function("() => !document.querySelector('.leaflet-zoom-anim')")
        page.screenshot(path="C:/Users/lucia/dev/gridlock-runs/codex/redesign-detail-overview.png")
        expect(page.locator(".overlap-projects")).to_be_hidden()
        page.locator("#pair-projects").click()
        expect(page.locator(".overlap-projects")).to_be_visible()
        expect(page.locator(".overlap-projects a[data-src='source']")).to_have_count(2)
        expect(page.locator("#brief-panel")).to_be_hidden()
        page.get_by_role("button", name="Open brief", exact=True).click()
        expect(page.locator("#brief-panel")).to_be_visible()
        expect(page.locator("#brief-copy")).to_be_enabled()
        expect(page.locator("#brief-heading")).to_be_focused()
        page.get_by_role("button", name="Back to pair detail", exact=True).click()
        expect(page.locator("#brief-panel")).to_be_hidden()
        expect(page.locator("#open-brief")).to_be_focused()
        page.screenshot(path="C:/Users/lucia/dev/gridlock-runs/codex/redesign-detail.png")
        browser.close()


def test_phone_tour_exposes_timeline(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        page.locator("#more-toggle").click()
        page.locator("#tour-launch").click()
        for _ in range(12):
            title = page.locator("#tour-heading").inner_text()
            if title == "Compare years":
                break
            page.locator("#tour-card").get_by_role("button", name="Next", exact=True).click()
            expect(page.locator("#tour-heading")).not_to_have_text(title)
        expect(page.locator("#tour-heading")).to_have_text("Compare years")
        slider = page.locator("#timeline-year")
        assert slider.evaluate("el => { const r=el.getBoundingClientRect(); return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2) === el; }")
        browser.close()


def test_nearest_geometry_midpoint_uses_segments_not_bounds(live_server):
    cases = [
        ({"type":"Point","coordinates":[0,0]}, {"type":"Point","coordinates":[4,2]}, [2,1]),
        ({"type":"Point","coordinates":[2,3]}, {"type":"LineString","coordinates":[[0,0],[4,0]]}, [2,1.5]),
        ({"type":"Point","coordinates":[7,3]}, {"type":"LineString","coordinates":[[0,0],[4,0]]}, [5.5,1.5]),
        ({"type":"LineString","coordinates":[[-2,-2],[2,2]]}, {"type":"LineString","coordinates":[[-2,2],[2,-2]]}, [0,0]),
        ({"type":"LineString","coordinates":[[0,0],[4,0]]}, {"type":"LineString","coordinates":[[2,0],[6,0]]}, [4,0]),
        ({"type":"LineString","coordinates":[[0,0],[4,0]]}, {"type":"LineString","coordinates":[[0,2],[4,2]]}, [0,1]),
        ({"type":"LineString","coordinates":[[1,1],[1,1]]}, {"type":"Point","coordinates":[3,1]}, [2,1]),
        ({"type":"MultiLineString","coordinates":[[[0,0],[1,0]],[[9,0],[10,0]]]}, {"type":"Point","coordinates":[5,1]}, [3,.5]),
        (None, {"type":"Point","coordinates":[1,1]}, None),
        ({"type":"LineString","coordinates":[]}, {"type":"Point","coordinates":[1,1]}, None),
    ]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        actual = page.evaluate("""async cases => {
          const {nearestGeometryMidpoint}=await import('/web/js/nearest-geometry.js');
          return cases.map(([a,b])=>nearestGeometryMidpoint(a,b));
        }""", cases)
        for index, (result, (_, _, expected)) in enumerate(zip(actual, cases)):
            assert result == expected, (index, result, expected)
        browser.close()


def test_rank_marker_crossing_lifecycle_and_accessibility(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width":1440,"height":900}, reduced_motion="reduce")
        pairs = page.request.get(live_server + "/api/overlaps").json()
        pair = pairs[0]
        geometries = {
            pair["a"]: {"type":"LineString","coordinates":[[-81,32],[-80.9,32]]},
            pair["b"]: {"type":"LineString","coordinates":[[-80.98,31.99],[-80.98,32.04]]},
        }
        def projects(route):
            payload = route.fetch().json()
            for feature in payload["features"]:
                if feature["properties"]["id"] in geometries:
                    feature["geometry"] = geometries[feature["properties"]["id"]]
            route.fulfill(json=payload)
        def detail(route):
            payload = route.fetch().json()
            for key in ("project_a", "project_b"):
                payload[key]["geometry"] = geometries[payload[key]["properties"]["id"]]
            route.fulfill(json=payload)
        page.route("**/api/projects", projects)
        page.route(f'**/api/overlaps/{pair["id"]}', detail)
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        expect(page.get_by_test_id("pair-rank-marker")).to_have_count(0)
        page.get_by_test_id("overlap-row").first.locator("button").click()
        marker = page.get_by_test_id("pair-rank-marker")
        expect(marker).to_have_count(1)
        expect(marker).to_have_text(str(pair["rank"]))
        expect(marker).to_have_attribute("aria-hidden", "true")
        assert marker.get_attribute("tabindex") in (None, "-1")
        expect(marker).to_have_css("pointer-events", "none")
        position = page.evaluate("""async () => {
          const {state}=await import('/web/js/state.js');
          const p=state.pairRankMarker.getLatLng(); return [p.lat,p.lng];
        }""")
        assert abs(position[0]-32) < 1e-8 and abs(position[1]+80.98) < 1e-8, position
        expect(page.locator('[data-testid="project-feature"][data-selected="true"]')).to_have_count(2)
        expect(page.get_by_test_id("pair-halo")).to_have_count(2)
        page.get_by_test_id("overlap-row").nth(1).locator("button").click()
        expect(marker).to_have_text(str(pairs[1]["rank"]))
        expect(marker).to_have_count(1)
        page.locator("#more-toggle").click()
        page.locator("#theme-toggle").click()
        expect(marker).to_have_count(1)
        page.locator("#more-toggle").click()
        page.goto(live_server + "/#overlap=invalid")
        expect(page.locator("#overlap-detail-heading")).to_have_text("Unknown overlap link")
        expect(marker).to_have_count(0)
        browser.close()


def test_quiet_list_timeline_and_tablet_sheet(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width":768,"height":900}, reduced_motion="reduce")
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        expect(page.locator("#opportunities #start-here")).to_be_visible()
        first = page.get_by_test_id("overlap-row").first
        for swatch in first.locator(".row-project .swatch").all():
            box = swatch.bounding_box()
            assert box["width"] == box["height"] and box["width"] >= 14
        line = page.locator("#impact-line").bounding_box()
        assert line["height"] <= 22
        timeline = page.locator("#timeline").bounding_box()
        assert timeline["height"] <= 92
        map_box = page.locator(".map-region").bounding_box()
        assert abs(timeline["x"] + timeline["width"]/2 - map_box["x"] - map_box["width"]/2) <= 1
        first.locator("button").click()
        left = page.locator(".panel").bounding_box()
        sheet = page.locator(".detail-pane").bounding_box()
        assert left["x"] + left["width"] <= sheet["x"] + 1
        assert sheet["x"] + sheet["width"] == 768
        expect(page.get_by_test_id("overlap-row").nth(1)).to_be_visible()
        page.locator("#timeline-year").focus()
        expect(page.locator(".detail-pane")).to_be_hidden()
        expect(page.locator("#timeline-year")).to_be_focused()
        browser.close()


def test_impact_popover_yields_to_next_keyboard_target(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        summary = page.locator("#impact-card summary")
        summary.focus()
        page.keyboard.press("Enter")
        expect(page.locator("#impact-full")).to_be_visible()
        page.keyboard.press("Tab")
        expect(page.locator("#impact-full")).to_be_hidden()
        expect(page.locator("#start-here button").first).to_be_focused()
        summary.focus()
        page.keyboard.press("Enter")
        page.keyboard.press("Escape")
        expect(page.locator("#impact-full")).to_be_hidden()
        expect(summary).to_be_focused()
        browser.close()
