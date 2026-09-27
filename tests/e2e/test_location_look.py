"""UI pass: location looks, town-level wording, capped pairs, map key, labels, framing and attribution."""

import pytest
from playwright.sync_api import expect, sync_playwright


def open_page(playwright, live_server, width=1440, height=900, theme="light", path="", dismissed=True):
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": width, "height": height}, color_scheme=theme, reduced_motion="reduce")
    if dismissed:
        page.add_init_script("localStorage.setItem('gridlock-tour-dismissed', 'yes')")
    page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(live_server) else route.abort())
    page.goto(f"{live_server}/{path}")
    return browser, page


def records(page, live_server):
    projects = page.request.get(f"{live_server}/api/projects").json()["features"]
    pairs = page.request.get(f"{live_server}/api/overlaps").json()
    return {project["properties"]["id"]: project for project in projects}, pairs


def first(projects, test):
    return next(project for project in projects.values() if project["geometry"] and test(project))


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_map_draws_exact_approximate_and_town_level_distinctly(live_server, theme):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server, theme=theme)
        page.get_by_test_id("overlap-row").first.wait_for()
        projects, _ = records(page, live_server)
        kind = lambda project: project["geometry"]["type"]
        town = lambda project: project["properties"].get("town_only") is True
        accuracy = lambda project: project["properties"]["accuracy"]
        cases = {
            "exact point": first(projects, lambda p: kind(p) == "Point" and accuracy(p) == "exact"),
            "approximate point": first(projects, lambda p: kind(p) == "Point" and accuracy(p) == "approximate" and not town(p)),
            "town point": first(projects, lambda p: kind(p) == "Point" and town(p)),
            "exact line": first(projects, lambda p: kind(p) != "Point" and accuracy(p) == "exact"),
            "approximate line": first(projects, lambda p: kind(p) != "Point" and accuracy(p) == "approximate" and not town(p)),
            "town line": first(projects, lambda p: kind(p) != "Point" and town(p)),
        }
        drawn = {name: page.locator(f'[data-testid="project-feature"][data-project-id="{project["properties"]["id"]}"]')
                 for name, project in cases.items()}
        # Points: a filled dot is exact, a hollow ring approximate, a dashed hollow ring town-level.
        expect(drawn["exact point"]).to_have_attribute("fill-opacity", "1")
        assert drawn["exact point"].get_attribute("stroke-dasharray") is None
        expect(drawn["approximate point"]).to_have_attribute("fill-opacity", "0")
        assert drawn["approximate point"].get_attribute("stroke-dasharray") is None
        expect(drawn["town point"]).to_have_attribute("fill-opacity", "0")
        expect(drawn["town point"]).to_have_attribute("stroke-dasharray", "3 3")
        # Lines: solid exact, dashed approximate, dotted town-level.
        assert drawn["exact line"].get_attribute("stroke-dasharray") is None
        expect(drawn["approximate line"]).to_have_attribute("stroke-dasharray", "8 5")
        expect(drawn["town line"]).to_have_attribute("stroke-dasharray", "1 7")
        expect(drawn["town line"]).to_have_attribute("stroke-linecap", "round")
        for name, locator in drawn.items():
            expected = "town" if "town" in name else name.split()[0]
            expect(locator).to_have_attribute("data-look", expected)
        browser.close()


def test_town_level_wording_in_tooltip_row_and_project_detail(live_server):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server)
        page.get_by_test_id("overlap-row").first.wait_for()
        projects, pairs = records(page, live_server)
        paired = {key for pair in pairs for key in (pair["a"], pair["b"])}
        town = first(projects, lambda p: p["properties"].get("town_only") is True and p["geometry"]["type"] == "Point"
                     and p["properties"]["id"] in paired)
        town_id = town["properties"]["id"]
        tooltip = page.evaluate("""async id => {
          const {state} = await import('/web/js/state.js');
          let text = null;
          state.projectLayers.eachLayer(layer => {
            if (layer.feature.properties.id === id) { layer.openTooltip(); text = layer.getTooltip().getElement().innerText; }
          });
          return text;
        }""", town_id)
        assert "Town-level location" in tooltip and town["properties"]["name"] in tooltip
        pair = next(p for p in pairs if town_id in (p["a"], p["b"]))
        row = page.locator(f'[data-testid="overlap-row"][data-overlap-id="{pair["id"]}"]')
        expect(row.locator('[data-src="town_only"]')).to_have_text("Town-level location")
        page.locator("#projects-toggle").click()
        page.locator(f'[data-project-ref="{town_id}"] button').click()
        bullet = page.locator('#project-fields [data-src="town_only"]')
        expect(bullet).to_be_visible()
        expect(bullet).to_contain_text("Town-level location")
        assert page.locator('#project-fields details [data-src="town_only"]').count() == 0
        browser.close()


