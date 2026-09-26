"""First walking-skeleton audit set: ui-contract checks 1, 2, 6, 7, 10, 15."""

from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

from tests.e2e.audits.checks import (
    KEYBOARD_STATIC_JS,
    OVERFLOW_JS,
    TEXT_LINT_JS,
    color_literals_outside_tokens,
    external_request_urls,
    visible_focus_failures,
)


ROOT = Path(__file__).resolve().parents[3]
if not (ROOT / "web" / "index.html").exists():
    pytest.skip("no web shell yet", allow_module_level=True)


def _loaded_page(browser, base_url, width, height):
    page = browser.new_page(viewport={"width": width, "height": height}, color_scheme="light")
    with page.expect_response(lambda response: response.url.endswith("/api/overlaps") and response.ok):
        page.goto(base_url, wait_until="domcontentloaded")
    page.get_by_test_id("overlap-row").first.wait_for()
    return page


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_demo_shell_has_no_errors_or_external_requests(live_server, width, height):
    errors, urls = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": height}, color_scheme="light")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
            page.on("request", lambda request: urls.append(request.url))
            page.route("**/*", lambda route: route.continue_() if not external_request_urls([route.request.url], live_server) else route.abort())
            with page.expect_response(lambda response: response.url.endswith("/api/overlaps") and response.ok):
                page.goto(live_server, wait_until="domcontentloaded")
            page.get_by_test_id("overlap-row").first.wait_for()
            assert not errors, errors
            assert not external_request_urls(urls, live_server), external_request_urls(urls, live_server)
        finally:
            browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_every_tab_stop_has_changed_visible_focus(live_server, width, height):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = _loaded_page(browser, live_server, width, height)
            assert not visible_focus_failures(page)
        finally:
            browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_keyboard_subset_reaches_ranked_pair(live_server, width, height):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = _loaded_page(browser, live_server, width, height)
            assert not page.evaluate(KEYBOARD_STATIC_JS)
            page.keyboard.press("Tab")
            skip = page.get_by_role("link", name="Skip to opportunities")
            expect(skip).to_be_focused()
            page.keyboard.press("Enter")
            expect(page.locator("#opportunities")).to_be_focused()
            first = page.get_by_test_id("overlap-row").first.get_by_role("button")
            first.focus()
            page.keyboard.press("Enter")
            expect(first).to_have_attribute("aria-pressed", "true")
        finally:
            browser.close()


@pytest.mark.parametrize("width,height", [(768, 900), (390, 844), (320, 700)])
def test_shell_has_no_unclipped_horizontal_overflow(live_server, width, height):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = _loaded_page(browser, live_server, width, height)
            assert not page.evaluate(OVERFLOW_JS)
        finally:
            browser.close()


def test_authored_color_and_visible_copy_lint(live_server):
    assert not color_literals_outside_tokens(ROOT)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = _loaded_page(browser, live_server, 1440, 900)
            result = page.evaluate(TEXT_LINT_JS)
            assert not result["own"], result["own"]
            assert not result["visible"], result["visible"]
        finally:
            browser.close()


def test_phone_default_has_no_axe_violations(live_server):
    axe_source = (ROOT / "tests" / "e2e" / "vendor" / "axe.min.js").read_text(encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = _loaded_page(browser, live_server, 390, 844)
            violations = page.evaluate(
                axe_source + "\nwindow.axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']}})"
            )["violations"]
            assert not violations, [(item["id"], item["nodes"][0]["target"]) for item in violations]
        finally:
            browser.close()
