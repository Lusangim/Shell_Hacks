"""Filter controls stay in step with API project and overlap semantics."""

from __future__ import annotations

from urllib.parse import urlencode, urlsplit, parse_qs

import pytest
from playwright.sync_api import expect, sync_playwright


def expected(page, base, params):
    query = urlencode(params, doseq=True)
    projects = page.request.get(f"{base}/api/projects?{query}").json()["features"]
    overlaps = page.request.get(f"{base}/api/overlaps?{query}").json()
    return projects, overlaps


def assert_parity(page, projects, overlaps):
    expect(page.get_by_test_id("overlap-row")).to_have_count(len(overlaps))
    assert {row.get_attribute("data-overlap-id") for row in page.get_by_test_id("overlap-row").all()} == {
        pair["id"] for pair in overlaps
    }
    assert set(page.locator('[data-testid="project-feature"]').evaluate_all(
        "elements => elements.map(element => element.dataset.projectId)"
    )) == {feature["properties"]["id"] for feature in projects if feature["geometry"] is not None}
    expect(page.locator("#overlap-count")).to_have_text(f"{len(overlaps)} pairs")
    expect(page.locator("#status")).to_contain_text(str(len(overlaps)))


def open_filters(page, more=False):
    page.locator("#filters-toggle").click()
    expect(page.locator("#filter-band")).to_be_visible()
    if more:
        page.locator("#more-filters summary").click()


@pytest.mark.parametrize("params,actions", [
    ({"band": "touching", "cross_state": "true"}, [("#filter-band", "touching"), ("#filter-cross-state", "true")]),
    ({"utility": ["Dominion Energy SC", "Georgia Power"]}, [("utility", "Dominion Energy SC"), ("utility", "Georgia Power")]),
    ({"voltage_kv": "230", "project_type": "equipment"}, [("#filter-voltage", "230"), ("#filter-type", "equipment")]),
])
def test_filter_combinations_match_both_api_responses(live_server, params, actions):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        open_filters(page, more=any(kind not in ("#filter-band", "utility") for kind, _ in actions))
        for kind, value in actions:
            if kind == "utility":
                page.locator(f'#filter-panel input[name="utility"][value="{value}"]').check()
            else:
                page.locator(kind).select_option(value)
        projects, overlaps = expected(page, live_server, params)
        assert_parity(page, projects, overlaps)
        if "utility" in params:
            assert all(pair["a_utility"] in params["utility"] and pair["b_utility"] in params["utility"] for pair in overlaps)
        browser.close()


