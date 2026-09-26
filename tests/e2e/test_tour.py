"""Tour follows real records without changing the visitor's filter choices."""

import re
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_first_visit_invitation_keeps_projects_reachable(live_server, width, height, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, color_scheme=theme)
        page.add_init_script("""window.tourInitialCls = 0;
          new PerformanceObserver(list => {
            for (const entry of list.getEntries()) {
              if (!entry.hadRecentInput) window.tourInitialCls += entry.value;
            }
          }).observe({type: 'layout-shift', buffered: true});
        """)
        page.goto(live_server)
        expect(page.locator(".overlap-button").first).to_be_visible()
        invitation = page.get_by_role("button", name="New here? Take the tour", exact=True)
        expect(invitation).to_be_visible()
        page.wait_for_timeout(1000)
        initial_cls = page.evaluate("window.tourInitialCls")
        print({"width": width, "theme": theme, "initial_cls": initial_cls})
        assert initial_cls < 0.1
        if width == 390:
            first_view = page.evaluate("""() => {
              const rows = document.querySelectorAll('[data-testid="overlap-row"]');
              const panel = document.querySelector('.panel').getBoundingClientRect();
              const zoom = document.querySelector('.leaflet-control-zoom-in').getBoundingClientRect();
              return {secondRowBottom: rows[1].getBoundingClientRect().bottom,
                panelBottom: document.querySelector('.panel-body').getBoundingClientRect().bottom,
                zoomBottom: zoom.bottom, panelTop: panel.top};
            }""")
            print({"theme": theme, "first_view": first_view})
            assert first_view["secondRowBottom"] <= first_view["panelBottom"]
            assert first_view["zoomBottom"] <= first_view["panelTop"]
            page.locator("#sheet-toggle").click()
            expect(page.locator("#sheet-toggle")).to_have_attribute("aria-expanded", "true")
        projects = page.locator("#projects-toggle")
        # Trial click waits for the sheet transition, then checks the real pointer target.
        try:
            projects.click(trial=True, timeout=3000)
        except Exception:
            print({"theme": theme, "projects": projects.bounding_box(),
                   "invitation": page.locator("#tour-invitation-box").bounding_box()})
            raise
        button_box = projects.bounding_box()
        prompt_box = page.locator("#tour-invitation-box").bounding_box()
        print({"width": width, "theme": theme, "projects": button_box, "invitation": prompt_box})
        assert (button_box["x"] + button_box["width"] <= prompt_box["x"]
                or prompt_box["x"] + prompt_box["width"] <= button_box["x"]
                or button_box["y"] + button_box["height"] <= prompt_box["y"]
                or prompt_box["y"] + prompt_box["height"] <= button_box["y"])
        projects.click()
        expect(page.locator("#project-filter")).to_be_focused()
        records = page.request.get(f"{live_server}/api/projects").json()["features"]
        longest = max((item["properties"] for item in records), key=lambda item: len(item["name"]))
        page.locator("#project-filter").fill(longest["name"])
        page.locator(f'[data-project-ref="{longest["id"]}"] button').click()
        detail = page.get_by_test_id("project-detail")
        expect(detail.locator("#project-detail-heading")).to_have_text(longest["name"])
        expect(detail.get_by_role("link", name=f'{longest["source"]["doc"]}, p. {longest["source"]["page"]}')).to_be_visible()
        expect(invitation).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        page.get_by_role("button", name="Dismiss tour invitation").click()
        launch = page.get_by_role("button", name="Take the tour", exact=True)
        expect(invitation).not_to_be_visible()
        expect(launch).to_be_focused()
        launch.press("Enter")
        card = page.get_by_role("dialog", name="GridLock tour")
        expect(card).to_be_focused()
        page.keyboard.press("Escape")
        expect(card).not_to_be_visible()
        expect(launch).to_be_focused()
        page.reload()
        expect(invitation).not_to_be_visible()
        expect(launch).to_be_visible()
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_keyboard_tour_walk_and_focus_return(live_server, width, height, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, color_scheme=theme,
                                reduced_motion="reduce")
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("request", lambda request: external.append(request.url) if not request.url.startswith(live_server) else None)
        page.goto(live_server)
        expect(page.locator(".overlap-button").first).to_be_visible()
        launch = page.get_by_role("button", name="Take the tour", exact=True)
        expect(launch).to_be_visible()
        initial_query = page.evaluate("location.search")
        launch.focus()
        page.keyboard.press("Enter")
        card = page.get_by_role("dialog", name="GridLock tour")
        titles = []
        for _ in range(12):
            expect(card).to_be_visible()
            expect(card).to_be_focused()
            title = card.locator("h2").inner_text()
            titles.append(title)
            if len(titles) == 1:
                axe_source = (Path(__file__).parent / "vendor" / "axe.min.js").read_text(encoding="utf-8")
                audit = page.evaluate(axe_source + "\nwindow.axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']}})")
                assert audit["violations"] == [], audit["violations"]
            expect(page.locator(".tour-target")).to_have_count(1)
            assert page.locator(".tour-target").evaluate("el => getComputedStyle(el).outlineStyle") == "double"
            expect(card.locator("#tour-count")).to_have_text(re.compile(r"Step \d+ of \d+"))
            assert card.evaluate("el => { const r = el.getBoundingClientRect(); return r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight; }")
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            for button in card.get_by_role("button").all():
                box = button.bounding_box()
                assert box["height"] >= 44 and box["width"] >= 44
            if len(titles) == 2:
                card.get_by_role("button", name="Back", exact=True).focus()
                page.keyboard.press("Enter")
                expect(card.locator("h2")).to_have_text(titles[0])
                card.get_by_role("button", name="Next", exact=True).focus()
                page.keyboard.press("Enter")
                expect(card.locator("h2")).to_have_text(title)
            next_button = card.get_by_role("button", name=re.compile(r"^(Next|Finish tour)$"))
            last = next_button.inner_text() == "Finish tour"
            next_button.focus()
            page.keyboard.press("Enter")
            if last:
                break
        assert 8 <= len(titles) <= 12, titles
        assert {"Public plans, shared possibilities", "Read the map", "How pairs are ranked", "Find Savannah",
                "Open the top pair", "Check the source", "Estimates and uncertainty", "Compare years",
                "Narrow the results", "Keep a copy"}.issubset(titles), titles
        expect(card).not_to_be_visible()
        expect(launch).to_be_focused()
        assert page.evaluate("location.search") == initial_query
        expect(page.locator("#search-input")).to_have_value("")
        launch.press("Enter")
        expect(card).to_be_visible()
        page.keyboard.press("Escape")
        expect(card).not_to_be_visible()
        expect(launch).to_be_focused()
        launch.press("Enter")
        card.get_by_role("button", name="Skip tour", exact=True).click()
        expect(launch).to_be_focused()
        assert errors == []
        assert external == []
        browser.close()


