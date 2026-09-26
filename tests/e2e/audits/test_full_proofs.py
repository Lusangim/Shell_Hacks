"""Broken scratch surfaces prove each added measurement detects its defect."""

import pytest
from playwright.sync_api import sync_playwright

from tests.e2e.audits.full_checks import surface_issues
from tests.e2e.audits.full_checks import (
    STATES, THEMES, VIEWPORTS, matrix_issues, motion_source_issues,
    print_issues, recovery_issues, status_issues, timing_issues,
    wait_for_print,
    MINIMUM_JS,
)


CASES = [
    ("contrast", '<p style="color:#aaa">Low contrast</p>', '<p>Readable text</p>'),
    ("contrast", '<p style="opacity:.3">Faint text</p>', '<p>Opaque text</p>'),
    ("contrast", '<div style="background:#222"><p style="color:#555">Dark backing</p></div>', '<div style="background:#222"><p style="color:#eee">Dark backing</p></div>'),
    ("graphics", '<button style="border:2px solid #ddd">Go</button>', '<button style="border:2px solid #222">Go</button>'),
    ("graphics", '<svg width="100" height="20"><path class="project-line" d="M0 10 L100 10" stroke="#aaa" stroke-opacity=".3" stroke-width="4"/></svg>', '<svg width="100" height="20"><path class="project-line" d="M0 10 L100 10" stroke="#222" stroke-width="4"/></svg>'),
    ("targets", '<button style="width:20px;height:20px;padding:0">X</button>', '<button>Go</button>'),
    ("fonts", '<p style="font-size:8px">Tiny body</p>', '<p>Readable body</p>'),
    ("fonts", '<input aria-label="Search" style="font-size:12px">', '<input aria-label="Search">'),
    ("fonts", '<span data-map-label style="font-size:12px;display:block;transform:scale(.5)">Scaled map label</span>', '<span data-map-label style="font-size:12px">Map label</span>'),
    ("motion", '<button style="transition:height 600ms ease-in">Go</button>', '<button style="transition:opacity 160ms ease-out">Go</button>'),
    ("structure", '<h3>Skipped level</h3><input>', '<h2>Ordered level</h2><input aria-label="Search">'),
    ("reduced", '<p style="opacity:0">Hidden answer</p>', '<p>Visible answer</p>'),
    ("reduced", '<style>@keyframes spin {to {transform:rotate(360deg)}}</style><p style="animation:spin 1s infinite">Endless</p>', '<p>Still</p>'),
    ("names", '<p data-src="name" style="width:40px;overflow:hidden;white-space:nowrap">' + 'W' * 100 + '</p>', '<p data-src="name" style="overflow-wrap:anywhere">' + 'W' * 100 + '</p>'),
]


@pytest.mark.parametrize("category,broken,repaired", CASES)
def test_surface_probe_red_then_green(category, broken, repaired):
    shell = '''<html lang="en"><title>Audit scratch</title><style>
    body {margin:16px;background:#fafafa;color:#202020;font:16px/1.4 system-ui}
    button,input {min-width:44px;min-height:44px;font-size:16px;background:#fafafa;color:#202020}
    </style><main><h1>Scratch</h1><section role="region" aria-label="Project map"></section>CONTENT</main></html>'''
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
            page.set_content(shell.replace("CONTENT", broken).replace("min-width:44px;", ""))
            assert surface_issues(page)[category], f"RED proof missed {category}"
            page.set_content(shell.replace("CONTENT", repaired))
            assert not surface_issues(page)[category], f"GREEN proof rejected {category}"
        finally:
            browser.close()


def test_status_probe_rejects_stale_or_silent_count():
    assert status_issues("10 pairs", "10 pairs", "status")
    assert status_issues("10 pairs", "0 pairs", None)
    assert not status_issues("10 pairs", "0 pairs", "status")


def test_performance_probe_rejects_each_boundary():
    assert timing_issues(2500, 10, 0)
    assert timing_issues(100, 200, 0)
    assert timing_issues(100, 10, .1)
    assert not timing_issues(2499, 199, .099)


def test_recovery_probe_rejects_blank_surface_and_unhelpful_message():
    assert recovery_issues(0, 0, "Oops", [])
    assert recovery_issues(1, 1, "Try again", ["uncaught"])
    assert not recovery_issues(1, 1, "Check the local server and try again.", [])


def test_motion_source_probe_catches_inactive_rules():
    assert motion_source_issues("@media(max-width:390px){.panel{transition:height 250ms ease-in}}")
    assert motion_source_issues("button{transition:all 100ms}")
    assert not motion_source_issues("button{transition:opacity 100ms ease-out}")


