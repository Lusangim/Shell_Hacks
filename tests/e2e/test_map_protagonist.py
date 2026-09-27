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