def test_prompt_persistence_and_storage_denied(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        expect(page.get_by_role("button", name="New here? Take the tour", exact=True)).to_be_visible()
        page.get_by_role("button", name="Dismiss tour invitation").click()
        page.reload()
        expect(page.get_by_role("button", name="New here? Take the tour", exact=True)).not_to_be_visible()
        expect(page.get_by_role("button", name="Take the tour", exact=True)).to_be_visible()
        page.close()
        page = browser.new_page()
        page.add_init_script("Storage.prototype.getItem = () => { throw new Error('denied'); }; Storage.prototype.setItem = () => { throw new Error('denied'); };")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(live_server)
        page.get_by_role("button", name="New here? Take the tour", exact=True).click()
        expect(page.get_by_role("dialog", name="GridLock tour")).to_be_visible()
        page.keyboard.press("Escape")
        expect(page.get_by_role("button", name="Take the tour", exact=True)).to_be_focused()
        page.reload()
        page.get_by_role("button", name="Dismiss tour invitation").click()
        page.get_by_role("button", name="Take the tour", exact=True).click()
        expect(page.get_by_role("dialog", name="GridLock tour")).to_be_visible()
        page.keyboard.press("Escape")
        expect(page.locator(".overlap-button").first).to_be_visible()
        assert errors == []
        browser.close()


def test_missing_and_hidden_targets_skip_without_stranded_focus(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(live_server)
        expect(page.locator(".overlap-button").first).to_be_visible()
        page.evaluate("document.querySelector('#timeline').remove(); document.querySelector('#map').hidden = true;")
        page.get_by_role("button", name="Take the tour", exact=True).click()
        card = page.get_by_role("dialog", name="GridLock tour")
        titles = []
        for _ in range(12):
            expect(card).to_be_focused()
            titles.append(card.locator("h2").inner_text())
            button = card.get_by_role("button", name=re.compile(r"^(Next|Finish tour)$"))
            last = button.inner_text() == "Finish tour"
            button.press("Enter")
            if last:
                break
        assert "Read the map" not in titles
        assert "Compare years" not in titles
        expect(card).not_to_be_visible()
        expect(page.get_by_role("button", name="Take the tour", exact=True)).to_be_focused()
        assert errors == []
        browser.close()


def test_tour_keeps_active_filters_and_skips_failed_detail(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(f"{live_server}/?band=touching")
        expect(page.locator(".overlap-button").first).to_be_visible()
        rows = page.locator(".overlap-button").count()
        page.route("**/api/overlaps/*", lambda route: route.fulfill(status=503, content_type="application/json", body='{}'))
        page.get_by_role("button", name="Take the tour", exact=True).click()
        card = page.get_by_role("dialog", name="GridLock tour")
        titles = []
        for _ in range(12):
            expect(card).to_be_focused()
            titles.append(card.locator("h2").inner_text())
            button = card.get_by_role("button", name=re.compile(r"^(Next|Finish tour)$"))
            last = button.inner_text() == "Finish tour"
            button.press("Enter")
            if last:
                break
        expect(card).not_to_be_visible()
        assert "Check the source" not in titles
        assert "Estimates and uncertainty" not in titles
        expect(page.locator("#filter-band")).to_have_value("touching")
        assert page.evaluate("location.search") == "?band=touching"
        expect(page.locator(".overlap-button")).to_have_count(rows)
        expect(page.get_by_role("button", name="Take the tour", exact=True)).to_be_focused()
        assert errors == []
        browser.close()
