"""UI contract T1.4b: every remaining measurable gate over 24 real scenes."""

from pathlib import Path
from datetime import datetime, timezone
import json
import re

import pytest
from playwright.sync_api import expect, sync_playwright

from tests.e2e.ui_helpers import back_to_pair, close_more, open_more, reveal_brief

from tests.harness import required_test_port

from tests.e2e.audits.checks import (
    KEYBOARD_STATIC_JS, OVERFLOW_JS, TEXT_LINT_JS, external_request_urls,
)
from tests.e2e.audits.full_checks import (
    PERFORMANCE_INIT, STATES, THEMES, VIEWPORTS, matrix_issues, motion_source_issues,
    print_issues, recovery_issues, status_issues, surface_issues, timing_issues,
    wait_for_print,
)


ROOT = Path(__file__).resolve().parents[3]
MATRIX = [(state, width, height, theme) for state in STATES for width, height in VIEWPORTS for theme in THEMES]
AXE = (ROOT / "tests/e2e/vendor/axe.min.js").read_text(encoding="utf-8")


def open_phone_sheet(page):
    control = page.locator("#sheet-toggle")
    if control.is_visible() and control.get_attribute("aria-expanded") != "true":
        control.click()


def loaded_page(browser, live_server, width, height, theme):
    page = browser.new_page(viewport={"width": width, "height": height}, color_scheme=theme)
    page.add_init_script(PERFORMANCE_INIT)
    page.add_init_script("window.print = () => { window.auditPrinted = true; };")
    page.goto(live_server, wait_until="domcontentloaded")
    page.get_by_test_id("overlap-row").first.wait_for()
    page.get_by_test_id("project-feature").first.wait_for(state="attached")
    expect(page.locator("#timeline-year")).to_be_enabled()
    return page


def choose_scene(page, state):
    """Use actual controls, preserving the state even when the audit finds defects."""
    if state != "default":
        open_phone_sheet(page)
    if state == "empty":
        page.locator("#filters-toggle").click()
        page.locator("#more-filters summary").click()
        page.locator("#filter-year-min").fill("2199")
        page.locator("#filter-year-min").press("Tab")
        expect(page.get_by_test_id("overlap-row")).to_have_count(0)
        expect(page.locator("#status")).to_contain_text("0")
    elif state == "detail":
        page.get_by_test_id("overlap-row").first.locator("button").click()
        expect(page.locator("#overlap-content")).not_to_be_empty()
        reveal_brief(page)
        page.get_by_role("button", name="Copy brief", exact=True).wait_for()
        back_to_pair(page)
    elif state == "area":
        page.locator("#search-input").fill("Savannah")
        expect(page.locator("#search-options option")).not_to_have_count(0)
        page.locator("#search-input").press("Enter")
        page.locator("#explore-area").click()
        page.get_by_test_id("area-circle").wait_for(state="attached")
        expect(page.locator("#area-selection")).to_contain_text("40 km")
    elif state == "late":
        page.locator("#timeline-year").focus()
        page.keyboard.press("End")
        expect(page.locator("#timeline-output")).to_have_text(page.locator("#timeline-year").get_attribute("max"))
    elif state == "error":
        page.route("**/api/search?*", lambda route: route.fulfill(status=503, content_type="application/json", body='{"error":{"code":"unavailable","message":"Unavailable"}}'))
        page.locator("#search-input").fill("Savannah")
        expect(page.locator("#search-state")).to_contain_text("unavailable")


def slider_latency(page):
    return page.evaluate("""async () => {
      const range=document.querySelector('#timeline-year'), output=document.querySelector('#timeline-output');
      const previous=output.textContent;
      const target=range.value===range.min?range.max:range.min;
      const start=performance.now();
      range.value=target; range.dispatchEvent(new Event('input',{bubbles:true}));
      while(output.textContent!==target && performance.now()-start<1000)await new Promise(requestAnimationFrame);
      await new Promise(requestAnimationFrame);
      const elapsed=performance.now()-start;
      if(previous==='All years')document.querySelector('#timeline-all').click();
      else {range.value=previous;range.dispatchEvent(new Event('input',{bubbles:true}));}
      return elapsed;
    }""")


