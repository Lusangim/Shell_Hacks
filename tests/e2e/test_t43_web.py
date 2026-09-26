"""Real G3 findings: provenance, recoverable states and unobscured phone focus."""

from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright


@pytest.fixture
def browser_page():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page.add_init_script("localStorage.setItem('gridlock-tour-dismissed', 'yes')")
        yield page
        browser.close()


def start(page, url, width, theme="light"):
    page.set_viewport_size({"width": width, "height": 844})
    page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
    page.goto(url)
    expect(page.locator("#filters-toggle")).to_be_enabled()
    expect(page.locator("#timeline-year")).to_be_enabled()


def project(page, project_id):
    page.locator("#projects-toggle").click()
    page.locator(f'[data-project-ref="{project_id}"] button').click()
    return page.locator("#project-fields")


@pytest.mark.parametrize("width", [390, 1440])
def test_inferred_utility_across_real_project_pair_map_and_print(live_server, browser_page, width):
    page = browser_page
    start(page, live_server, width)
    row = page.get_by_test_id("overlap-row").first
    expect(row.locator('[data-src="utility"]').nth(0)).to_have_text("Dominion Energy SC")
    expect(row.locator('[data-src="utility"]').nth(1)).to_have_text("Georgia Power (inferred)")
    row.locator("button").click()
    expect(page.locator('#overlap-content .overlap-project [data-src="utility"]').nth(1)).to_have_text("Georgia Power (inferred)")
    expect(page.locator('.leaflet-tooltip [data-src="utility"]').filter(has_text="Georgia Power")).to_have_text("Georgia Power (inferred)")
    page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    expect(page.locator('#print-selected .overlap-project [data-src="utility"]').nth(1)).to_have_text("Georgia Power (inferred)")
    page.locator("#overlap-back").click()
    fields = project(page, "sertp-p107-9bc088")
    expect(fields.locator('[data-src="utility"]')).to_have_text("Georgia Power (inferred)")
    raw = page.request.get(f"{live_server}/api/projects/sertp-p107-9bc088").json()
    assert raw["properties"]["utility"] == "Georgia Power"
    assert raw["properties"]["utility_basis"] == "inferred_from_location"


@pytest.mark.parametrize("width", [390, 1440])
def test_printed_cost_keeps_adjacent_warnings_and_unflagged_stays_plain(live_server, browser_page, width):
    page = browser_page
    start(page, live_server, width)
    fields = project(page, "desc-p4")
    cost = fields.locator('[data-src="cost_usd"]')
    expect(cost).to_have_text("$1,238,443")
    cost_row = cost.locator("..")
    expect(cost_row).to_contain_text("Printed total differs from the year columns; verify the source.")
    expect(cost_row).to_contain_text("Printed total is below the list's $2 million threshold.")
    expect(cost_row.locator(".cost-warning")).to_have_count(2)
    for warning in cost_row.locator(".cost-warning").all():
        expect(warning).to_be_visible()
    assert fields.locator(".detail-points").first.locator("li").count() <= 3
    assert "printed_total_differs_from_sum" not in fields.inner_text()
    page.locator("#project-back").click()
    page.locator('[data-project-ref="desc-p41"] button').click()
    expect(page.locator("#project-fields .cost-warning")).to_have_count(0)
    # No real pair contains a flagged project. Keep desc-p4 verbatim in a
    # synthetic pair to exercise the shared pair and selected-print consumer.
    projects = page.request.get(f"{live_server}/api/projects").json()["features"]
    flagged = {p["properties"]["id"] for p in projects if p["properties"]["cost_flags"]}
    pairs = page.request.get(f"{live_server}/api/overlaps").json()
    assert not any(p["a"] in flagged or p["b"] in flagged for p in pairs)
    pair = pairs[0]
    flagged_project = next(p for p in projects if p["properties"]["id"] == "desc-p4")

    def with_flagged_project(route):
        payload = route.fetch().json()
        payload["project_a"] = flagged_project
        payload["overlap"]["a"] = "desc-p4"
        route.fulfill(json=payload)

    page.route(f"**/api/overlaps/{pair['id']}", with_flagged_project)
    page.goto(f"{live_server}/#overlap={pair['id']}")
    expect(page.locator("#overlap-content .cost-warning").first).to_be_visible()
    page.evaluate("window.print = () => {}")
    page.locator(".legend summary").click()
    page.locator("#print-report-button").click()
    expect(page.locator("#print-selected .cost-warning").first).to_contain_text("Printed total")
    expect(page.locator('#print-selected [data-src="cost_usd"]').first).to_have_text("$1,238,443")


