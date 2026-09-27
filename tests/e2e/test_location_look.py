"""UI pass: location looks, town-level wording, capped pairs, map key, labels, framing and attribution."""

from datetime import date

import pytest
from playwright.sync_api import expect, sync_playwright

from tests.e2e.ui_helpers import back_to_pair, close_more, open_more, open_pair_section, reveal_brief


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
        # The compact row keeps a short marker; the tooltip above and the project detail below say it in full.
        expect(row.locator('[data-src="town_only"]')).to_have_text("Town-level")
        open_more(page)
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
        overview_note = page.locator('#pair-summary [data-src="town_capped"]')
        expect(overview_note).to_be_visible()
        expect(overview_note).to_contain_text("Counted as under 40 km")
        open_pair_section(page, "Why they appear together")
        note = page.locator('#overlap-content [data-src="town_capped"]')
        expect(note).to_be_visible()
        expect(note).to_contain_text("Counted as under 40 km")
        assert page.locator('#overlap-content .detail-block details [data-src="town_capped"]').count() == 0
        expect(page.locator('#overlap-content [data-src="distance_km"]').first).to_contain_text(f'{capped["distance_km"]:.1f} km')
        # The selected pair's accent halo paints for points as well as lines.
        expect(page.get_by_test_id("pair-halo")).to_have_count(2)
        assert page.evaluate("""() => [...document.querySelectorAll('[data-testid="pair-halo"]')]
          .every(el => el.getAttribute('fill') !== 'none' || el.getAttribute('stroke') !== 'none')""")
        page.evaluate("window.print = () => { window.printed = true; }")  # same document after the hash change
        open_more(page)
        page.locator(".legend summary").click()
        open_more(page)
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
            expect(key.locator(".key-list").first).to_be_hidden()
            key.locator("summary").focus()
            page.keyboard.press("Enter")
            expect(key).to_have_attribute("open", "")
            for label in labels + ["Dominion Energy SC", "Georgia Power", "MEAG Power", "Georgia Transmission Corp."]:
                expect(key).to_contain_text(label)
                expect(key.get_by_text(label, exact=True)).to_be_visible()
            expect(key.locator(".sample")).to_have_count(5)
            key.locator("summary").press("Enter")
            expect(key.locator(".key-list").first).to_be_hidden()
            expect(key.locator("summary")).to_be_focused()
        else:
            expect(key).to_be_hidden()
            open_more(page)
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
        open_more(page)
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


def coordinate_text(a_year, b_year):
    """The years-to-coordinate wording, from today's year so the test does not age."""
    if not isinstance(a_year, int) or not isinstance(b_year, int):
        return None
    years = max(0, min(a_year, b_year) - date.today().year)
    return "Coordinate now" if years == 0 else "1 year to coordinate" if years == 1 else f"{years} years to coordinate"


def js_number(value):
    return str(int(value)) if float(value).is_integer() else str(value)


def test_ranked_rows_are_short_and_keep_whole_names_in_reach(live_server):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server)
        page.get_by_test_id("overlap-row").first.wait_for()
        projects, pairs = records(page, live_server)
        rows = page.evaluate("""() => [...document.querySelectorAll('[data-testid="overlap-row"]')].slice(0, 12).map(row => ({
          id: row.dataset.overlapId, height: row.getBoundingClientRect().height, text: row.querySelector('button').textContent,
          names: [...row.querySelectorAll('[data-src="name"]')].map(n => ({text: n.textContent, title: n.title, height: n.getBoundingClientRect().height})),
          sources: row.querySelectorAll('[data-src="source"]').length, marker: row.querySelector('.row-accuracy')?.textContent}))""")
        by_id = {pair["id"]: pair for pair in pairs}
        for row in rows:
            pair = by_id[row["id"]]
            assert row["sources"] == 0, row  # citations live in the pair and project details
            if not pair.get("town_capped"):
                assert row["height"] <= 110, row  # four short lines at most (a capped pair adds its note)
            assert [name["text"] for name in row["names"]] == [projects[pair[key]]["properties"]["name"] for key in ("a", "b")]
            for name in row["names"]:
                assert name["title"] == name["text"] and name["height"] < 24, name  # one line; the whole name is its title
                assert name["text"] in row["text"], name  # and part of the row button's name
            assert row["marker"] in {"Exact", "Approx.", "Town-level"}, row
        browser.close()


