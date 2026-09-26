"""In-service timeline keeps public-plan years and API-filtered pairs distinct."""

from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import expect, sync_playwright


MCINTOSH = "desc-p41__sertp-p107-9bc088"


def wait_for_timeline(page):
    slider = page.locator("#timeline-year")
    expect(slider).to_be_enabled(timeout=5000)
    expect(slider).to_have_attribute("min", "2026")
    expect(slider).to_have_attribute("max", "2035")


def set_year(page, year):
    wait_for_timeline(page)
    page.locator("#timeline-year").evaluate("""(element, value) => {
      element.value = String(value);
      element.dispatchEvent(new Event('input', {bubbles: true}));
    }""", year)
    expect(page.locator("#timeline-output")).to_have_text(str(year))


def lit_ids(page):
    return set(page.locator('[data-testid="overlap-row"][data-timeline="lit"]').evaluate_all(
        "elements => elements.map(element => element.dataset.overlapId)"))


def entering_ids(page):
    return set(page.locator('[data-testid="project-feature"][data-timeline="entering"]').evaluate_all(
        "elements => elements.map(element => element.dataset.projectId)"))


def test_actual_bounds_2028_mcintosh_exact_projects_and_pair_window(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(live_server)
        projects = page.request.get(f"{live_server}/api/projects").json()["features"]
        pairs = page.request.get(f"{live_server}/api/overlaps").json()
        stated_years = [feature["properties"]["year"] for feature in projects if feature["properties"]["year"] is not None]
        assert (min(stated_years), max(stated_years)) == (2026, 2035)
        expect(page.locator("#timeline-year")).to_have_attribute("min", "2026")
        expect(page.locator("#timeline-year")).to_have_attribute("max", "2035")
        set_year(page, 2028)
        assert entering_ids(page) == {feature["properties"]["id"] for feature in projects
                                      if feature["geometry"] is not None and feature["properties"]["year"] == 2028}
        expected_lit = {pair["id"] for pair in pairs if pair["a_year"] is not None and pair["b_year"] is not None
                        and abs(pair["a_year"] - 2028) <= 1 and abs(pair["b_year"] - 2028) <= 1}
        assert lit_ids(page) == expected_lit
        assert MCINTOSH in expected_lit
        all_entering = sum(feature["properties"]["year"] == 2028 for feature in projects)
        expect(page.locator("#timeline-year")).to_have_attribute("aria-valuetext", f"2028: {all_entering} projects entering service, {len(expected_lit)} pairs in the year window")
        expect(page.locator("#overlap-count")).to_have_text(f"{len(pairs)} pairs")
        expect(page.locator("#timeline-status")).to_contain_text(f"{len(expected_lit)} pairs")
        browser.close()


def test_unknown_year_stays_unknown_and_all_years_restores_full_view(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        projects = page.request.get(f"{live_server}/api/projects").json()["features"]
        unknown = [feature for feature in projects if feature["properties"]["year"] is None]
        assert len(unknown) == 2
        set_year(page, 2028)
        for feature in unknown:
            if feature["geometry"] is not None:
                expect(page.locator(f'[data-testid="project-feature"][data-project-id="{feature["properties"]["id"]}"]')).to_have_attribute("data-timeline", "unknown")
        expect(page.locator("#timeline-status")).to_contain_text("2 projects with unknown in-service year")
        page.get_by_role("button", name="All years").click()
        expect(page.locator("#timeline-output")).to_have_text("All years")
        expect(page.locator("#timeline-year")).to_have_attribute("aria-valuetext", "All years")
        assert "year" not in parse_qs(urlsplit(page.url).query)
        expect(page.locator('[data-testid="overlap-row"][data-timeline="lit"]')).to_have_count(0)
        expect(page.locator('[data-testid="project-feature"][data-timeline="entering"]')).to_have_count(0)
        browser.close()


def test_arrow_year_url_reload_back_forward_preserves_filters_and_area(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}/?band=touching&area=32.1,-81.2&year=2028")
        expect(page.locator("#timeline-output")).to_have_text("2028")
        expect(page.locator("#filter-band")).to_have_value("touching")
        page.locator("#timeline-year").focus()
        page.locator("#timeline-year").press("ArrowRight")
        expect(page.locator("#timeline-output")).to_have_text("2029")
        params = parse_qs(urlsplit(page.url).query)
        assert params["year"] == ["2029"] and params["band"] == ["touching"] and params["area"] == ["32.1,-81.2"]
        page.go_back()
        expect(page.locator("#timeline-output")).to_have_text("2028")
        page.go_forward()
        expect(page.locator("#timeline-output")).to_have_text("2029")
        page.reload()
        expect(page.locator("#timeline-output")).to_have_text("2029")
        expect(page.locator("#filter-band")).to_have_value("touching")
        page.locator("#timeline-year").press("ArrowLeft")
        expect(page.locator("#timeline-output")).to_have_text("2028")
        browser.close()


def test_play_pause_and_last_year_are_deterministic(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.clock.install()
        page.goto(live_server)
        expect(page.locator("#timeline-year")).to_have_attribute("max", "2035")
        set_year(page, 2028)
        page.get_by_role("button", name="Play years").click()
        page.clock.run_for(450)
        expect(page.locator("#timeline-output")).to_have_text("2029")
        page.get_by_role("button", name="Pause years").click()
        page.clock.run_for(1600)
        expect(page.locator("#timeline-output")).to_have_text("2029")
        set_year(page, 2034)
        page.get_by_role("button", name="Play years").click()
        page.clock.run_for(450)
        expect(page.locator("#timeline-output")).to_have_text("2035")
        expect(page.get_by_role("button", name="Play years")).to_be_visible()
        page.clock.run_for(1600)
        expect(page.locator("#timeline-output")).to_have_text("2035")
        browser.close()


def test_filter_removes_year_pairs_then_clear_restores_lighting(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        set_year(page, 2028)
        assert MCINTOSH in lit_ids(page)
        page.locator("#filters-toggle").click()
        page.locator("#more-filters summary").click()
        page.locator("#filter-year-min").fill("2199")
        page.locator("#filter-year-min").press("Tab")
        expect(page.get_by_test_id("overlap-row")).to_have_count(0)
        expect(page.locator("#timeline-status")).to_contain_text("No ranked pairs meet the 2028 year window under current filters")
        assert parse_qs(urlsplit(page.url).query)["year"] == ["2028"]
        page.locator("#filter-clear").click()
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        assert MCINTOSH in lit_ids(page)
        expect(page.locator("#timeline-output")).to_have_text("2028")
        browser.close()


def test_invalid_year_link_has_visible_fallback(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}/?year=2199")
        expect(page.locator("#timeline-output")).to_have_text("All years")
        expect(page.locator("#timeline-status")).to_contain_text("outside the loaded plan years")
        assert "year" not in parse_qs(urlsplit(page.url).query)
        browser.close()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_phone_keyboard_focus_reduced_motion_and_no_outbound_calls(live_server, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        page.emulate_media(reduced_motion="reduce")
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: external.append(request.url) if not request.url.startswith(live_server) else None)
        page.goto(live_server)
        expect(page.locator("#timeline-year")).to_be_visible()
        wait_for_timeline(page)
        page.get_by_role("button", name="All years").focus()
        page.keyboard.press("Tab")
        expect(page.locator("#timeline-year")).to_be_focused()
        page.keyboard.press("ArrowRight")
        expect(page.locator("#timeline-output")).to_have_text("2027")
        assert page.locator("#timeline-year").evaluate("element => getComputedStyle(element).outlineStyle") != "none"
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        assert page.evaluate("document.getAnimations().length") == 0
        assert errors == [] and external == []
        browser.close()


def test_rapid_filter_year_changes_keep_latest_lighting(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("""(() => {
          const original = window.fetch;
          window.releaseOldYearFilter = null;
          window.fetch = (url, options) => {
            if (String(url).includes('/api/overlaps?') && String(url).includes('band=touching')) {
              document.documentElement.dataset.oldYearFilterPending = 'true';
              return new Promise(resolve => { window.releaseOldYearFilter = () => resolve(original(url, options).then(
                response => { document.documentElement.dataset.oldYearFilterSettled = 'true'; return response; },
                error => { document.documentElement.dataset.oldYearFilterSettled = 'true'; throw error; }
              )); });
            }
            return original(url, options);
          };
        })();""")
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        page.locator("#filters-toggle").click()
        page.locator("#filter-band").select_option("touching")
        expect(page.locator("html[data-old-year-filter-pending='true']")).to_have_count(1)
        set_year(page, 2028)
        page.locator("#filter-band").select_option("lt_40km")
        set_year(page, 2029)
        pairs = page.request.get(f"{live_server}/api/overlaps?band=lt_40km").json()
        expect(page.get_by_test_id("overlap-row")).to_have_count(len(pairs))
        expected_lit = {pair["id"] for pair in pairs if pair["a_year"] is not None and pair["b_year"] is not None
                        and abs(pair["a_year"] - 2029) <= 1 and abs(pair["b_year"] - 2029) <= 1}
        assert lit_ids(page) == expected_lit
        page.evaluate("window.releaseOldYearFilter()")
        expect(page.locator("html[data-old-year-filter-settled='true']")).to_have_count(1)
        assert lit_ids(page) == expected_lit
        expect(page.locator("#timeline-output")).to_have_text("2029")
        browser.close()