@pytest.mark.parametrize("state", ["loading", "empty", "error"])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_phone_search_feedback_is_visible_and_recovers(live_server, browser_page, state, theme):
    page = browser_page
    start(page, live_server, 390, theme)
    pending = []
    if state == "loading":
        page.route("**/api/search?*", lambda route: pending.append(route))
    elif state == "error":
        page.route("**/api/search?*", lambda route: route.fulfill(status=503, json={"error": {"code": "unavailable", "message": "Unavailable"}}))
    page.locator("#search-input").fill("zzzz-no-such-place" if state == "empty" else "Savannah")
    feedback = page.locator("#search-state")
    expect(feedback).to_contain_text({"loading": "Searching local plans", "empty": "No local matches", "error": "Search unavailable. Check the local server and try again."}[state])
    expect(feedback).to_be_visible()
    expect(feedback).to_have_attribute("role", "status")
    expect(page.locator("#sheet-toggle")).to_have_attribute("aria-expanded", "false")
    expect(page.locator("#search-input")).to_be_editable()
    for route in pending:
        route.fulfill(json=[])
    page.unroute("**/api/search?*")
    page.locator("#search-input").fill("Okatie")
    expect(feedback).to_contain_text("local matches for Okatie")
    expect(feedback).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")


@pytest.mark.parametrize("width", [390, 768, 1440])
def test_filtered_project_empty_explains_recovery_and_search_remains_distinct(live_server, browser_page, width):
    page = browser_page
    start(page, f"{live_server}/?year_min=2199", width)
    page.locator("#projects-toggle").click()
    expect(page.locator("#projects-state")).to_have_text("No projects match the current filters. Open Filters and select Clear all filters to see all projects.")
    page.locator("#filters-toggle").click()
    page.locator("#filter-clear").click()
    expect(page.locator("#projects-state")).to_have_text("230 projects shown.")
    page.locator("#project-filter").fill("zzzz-no-project")
    expect(page.locator("#projects-state")).to_have_text("No projects match this search.")


def assert_exposed(control):
    expect(control).to_be_visible()
    assert control.evaluate("""element => {
      const r = element.getBoundingClientRect();
      return [0.2, 0.5, 0.8].every(x => [0.2, 0.5, 0.8].every(y => {
        const hit = document.elementFromPoint(r.left + r.width*x, r.top + r.height*y);
        return hit === element || element.contains(hit);
      }));
    }"""), f"Focused control is occluded: {control.get_attribute('id')}"
    assert control.evaluate("element => getComputedStyle(element).outlineStyle") != "none"


@pytest.mark.parametrize("width,path", [(390, "click"), (390, "pair"), (390, "area"), (768, "pair"), (1440, "pair")])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_keyboard_exposes_timeline_and_background_controls(live_server, browser_page, width, path, theme):
    page = browser_page
    start(page, live_server, width, theme)
    if path == "pair":
        page.get_by_test_id("overlap-row").first.locator("button").click()
        expect(page.locator("#overlap-content .overlap-project")).to_have_count(2)
    elif path == "area":
        page.locator("#search-input").fill("Savannah")
        expect(page.locator("#search-state")).to_contain_text("local matches for Savannah")
        page.locator("#search-input").press("Enter")
        page.locator("#explore-area").click()
        expect(page.locator("#area-results")).to_be_visible()
    else:
        page.locator("#sheet-toggle").click()
    if width == 390:
        expect(page.locator("#sheet-toggle")).to_have_attribute("aria-expanded", "true")
    # Begin within the sheet; actual reverse Tab reaches map controls and wraps to timeline.
    page.locator("#tour-launch").focus()
    reached = set()
    for _ in range(24):
        page.keyboard.press("Shift+Tab")
        active = page.locator(":focus")
        if not active.count():
            continue
        control_id = active.get_attribute("id")
        if control_id in {"timeline-play", "timeline-year", "timeline-all"}:
            assert_exposed(active)
            reached.add(control_id)
            if control_id == "timeline-year":
                page.keyboard.press("ArrowRight")
                expect(page.locator("#timeline-output")).to_be_visible()
                expect(page.locator("#timeline-output")).not_to_have_text("All years")
                if width == 390 and path == "click":
                    evidence = Path(__file__).resolve().parents[2] / "reviews/2026-09-26-gridlock-build/web-t43"
                    evidence.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(evidence / f"timeline-focus-390-{theme}.png"))
        elif active.evaluate("el => el.matches('.leaflet-control-zoom a, .leaflet-control-attribution a, #map-pair-open')"):
            assert_exposed(active)
        if len(reached) == 3:
            break
    assert reached == {"timeline-play", "timeline-year", "timeline-all"}
    # Forward Tab keeps the range and play button exposed too.
    for expected in ["timeline-year", "timeline-play"]:
        page.keyboard.press("Tab")
        expect(page.locator(f"#{expected}")).to_be_focused()
        assert_exposed(page.locator(f"#{expected}"))
    if width == 390:
        page.locator("#sheet-toggle").click()
        expect(page.locator("#sheet-toggle")).to_have_attribute("aria-expanded", "true")
        page.evaluate("""() => {
          const controls = [...document.querySelector('.panel').querySelectorAll(
            'a[href], button:not(:disabled), input:not(:disabled), summary')]
            .filter(el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
          controls.at(-1).focus();
        }""")
        # Forward Tab enters the timeline directly from the expanded sheet,
        # without first touching a map control that could collapse it.
        for expected in ["timeline-all", "timeline-year", "timeline-play"]:
            page.keyboard.press("Tab")
            expect(page.locator(f"#{expected}")).to_be_focused()
            assert_exposed(page.locator(f"#{expected}"))
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