@pytest.mark.parametrize("state,width,height,theme", MATRIX, ids=[f"{s}-{w}-{t}" for s,w,h,t in MATRIX])
def test_full_contract_scene(live_server, state, width, height, theme, record_property):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            errors, urls, console = [], [], []
            context = browser.new_context(viewport={"width": width, "height": height}, color_scheme=theme)
            page = context.new_page()
            page.add_init_script(PERFORMANCE_INIT)
            page.add_init_script("window.print = () => { window.auditPrinted = true; };")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on("console", lambda message: console.append(message.text) if message.type == "error" else None)
            page.on("request", lambda request: urls.append(request.url))
            page.route("**/*", lambda route: route.abort() if external_request_urls([route.request.url], live_server) else route.continue_())
            page.goto(live_server, wait_until="domcontentloaded")
            page.get_by_test_id("overlap-row").first.wait_for()
            page.get_by_test_id("project-feature").first.wait_for(state="attached")
            expect(page.locator("#timeline-year")).to_be_enabled()
            initial = page.evaluate("window.auditTiming")
            choose_scene(page, state)
            # Wait for designed finite map motion before sampling its labels.
            page.wait_for_function("() => !document.querySelector('.leaflet-zoom-anim')")
            issues = surface_issues(page)
            issues["overflow"] = page.evaluate(OVERFLOW_JS)
            issues["keyboard"] = page.evaluate(KEYBOARD_STATIC_JS)
            lint = page.evaluate(TEXT_LINT_JS)
            issues["copy"] = lint["own"] + lint["visible"]
            issues["axe"] = [(v["id"], v["nodes"][0]["target"]) for v in page.evaluate(AXE + "\nwindow.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")["violations"]]
            page.emulate_media(reduced_motion="reduce")
            issues["reduced"] = surface_issues(page)["reduced"]
            # Expand disclosures through native controls so legend, raw evidence,
            # filters and their targets are measured as reachable parts of each scene.
            close_more(page)
            expected = page.locator('#overlap-content [data-src]').all_text_contents() if state == "detail" else []
            detail_expanded = {}
            brief_expanded = {}
            if state == "detail":
                for summary in page.locator(".detail-pane details > summary").all():
                    if summary.is_visible() and summary.locator("..").get_attribute("open") is None:
                        summary.click()
                detail_expanded = surface_issues(page)
                reveal_brief(page)
                for summary in page.locator("#brief-panel details > summary").all():
                    if summary.is_visible() and summary.locator("..").get_attribute("open") is None:
                        summary.click()
                brief_expanded = surface_issues(page)
                issues["overflow"] += page.evaluate(OVERFLOW_JS)
                brief_lint = page.evaluate(TEXT_LINT_JS)
                issues["copy"] += brief_lint["own"] + brief_lint["visible"]
                issues["axe"] += [(v["id"], v["nodes"][0]["target"]) for v in page.evaluate(AXE + "\nwindow.axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")["violations"]]
                back_to_pair(page)
                page.locator("#overlap-back").click()
            open_phone_sheet(page)
            for summary in page.locator("main details > summary").all():
                if summary.is_visible() and summary.locator("..").get_attribute("open") is None:
                    summary.click()
            expanded = surface_issues(page)
            open_more(page)
            for summary in page.locator("#more-menu details > summary").all():
                if summary.is_visible() and summary.locator("..").get_attribute("open") is None:
                    summary.click()
            menu_expanded = surface_issues(page)
            for category in ("contrast", "graphics", "targets", "fonts", "structure", "names", "motion", "reduced"):
                issues[category] = sorted(set(issues[category] + detail_expanded.get(category, []) + brief_expanded.get(category, []) + expanded[category] + menu_expanded[category]))
            close_more(page)
            # The active control's ring must contrast with its actual surrounding surface.
            page.keyboard.press("Tab")
            issues["graphics"] += sorted(set(surface_issues(page, focus_only="all")["graphics"]))
            shift=page.evaluate("window.auditTiming.shift")
            latency=slider_latency(page)
            issues["speed"] = timing_issues(initial["content"], latency, shift)
            record_property("measurements", json.dumps({"content_ms":initial["content"],"slider_ms":latency,"layout_shift":shift,"initial_shift":initial["shift"],"shifts":page.evaluate("window.auditTiming.shifts")}))
            record_property("zoom_colors", json.dumps(page.locator('.leaflet-control-zoom-in').evaluate("el=>({border:getComputedStyle(el).borderBottomColor,background:getComputedStyle(el).backgroundColor,parent:getComputedStyle(el.parentElement).backgroundColor})")))
            if state == "error":
                issues["recovery"] = recovery_issues(page.get_by_test_id("project-feature").count(), page.get_by_test_id("overlap-row").count(), page.locator("#search-state").inner_text(), errors)
            # Browser reports the intentionally fulfilled 503 resource separately from app errors.
            issues["errors"] = errors + [item for item in console if not (state=="error" and "503" in item and "Failed to load resource" in item)]
            issues["external"] = external_request_urls(urls, live_server)
            open_more(page)
            page.locator("#print-report-button").click()
            wait_for_print(page)
            page.emulate_media(media="print")
            issues["print"] = print_issues(page, expected)
            record_property("issues", json.dumps({key:value for key,value in issues.items() if value}))
            evidence_dir = Path.home() / "dev/gridlock-runs/audits" / f"port-{required_test_port()}"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            (evidence_dir / f"{state}-{width}-{theme}.json").write_text(json.dumps({
                "completed_at": datetime.now(timezone.utc).isoformat(), "state": state,
                "width": width, "theme": theme, "issues": issues,
                "timing": page.evaluate("window.auditTiming"), "slider_ms": latency,
            }, indent=2), encoding="utf-8")
            # One failure lists all independently measured problems in this scene.
            assert not {key:value for key,value in issues.items() if value}, json.dumps({key:value for key,value in issues.items() if value}, indent=2)
        finally:
            browser.close()