def test_no_match_clear_all_and_unknown_reasons(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        open_filters(page, more=True)
        page.locator("#filter-year-min").fill("2199")
        page.locator("#filter-year-min").press("Tab")
        projects, overlaps = expected(page, live_server, {"year_min": "2199"})
        assert projects == [] and overlaps == []
        assert_parity(page, projects, overlaps)
        expect(page.locator("#list-state")).to_contain_text("No matches for these filters")
        page.locator("#filter-clear").click()
        projects, overlaps = expected(page, live_server, {})
        assert_parity(page, projects, overlaps)
        unknown = [feature for feature in projects if feature["geometry"] is None]
        expect(page.locator("#unknown-heading")).to_have_text(f"Location unknown ({len(unknown)})")
        page.locator("#filters-toggle").click()
        expect(page.locator("#filters-toggle")).to_have_attribute("aria-expanded", "false")
        page.locator("#unknown-locations summary").click()
        expect(page.locator("#unknown-list li")).to_have_count(len(unknown))
        unknown_text = page.locator("#unknown-list").inner_text()
        assert all((feature["properties"]["location_source"] or "Location not stated in source") in unknown_text for feature in unknown)
        assert page.locator("#unknown-list a").first.get_attribute("href").startswith("/api/sources/")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        assert errors == []
        browser.close()


def test_filter_url_reload_back_forward_and_selection_outside_filters(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}/?year=2028&area=32.1,-81.2")
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        open_filters(page)
        page.locator("#filter-band").select_option("touching")
        expect(page.locator("#overlap-count")).not_to_have_text("465 pairs")
        params = parse_qs(urlsplit(page.url).query)
        assert params["band"] == ["touching"]
        assert params["year"] == ["2028"] and params["area"] == ["32.1,-81.2"]
        page.reload()
        expect(page.locator("#filter-band")).to_have_value("touching")
        projects, overlaps = expected(page, live_server, {"band": "touching"})
        assert_parity(page, projects, overlaps)
        open_filters(page, more=True)
        first = page.get_by_test_id("overlap-row").first
        selected_id = first.get_attribute("data-overlap-id")
        page.locator("#filters-toggle").click()
        expect(page.locator("#filters-toggle")).to_have_attribute("aria-expanded", "false")
        first.locator("button").click()
        expect(page.get_by_test_id("overlap-detail")).to_be_visible()
        assert page.url.endswith(f"#overlap={selected_id}")
        open_filters(page)
        page.locator("#filter-year-min").fill("2199")
        page.locator("#filter-year-min").press("Tab")
        expect(page.get_by_test_id("overlap-detail")).to_contain_text("outside the current filters")
        expect(page.get_by_test_id("overlap-row")).to_have_count(0)
        assert page.url.endswith(f"#overlap={selected_id}")
        page.go_back()
        expect(page.locator("#filter-year-min")).to_have_value("")
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        page.go_forward()
        expect(page.locator("#filter-year-min")).to_have_value("2199")
        expect(page.get_by_test_id("overlap-row")).to_have_count(0)
        browser.close()


def test_malformed_url_uses_visible_safe_fallback(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}/?utility=not-real&voltage_kv=-1&year_min=oops&year_max=1800&project_type=bad&band=nope&cross_state=maybe&year=oops&area=1000,nope")
        expect(page.get_by_test_id("filter-warning")).to_contain_text("Invalid link filters")
        projects, overlaps = expected(page, live_server, {})
        assert_parity(page, projects, overlaps)
        assert not any(key in parse_qs(urlsplit(page.url).query) for key in
                       ("utility", "voltage_kv", "year_min", "year_max", "project_type", "band", "cross_state", "year", "area"))
        browser.close()


def test_late_filtered_response_cannot_replace_newer_filter(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("""(() => {
          const original = window.fetch;
          window.releaseOldFilter = null;
          window.fetch = (url, options) => {
            if (String(url).includes('/api/overlaps?') && String(url).includes('band=touching')) {
              document.documentElement.dataset.oldFilterPending = 'true';
              return new Promise(resolve => { window.releaseOldFilter = () => {
                resolve(original(url, options).then(
                  response => { document.documentElement.dataset.oldFilterSettled = 'true'; return response; },
                  error => { document.documentElement.dataset.oldFilterSettled = 'true'; throw error; }
                ));
              }; });
            }
            return original(url, options);
          };
        })();""")
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        open_filters(page)
        page.locator("#filter-band").select_option("touching")
        expect(page.locator("html[data-old-filter-pending='true']")).to_have_count(1)
        page.locator("#filter-band").select_option("lt_40km")
        projects, overlaps = expected(page, live_server, {"band": "lt_40km"})
        assert_parity(page, projects, overlaps)
        page.evaluate("window.releaseOldFilter()")
        expect(page.locator("html[data-old-filter-settled='true']")).to_have_count(1)
        assert_parity(page, projects, overlaps)
        assert parse_qs(urlsplit(page.url).query)["band"] == ["lt_40km"]
        browser.close()


def test_visible_controls_have_reachable_tab_order(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        off_path = page.evaluate("""() => Array.from(document.querySelectorAll('a[href], button, input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"]), summary'))
          .filter(el => !el.disabled && el.getClientRects().length > 0 && !el.closest('[hidden], [inert]') && el.tabIndex < 0)
          .map(el => el.outerHTML.slice(0, 150))""")
        assert off_path == []
        candidates = page.evaluate("""() => Array.from(document.querySelectorAll('a[href], button, input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"]), summary'))
          .filter(el => !el.disabled && el.getClientRects().length > 0 && !el.closest('[hidden], [inert]'))
          .map((el, index) => { el.dataset.focusProbe = String(index); return el.outerHTML.slice(0, 150); })""")
        seen = set()
        page.evaluate("document.activeElement?.blur()")
        for _ in candidates:
            page.keyboard.press("Tab")
            marker = page.evaluate("document.activeElement?.dataset.focusProbe")
            if marker is not None:
                seen.add(int(marker))
        assert len(seen) == len(candidates), [candidates[index] for index in range(len(candidates)) if index not in seen]
        browser.close()


def test_filtered_request_error_keeps_previous_data_and_retry_recovers(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        baseline = page.get_by_test_id("overlap-row").count()
        page.route("**/api/overlaps?band=touching", lambda route: route.fulfill(status=503, body="unavailable"))
        open_filters(page)
        page.locator("#filter-band").select_option("touching")
        expect(page.get_by_test_id("error-state")).to_contain_text("Could not load filtered public plan data")
        expect(page.get_by_test_id("overlap-row")).to_have_count(baseline)
        page.unroute("**/api/overlaps?band=touching")
        page.get_by_role("button", name="Try again").click()
        projects, overlaps = expected(page, live_server, {"band": "touching"})
        assert_parity(page, projects, overlaps)
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_phone_filter_controls_remain_readable_and_focusable(live_server, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        open_filters(page, more=True)
        page.locator("#filter-cross-state").select_option("true")
        expect(page.locator("#filter-cross-state")).to_have_value("true")
        page.locator("#filter-cross-state").focus()
        page.keyboard.press("Tab")
        expect(page.locator("#filter-clear")).to_be_focused()
        assert page.locator("#filter-clear").evaluate("element => getComputedStyle(element).outlineStyle") != "none"
        assert page.locator("#filters-toggle").evaluate("element => element.getBoundingClientRect().height >= 44")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        assert errors == []
        browser.close()