def test_capped_pair_note_is_visible_in_row_detail_and_print(live_server):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server)
        page.get_by_test_id("overlap-row").first.wait_for()
        _, pairs = records(page, live_server)
        capped = next(p for p in pairs if p.get("town_capped") is True)
        plain = next(p for p in pairs if not p.get("town_capped"))
        row = page.locator(f'[data-testid="overlap-row"][data-overlap-id="{capped["id"]}"]')
        expect(row.locator('[data-src="town_capped"]')).to_have_text("Counted as under 40 km")
        expect(row.locator('[data-src="band_label"]')).to_have_text(capped["band_label"])
        assert page.locator(f'[data-overlap-id="{plain["id"]}"] [data-src="town_capped"]').count() == 0
        page.goto(f"{live_server}/#overlap={capped['id']}")
        note = page.locator('#overlap-content [data-src="town_capped"]')
        expect(note).to_be_visible()
        expect(note).to_contain_text("Counted as under 40 km")
        assert page.locator('#overlap-content details [data-src="town_capped"]').count() == 0
        expect(page.locator('#overlap-content [data-src="distance_km"]').first).to_contain_text(f'{capped["distance_km"]:.1f} km')
        # The selected pair's accent halo paints for points as well as lines.
        expect(page.get_by_test_id("pair-halo")).to_have_count(2)
        assert page.evaluate("""() => [...document.querySelectorAll('[data-testid="pair-halo"]')]
          .every(el => el.getAttribute('fill') !== 'none' || el.getAttribute('stroke') !== 'none')""")
        page.evaluate("window.print = () => { window.printed = true; }")  # same document after the hash change
        page.locator(".legend summary").click()
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printed === true")
        expect(page.locator('#print-selected [data-src="town_capped"]')).to_contain_text("Counted as under 40 km")
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_map_key_shows_exact_approximate_and_town_level(live_server, width, height):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server, width, height)
        page.get_by_test_id("overlap-row").first.wait_for()
        labels = ["Exact location", "Approximate location", "Town-level location"]
        key = page.get_by_test_id("map-key")
        if width == 1440:
            expect(key).to_be_visible()
            for label in labels + ["Dominion Energy SC", "Georgia Power", "MEAG Power", "Georgia Transmission Corp."]:
                expect(key).to_contain_text(label)
            expect(key.locator(".sample")).to_have_count(5)
        else:
            expect(key).to_be_hidden()
            page.locator(".legend summary").click()
            for label in labels:
                expect(page.locator(".legend").get_by_text(label).first).to_be_visible()
        browser.close()


def test_multilinestring_pair_is_highlighted_and_framed(live_server):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server)
        page.get_by_test_id("overlap-row").first.wait_for()
        projects, pairs = records(page, live_server)
        pair = next(p for p in pairs if "MultiLineString" in (projects[p["a"]]["geometry"] or {}).get("type", "")
                    + (projects[p["b"]]["geometry"] or {}).get("type", ""))
        contains = """async ids => {
          const {state} = await import('/web/js/state.js');
          const features = (await (await fetch('/api/projects')).json()).features.filter(f => ids.includes(f.properties.id));
          return features.every(f => state.map.getBounds().contains(L.geoJSON(f).getBounds()));
        }"""
        for entry in ("link", "list"):
            if entry == "link":
                page.goto(f"{live_server}/#overlap={pair['id']}")
            else:
                page.goto(live_server)
                row = page.locator(f'[data-testid="overlap-row"][data-overlap-id="{pair["id"]}"] button')
                row.scroll_into_view_if_needed()
                row.click()
            expect(page.locator("#overlap-content .overlap-project")).to_have_count(2)
            expect(page.locator('[data-testid="project-feature"][data-selected="true"]')).to_have_count(2)
            expect(page.get_by_test_id("pair-halo")).to_have_count(2)
            page.wait_for_function(contains, arg=[pair["a"], pair["b"]])
        browser.close()