def test_authored_motion_lint_and_matrix_floor():
    assert not matrix_issues([(s,w,t) for s,w,h,t in MATRIX])
    issues = {path.name: motion_source_issues(path.read_text(encoding="utf-8")) for path in (ROOT / "web/css").glob("*.css")}
    assert not {key:value for key,value in issues.items() if value}


@pytest.mark.parametrize("width,height", VIEWPORTS)
@pytest.mark.parametrize("theme", THEMES)
def test_filter_count_announced_after_real_input(live_server, width, height, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = loaded_page(browser, live_server, width, height, theme)
            before=page.locator("#status").inner_text()
            choose_scene(page, "empty")
            assert not status_issues(before, page.locator("#status").inner_text(), page.locator("#status").get_attribute("role"))
        finally:
            browser.close()


@pytest.mark.parametrize("width,height", VIEWPORTS)
@pytest.mark.parametrize("theme", THEMES)
def test_longest_real_and_hostile_names_are_reachable(live_server, width, height, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = loaded_page(browser, live_server, width, height, theme)
            projects=page.request.get(live_server+"/api/projects").json()["features"]
            longest=max(projects,key=lambda item:len(item["properties"]["name"]))
            open_phone_sheet(page)
            open_more(page)
            page.locator("#projects-toggle").click()
            page.locator("#project-filter").fill(longest["properties"]["name"])
            page.get_by_test_id("project-row").filter(has_text=longest["properties"]["name"]).first.locator("button").click()
            expect(page.locator("#project-detail-heading")).to_have_text(longest["properties"]["name"])
            assert not surface_issues(page)["names"]
            assert not page.evaluate(OVERFLOW_JS)
            hostile=('<img src=x onerror="window.auditInjected=1">'+'W'*100)[:100]
            page.route("**/api/search?*", lambda route: route.fulfill(status=200,content_type="application/json",body=json.dumps([{"type":"place","label":hostile,"lat":32.1,"lon":-81.1,"ref":None}])))
            page.locator("#search-input").fill("Hostile")
            expect(page.locator("#search-options option")).to_have_count(1)
            page.locator("#search-input").press("Enter")
            expect(page.locator('#search-selection [data-src="label"]')).to_have_text(hostile)
            assert not page.locator("img[src=x]").count()
            assert page.evaluate("window.auditInjected === undefined")
            assert not surface_issues(page)["names"]
            assert not page.evaluate(OVERFLOW_JS)
        finally:
            browser.close()


@pytest.mark.parametrize("width,height", VIEWPORTS)
@pytest.mark.parametrize("theme", THEMES)
def test_blocked_brief_and_optional_map_keep_app_usable(live_server, width, height, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width":width,"height":height},color_scheme=theme)
            errors, requested = [], []
            page.on("pageerror", lambda error:errors.append(str(error)))
            page.route("**/*", lambda route:route.abort() if external_request_urls([route.request.url],live_server) else route.continue_())
            def blocked(route):
                requested.append(route.request.url)
                route.fulfill(status=503,content_type="application/json",body='{"error":{"code":"unavailable","message":"Unavailable"}}')
            page.route("**/api/map-config",blocked)
            page.route("**/api/briefs/**",blocked)
            page.goto(live_server)
            page.get_by_test_id("overlap-row").first.wait_for()
            page.get_by_test_id("project-feature").first.wait_for(state="attached")
            open_phone_sheet(page)
            page.get_by_test_id("overlap-row").first.locator("button").click()
            reveal_brief(page)
            expect(page.locator("#brief-state")).to_contain_text(re.compile("unavailable|could not|failed",re.I))
            assert any('/api/briefs/' in url for url in requested)
            assert any('/api/map-config' in url for url in requested)
            message=page.locator("#brief-state").inner_text()
            back_to_pair(page)
            page.locator("#overlap-back").click()
            expect(page.get_by_test_id("overlap-row").first).to_be_visible()
            assert not recovery_issues(page.get_by_test_id("project-feature").count(),page.get_by_test_id("overlap-row").count(),message,errors)
            page.locator("#search-input").fill("Savannah")
            expect(page.locator("#search-options option")).not_to_have_count(0)
            page.locator("#search-input").press("Enter")
            expect(page.locator("#search-selection")).to_contain_text("Savannah")
            assert slider_latency(page)<200
        finally:
            browser.close()
