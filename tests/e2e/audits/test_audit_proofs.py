"""Each quick-audit probe catches a deliberately broken scratch surface."""

from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.e2e.audits.checks import (
    KEYBOARD_STATIC_JS,
    OVERFLOW_JS,
    TEXT_LINT_JS,
    color_literals_outside_tokens,
    external_request_urls,
    visible_focus_failures,
)


def test_console_and_external_request_probes_catch_broken_page():
    errors, requests = [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: requests.append(request.url))
        page.route("https://example.invalid/**", lambda route: route.abort())
        page.set_content('<main><img src="https://example.invalid/remote.png"><script>throw Error("broken scratch")</script></main>')
        assert any("broken scratch" in error for error in errors)
        assert external_request_urls(requests, "http://127.0.0.1:8770") == ["https://example.invalid/remote.png"]
        browser.close()


def test_axe_probe_catches_broken_scratch_image():
    axe_source = (Path(__file__).resolve().parents[1] / "vendor" / "axe.min.js").read_text(encoding="utf-8")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_content('<html lang="en"><title>Broken</title><main><img src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs="></main></html>')
        result = page.evaluate(axe_source + "\nwindow.axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']}})")
        assert any(item["id"] == "image-alt" for item in result["violations"])
        browser.close()


def test_focus_probe_rejects_preexisting_shadow_without_focus_change():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_content('<style>button {outline:none; box-shadow:0 0 3px gray}</style><main><button>One</button><button>Two</button></main>')
        assert len(visible_focus_failures(page)) == 2
        browser.close()


def test_keyboard_structure_probe_catches_missing_target_and_positive_tabindex():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_content('<a class="skip-link" href="#absent">Skip</a><main><button tabindex="2" aria-controls="lost">Go</button></main>')
        issues = page.evaluate(KEYBOARD_STATIC_JS)
        assert any("positive tabindex" in issue for issue in issues)
        assert "broken skip target" in issues
        assert "aria-controls missing #lost" in issues
        browser.close()


def test_overflow_probe_catches_unclipped_wide_element():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 320, "height": 600})
        page.set_content('<main><div style="width:600px;height:20px">Too wide</div></main>')
        assert page.evaluate(OVERFLOW_JS)
        browser.close()


def test_copy_and_color_probes_catch_broken_scratch(tmp_path):
    path = tmp_path / "web" / "js"
    path.mkdir(parents=True)
    (tmp_path / "web" / "css").mkdir()
    (path / "bad.js").write_text('const color = "#abcdef";', encoding="utf-8")
    assert color_literals_outside_tokens(tmp_path) == ["web/js/bad.js:1"]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.set_content('<main><p>Broken—copy and undefined</p></main>')
        lint = page.evaluate(TEXT_LINT_JS)
        assert lint["own"] and lint["visible"]
        browser.close()