def test_area_link_keeps_restored_area_view_on_first_load(live_server):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server)
        page.get_by_test_id("overlap-row").first.wait_for()
        projects, pairs = records(page, live_server)
        far = next(p for p in pairs if all(projects[key]["geometry"] and
                   projects[key]["geometry"]["type"] == "Point" and projects[key]["geometry"]["coordinates"][1] > 33.5
                   for key in (p["a"], p["b"])))
        page.goto(f"{live_server}/?area=32.08,-81.10&radius_km=40#overlap={far['id']}")
        expect(page.locator("#overlap-content .overlap-project")).to_have_count(2)
        expect(page.locator("#area-state")).to_contain_text("projects in area")
        assert page.evaluate("""async () => {
          const {state} = await import('/web/js/state.js');
          return state.map.getCenter().distanceTo([32.08, -81.10]) < 20000;
        }""")
        browser.close()


@pytest.mark.parametrize("width,theme", [(1440, "light"), (1440, "dark"), (768, "light")])
def test_selected_pair_labels_keep_words_whole_and_apart(live_server, width, theme):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server, width, 900, theme)
        page.get_by_test_id("overlap-row").first.locator("button").click()
        expect(page.locator(".leaflet-tooltip")).to_have_count(2)
        page.wait_for_function("async () => !(await import('/web/js/state.js')).state.map._animatingZoom")
        page.wait_for_timeout(200)
        labels = page.evaluate("""() => {
          const panel = document.querySelector('.panel').getBoundingClientRect();
          const samples = [];
          for (const path of document.querySelectorAll('[data-testid="project-feature"][data-selected="true"]')) {
            const total = path.getTotalLength(), matrix = path.getScreenCTM();
            for (let i = 0; i <= 48; i++) {
              const point = path.getPointAtLength(total * i / 48);
              samples.push(new DOMPoint(point.x, point.y).matrixTransform(matrix));
            }
          }
          return [...document.querySelectorAll('.leaflet-tooltip')].map(tip => {
            const rect = tip.getBoundingClientRect();
            const name = tip.querySelector('.tooltip-name');
            const text = name.firstChild, split = [];
            for (const match of text.textContent.matchAll(/\\S+/g)) {
              const range = document.createRange();
              range.setStart(text, match.index);
              range.setEnd(text, match.index + match[0].length);
              if (range.getClientRects().length > 1) split.push(match[0]);
            }
            const covered = samples.filter(p => p.x > rect.left && p.x < rect.right && p.y > rect.top && p.y < rect.bottom).length;
            return {left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom, width: rect.width,
                    split, covered, panelRight: panel.right};
          });
        }""")
        a, b = labels
        for label in labels:
            assert label["split"] == [], label
            assert label["width"] >= 160, label
        assert a["right"] <= b["left"] or b["right"] <= a["left"] or a["bottom"] <= b["top"] or b["bottom"] <= a["top"], labels
        if width == 1440:
            # With room to spare, labels sit clear of the panel and of the lines they name.
            assert all(label["left"] >= label["panelRight"] for label in labels), labels
            assert all(label["covered"] == 0 for label in labels), labels
        browser.close()


def fake_google(page):
    page.add_init_script("window.google = {maps:{Map:class {}}}")
    page.route("**/web/vendor/googlemutant/Leaflet.GoogleMutant.js", lambda route: route.fulfill(
        content_type="text/javascript", body="""
          L.gridLayer.googleMutant = options => {
            window.fakeGoogleType = options.type;
            return new (L.Layer.extend({onAdd() { this.fire('tileload'); }, onRemove() {}}))();
          };"""))