def test_matrix_probe_rejects_missing_state():
    cases = [(state, width, theme) for state in STATES for width, _ in VIEWPORTS for theme in THEMES]
    assert len(cases) == 24
    assert matrix_issues(cases[:-1])
    assert not matrix_issues(cases)


def test_print_probe_rejects_controls_missing_fields_and_truncated_detail():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.emulate_media(media="print")
            page.set_content('<article id="print-report"><button>Export</button><p>Partial</p></article>')
            assert len(print_issues(page, ["Full evidence"])) == 5
            page.set_content('''<article id="print-report"><p data-src="report_date">2026-09-26</p>
              <p data-src="filters">All overlaps</p><p data-src="source_documents">Public plan, p. 1</p>
              <p>Full evidence</p></article>''')
            assert not print_issues(page, ["Full evidence"])
        finally:
            browser.close()


def test_print_wait_respects_strict_csp():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content('''<meta http-equiv="Content-Security-Policy" content="default-src 'self'">
              <main><h1>Strict print scratch</h1></main>''')
            page.evaluate("() => { setTimeout(() => { window.auditPrinted=true; }, 100); }")
            wait_for_print(page)
            assert page.evaluate("() => window.auditPrinted === true")
        finally:
            browser.close()


def test_focus_contrast_batch_checks_the_final_control():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content('''<style>body{background:#fafafa}
              button:focus{outline:3px solid #222}button:last-child:focus{outline-color:#ddd}</style>
              <main>''' + ''.join(f'<button id="stop-{i}">Control {i}</button>' for i in range(60)) + '</main>')
            issues = surface_issues(page, focus_only="all")["graphics"]
            assert len(issues) == 1 and "#stop-59 focus" in issues[0]
            page.add_style_tag(content="button:last-child:focus{outline-color:#222}")
            assert not surface_issues(page, focus_only="all")["graphics"]
        finally:
            browser.close()


@pytest.mark.parametrize("inactive", [
    '<button disabled><span>−</span></button>',
    '<a href="#" role="button" aria-label="Zoom out" aria-disabled="true"><span>−</span></a>',
])
def test_contrast_exempts_inactive_controls_but_not_active_controls_or_body(inactive):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page=browser.new_page()
            style='<style>body{background:#fafafa}span{color:#bbb;font-size:22px;font-weight:700}</style>'
            page.set_content(style+'<main>'+inactive+'</main>')
            assert not surface_issues(page)["contrast"]
            page.set_content(style+'<main><a href="#" role="button" aria-label="Zoom out" aria-disabled="false"><span>−</span></a></main>')
            assert surface_issues(page)["contrast"]
            page.set_content(style+'<main><p aria-disabled="true"><span>Body text remains measured</span></p></main>')
            assert surface_issues(page)["contrast"]
        finally:
            browser.close()


def test_default_scene_preserves_collapsed_arrival_before_expanded_audit():
    from tests.e2e.audits.test_full_matrix import choose_scene

    with sync_playwright() as playwright:
        browser=playwright.chromium.launch()
        try:
            page=browser.new_page(viewport={"width":390,"height":844})
            page.set_content('''<button id="sheet-toggle" aria-expanded="false"
              onclick="this.setAttribute('aria-expanded','true')">Expand opportunities</button>''')
            choose_scene(page,"default")
            assert page.locator('#sheet-toggle').get_attribute('aria-expanded') == 'false'
        finally:
            browser.close()


@pytest.mark.parametrize("minimum", [4.5, 3, 44, 11, 12, 16, 9])
def test_exact_minimum_equality_passes_and_just_below_fails(minimum):
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch()
        try:
            page=browser.new_page()
            compare=f"values => ({MINIMUM_JS})(...values)"
            assert not page.evaluate(compare,[minimum,minimum])
            assert page.evaluate(compare,[minimum-.001,minimum])
        finally:
            browser.close()


def test_target_at_43_999_fails_and_exactly_44_passes():
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch()
        try:
            page=browser.new_page(viewport={"width":390,"height":844})
            page.set_content('<button style="width:44px;height:44px;transform:scale(.999977272727)">Go</button>')
            width=page.locator('button').bounding_box()['width']
            assert 43.9989 < width < 44
            assert surface_issues(page)["targets"]
            page.locator('button').evaluate("el=>el.style.transform='none'")
            assert page.locator('button').bounding_box()['width'] == 44
            assert not surface_issues(page)["targets"]
        finally:
            browser.close()


def test_speed_boundaries_have_no_rounding_allowance():
    assert timing_issues(2500, 0, 0)
    assert timing_issues(0, 200, 0)
    assert timing_issues(0, 0, .1)
    assert not timing_issues(2499.999, 199.999, .099999)