def test_years_to_coordinate_tag_in_rows_and_pair_summary(live_server):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server)
        page.get_by_test_id("overlap-row").first.wait_for()
        _, pairs = records(page, live_server)
        first = pairs[0]
        expected = coordinate_text(first["a_year"], first["b_year"])
        assert expected, first
        row = page.locator(f'[data-testid="overlap-row"][data-overlap-id="{first["id"]}"]')
        expect(row.locator(".coordinate-tag")).to_have_text(expected)
        tags = page.evaluate("""() => [...document.querySelectorAll('[data-testid="overlap-row"]')].map(row =>
          [row.dataset.overlapId, row.querySelector('.coordinate-tag')?.textContent ?? null])""")
        by_id = {pair["id"]: pair for pair in pairs}
        mismatched = [(pair_id, tag) for pair_id, tag in tags
                      if tag != coordinate_text(by_id[pair_id]["a_year"], by_id[pair_id]["b_year"])]
        assert mismatched == []
        edges = page.evaluate("""async () => {
          const {coordinateText} = await import('/web/js/look.js');
          const now = new Date(2026, 5, 1);
          return [coordinateText(2026, 2030, now), coordinateText(2027, 2031, now), coordinateText(2031, 2029, now),
                  coordinateText(2020, 2024, now), coordinateText(2028, null, now)];
        }""")
        assert edges == ["Coordinate now", "1 year to coordinate", "3 years to coordinate", "Coordinate now", None]
        row.locator("button").click()
        expect(page.get_by_test_id("pair-summary").locator(".coordinate-chip")).to_have_text(expected)
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_shell_keeps_search_pairs_and_reports_in_reach(live_server, width, height):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server, width, height)
        page.get_by_test_id("overlap-row").first.wait_for()
        _, pairs = records(page, live_server)
        if width == 390:
            page.locator("#sheet-toggle").click()
        expect(page.locator(".app-bar #search-input")).to_be_visible()
        expect(page.get_by_role("heading", name="Pairs", exact=True)).to_be_visible()
        expect(page.locator("#opportunities .step-hint")).to_contain_text("A pair is two planned projects")
        open_more(page)
        expect(page.locator(".legend > summary")).to_have_text("Map key")
        about = page.locator("#about-data")
        expect(about.locator("summary")).to_contain_text("About the data")
        expect(about.locator("#editions")).to_be_hidden()
        about.locator("summary").click()
        expect(about.locator("#editions")).to_be_visible()
        expect(about.locator("#no-overlap")).to_be_visible()
        for name in ("Export CSV", "Print report"):
            expect(page.get_by_role("button", name=name, exact=True)).to_be_visible()
        close_more(page)
        page.get_by_test_id("overlap-row").first.locator("button").click()
        expect(page.locator("#overlap-content .overlap-project")).to_have_count(2)
        # The chosen row remains selected while the right pane holds its detail.
        chosen = page.locator(f'[data-testid="overlap-row"][data-overlap-id="{pairs[0]["id"]}"]')
        expect(page.get_by_test_id("overlap-row")).to_have_count(len(pairs))
        if width > 700:
            expect(page.get_by_test_id("overlap-row").nth(1)).to_be_visible()
        expect(chosen).to_have_attribute("data-overlap-id", pairs[0]["id"])
        expect(chosen.get_by_role("button")).to_have_attribute("aria-pressed", "true")
        bar = page.locator("#detail-bar")
        expect(bar.locator("#detail-close")).to_be_visible()
        expect(bar.locator("#overlap-detail-heading")).to_have_text(f'Pair {pairs[0]["rank"]}')
        expect(page.locator(".detail-pane #overlap-detail")).to_be_visible()
        open_more(page)
        for name in ("Export CSV", "Print report"):
            expect(page.get_by_role("button", name=name, exact=True)).to_be_visible()  # still in reach with a pair open
        close_more(page)
        page.get_by_role("button", name="Back to ranked overlaps").click()
        expect(page.get_by_test_id("overlap-row").nth(1)).to_be_visible()
        expect(bar).to_be_hidden()
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_pair_summary_disclosures_and_brief_under_a_sticky_bar(live_server, width, height):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server, width, height)
        page.get_by_test_id("overlap-row").first.wait_for()
        projects, pairs = records(page, live_server)
        pair = pairs[0]
        page.goto(f"{live_server}/#overlap={pair['id']}")
        expect(page.locator("#overlap-content .overlap-project")).to_have_count(2)
        summary = page.get_by_test_id("pair-summary")
        expect(summary.locator('[data-src="summary_name"]')).to_have_text([projects[pair[key]]["properties"]["name"] for key in ("a", "b")])
        expect(summary.locator('[data-src="summary_band"]')).to_have_text(pair["band_label"])
        accuracy = {"approximate": "Approx.", "exact": "Exact"}.get(pair["accuracy_pair"], "Unknown")
        expect(summary.locator('[data-src="summary_distance"]')).to_have_text(f'{pair["distance_km"]:.1f} km · {accuracy}')
        expect(summary.locator('[data-src="summary_years"]')).to_have_text(f'{pair["a_year"]} / {pair["b_year"]}')
        expect(summary.locator('[data-src="summary_score"]')).to_have_text(js_number(pair["score"]))
        expect(summary.locator('[data-src="summary_savings"]')).to_contain_text("estimate")
        sections = ["Why they appear together", "Sources", "About the estimate"] + (["How this pair ranks"] if page.locator("#overlap-content .score-detail").count() else []) + ["Your coordination status"]
        expect(page.locator(".detail-pane .pair-disclosure > summary")).to_have_text(sections)
        for section, target in [("savings", "#pair-savings"), ("projects", "#pair-projects"), ("why", "#pair-why")]:
            control = page.locator(target)
            disclosure = control.locator("..")
            expect(disclosure).not_to_have_attribute("open", "")
            control.focus()
            page.keyboard.press("Enter")
            expect(disclosure).to_have_attribute("open", "")
            expect(control).to_be_focused()
            expect(disclosure.locator(":scope > .detail-block, :scope > .overlap-projects")).to_be_visible()
            layout = page.evaluate("""target => {
              const bar = document.querySelector('#detail-bar').getBoundingClientRect();
              const body = document.querySelector('.detail-pane').getBoundingClientRect();
              const heading = document.querySelector(target).getBoundingClientRect();
              return {barTop: bar.top, barBottom: bar.bottom, bodyTop: body.top, bodyBottom: body.bottom, top: heading.top};
            }""", target)
            # The bar stays at the top of the panel and the section starts just below it.
            assert abs(layout["barTop"] - layout["bodyTop"]) <= 1 and layout["barBottom"] - 1 <= layout["top"] < layout["bodyBottom"], (section, layout)
            page.keyboard.press("Enter")
            expect(disclosure).not_to_have_attribute("open", "")
            expect(control).to_be_focused()
        reveal_brief(page)
        expect(page.locator("#brief-heading")).to_be_focused()
        expect(page.get_by_role("button", name="Copy brief", exact=True)).to_be_enabled()
        back_to_pair(page)
        expect(page.get_by_role("button", name="Open brief", exact=True)).to_be_focused()
        expect(page.get_by_role("button", name="Back to ranked overlaps")).to_be_visible()
        browser.close()


