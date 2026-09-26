"""Default-state browser safety gate, promoted when the web shell exists."""

from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
if not (ROOT / "web" / "index.html").exists():
    pytest.skip("no web shell yet", allow_module_level=True)


def test_default_1440_has_no_console_errors_or_axe_violations(live_server):
    axe_source = (ROOT / "tests" / "e2e" / "vendor" / "axe.min.js").read_text(encoding="utf-8")
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900}, color_scheme="light")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
            page.goto(live_server, wait_until="domcontentloaded")
            page.locator("#overlap-list li").first.wait_for()
            violations = page.evaluate(
                axe_source + "\nwindow.axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']}})"
            )["violations"]
            assert not errors, errors
            assert not violations, [(item["id"], item["nodes"][0]["target"]) for item in violations]
        finally:
            browser.close()