def test_attribution_follows_the_displayed_basemap(live_server):
    """Only the base map on screen is credited; Google itself is never contacted."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        requests = []
        page.on("request", lambda request: requests.append(request.url))
        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(live_server) else route.abort())
        page.route("**/api/map-config", lambda route: route.fulfill(json={
            "offline_available": True, "google_enabled": True, "google_key": "synthetic-browser-key"}))
        fake_google(page)
        page.goto(live_server)
        page.get_by_test_id("overlap-row").first.wait_for()
        status = page.get_by_test_id("basemap-status")
        attribution = page.locator(".leaflet-control-attribution")
        expect(status).to_have_text("Offline street map")
        expect(attribution).to_contain_text("OpenStreetMap")
        expect(attribution).to_contain_text("Protomaps")
        assert status.bounding_box()["width"] <= 1  # routine state: announced, not drawn
        group = page.get_by_role("group", name="Base map")
        for mode, text in [("Google Maps", "Google Maps"), ("Satellite", "Satellite map")]:
            group.get_by_role("button", name=mode, exact=True).click()
            expect(status).to_have_text(text)
            expect(attribution).not_to_contain_text("OpenStreetMap")
            expect(attribution).to_be_hidden()
            assert status.bounding_box()["width"] > 1
            group.get_by_role("button", name="Map", exact=True).click()
            expect(status).to_have_text("Offline street map")
            expect(attribution).to_contain_text("OpenStreetMap")
            expect(attribution).to_be_visible()
        assert all(url.startswith(live_server) for url in requests), [url for url in requests if not url.startswith(live_server)]
        page.unroute("**/api/map-config")
        page.route("**/api/map-config", lambda route: route.fulfill(json={
            "offline_available": False, "google_enabled": False, "google_key": None}))
        page.reload()
        page.get_by_test_id("overlap-row").first.wait_for()
        expect(status).to_contain_text("Outline map")
        assert status.bounding_box()["width"] > 1
        expect(attribution).not_to_contain_text("OpenStreetMap")
        expect(attribution).to_be_hidden()
        browser.close()


def test_states_name_filters_show_skeleton_and_clear_stale_loading_text(live_server):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server, path="?year_min=2199")
        state = page.get_by_test_id("empty-state")
        expect(state).to_contain_text("No matches for these filters: in service from 2199.")
        expect(state.get_by_role("button", name="Clear filters")).to_be_visible()
        page.close()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.route("**/api/overlaps", lambda route: None)  # held open: the loading state stays
        page.goto(live_server, wait_until="domcontentloaded")
        loading = page.get_by_test_id("loading-state")
        expect(loading).to_contain_text("Loading ranked opportunities")
        expect(loading.locator('.skeleton-row[aria-hidden="true"]')).to_have_count(3)
        # A disabled control looks disabled: pencil text instead of ink.
        expect(page.locator("#filters-toggle")).to_be_disabled()
        assert page.evaluate("""() => {
          const probe = document.createElement('span');
          probe.style.color = 'var(--pencil)';
          document.body.append(probe);
          const pencil = getComputedStyle(probe).color;
          probe.remove();
          return getComputedStyle(document.querySelector('#filters-toggle')).color === pencil;
        }""")
        page.close()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.route("**/api/overlaps", lambda route: route.fulfill(status=503, json={"error": {"code": "unavailable", "message": "Unavailable"}}))
        page.goto(live_server)
        expect(page.get_by_test_id("error-state")).to_be_visible()
        expect(page.locator("#editions")).to_have_text("Plan editions not loaded.")
        expect(page.locator("#no-overlap")).to_have_text("Project counts not loaded.")
        expect(page.locator("#timeline-status")).to_have_text("In-service years not loaded.")
        browser.close()


def test_rows_search_and_tour_use_drawn_icons_and_plain_words(live_server):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server)
        row = page.get_by_test_id("overlap-row").first
        _, pairs = records(page, live_server)
        band = row.locator(".row-band")
        expect(band).to_have_text(pairs[0]["band_label"])
        expect(band.locator("svg.band-glyph")).to_have_count(1)
        expect(row.locator(".swatch")).to_have_count(2)
        page.locator("#search-input").fill("Savannah")
        expect(page.locator("#search-options option")).not_to_have_count(0)
        page.locator("#search-input").press("Enter")
        expect(page.get_by_test_id("search-selection")).to_have_text("Place: Savannah city")
        page.get_by_role("button", name="Take the tour", exact=True).click()
        card = page.get_by_role("dialog", name="GridLock tour")
        panel = page.locator(".panel").bounding_box()
        zoom = page.locator(".leaflet-control-zoom").bounding_box()
        for _ in range(2):
            box = card.bounding_box()
            assert box["x"] >= panel["x"] + panel["width"], box
            assert (box["x"] + box["width"] <= zoom["x"] or box["y"] >= zoom["y"] + zoom["height"]
                    or box["y"] + box["height"] <= zoom["y"]), (box, zoom)
            card.get_by_role("button", name="Next", exact=True).click()
        browser.close()