def test_map_labels_carry_the_name_and_utility_only(live_server):
    with sync_playwright() as playwright:
        browser, page = open_page(playwright, live_server)
        page.get_by_test_id("overlap-row").first.locator("button").click()
        expect(page.locator(".leaflet-tooltip.pair-label")).to_have_count(2)
        labels = page.evaluate("""() => [...document.querySelectorAll('.leaflet-tooltip.pair-label')].map(tip => {
          const name = tip.querySelector('.tooltip-name'), line = parseFloat(getComputedStyle(name).lineHeight);
          return {name: name.textContent, title: name.title, lines: Math.round(name.getBoundingClientRect().height / line),
                  utility: tip.querySelector('[data-src="utility"]').textContent,
                  accuracyShown: getComputedStyle(tip.querySelector('.tooltip-accuracy')).display !== 'none',
                  sources: tip.querySelectorAll('[data-src="source"]').length};
        })""")
        for label in labels:
            assert label["title"] == label["name"] and 1 <= label["lines"] <= 2, label
            assert label["utility"] and not label["accuracyShown"] and label["sources"] == 0, label
        # A hover label adds one accuracy line, still without a citation.
        page.get_by_role("button", name="Back to ranked overlaps").click()
        hover = page.evaluate("""async () => {
          const {state} = await import('/web/js/state.js');
          let found = null;
          state.projectLayers.eachLayer(layer => {
            if (found || layer.feature.properties.id === state.overlaps[0].a || layer.feature.properties.id === state.overlaps[0].b) return;
            layer.openTooltip();
            const tip = layer.getTooltip().getElement();
            found = {accuracy: getComputedStyle(tip.querySelector('.tooltip-accuracy')).display !== 'none',
                     sources: tip.querySelectorAll('[data-src="source"]').length};
          });
          return found;
        }""")
        assert hover == {"accuracy": True, "sources": 0}, hover
        browser.close()
