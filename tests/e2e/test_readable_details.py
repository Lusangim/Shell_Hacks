"""Readable detail summaries keep evidence, uncertainty, and selection together."""

import re
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright


MCINTOSH = "desc-p41__sertp-p107-9bc088"
FORBIDDEN = re.compile(r"desc-p|sertp-p|\bTAP\d+\b|\b[a-z]+_[a-z0-9_]+\b|data[/\\]|[A-Z]:[/\\]")


@pytest.mark.parametrize("band", ["touching", "lt_1_6km", "lt_8km", "lt_40km"])
def test_approximate_distance_wording_matches_band(live_server, band):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        pairs = page.request.get(f"{live_server}/api/overlaps").json()
        pair = next(p for p in pairs if p["band"] == band and p["accuracy_pair"] == "approximate")
        page.goto(f"{live_server}/#overlap={pair['id']}")
        detail = page.locator("#overlap-content")
        expect(detail).to_contain_text(pair["band_label"])
        expect(detail).to_contain_text("Approximate locations")
        if band == "touching":
            expect(detail).to_contain_text("possibly touching")
        else:
            expect(detail).not_to_contain_text("possibly touching")
        browser.close()


def test_filtered_unknown_and_placed_project_absence_are_distinct(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}/?utility=Dominion+Energy+SC")
        expect(page.locator("#overlap-count")).to_have_text("0 pairs")
        page.locator("#projects-toggle").click()
        page.locator('[data-project-ref="desc-p41"] button').click()
        expect(page.locator("#project-overlaps")).to_have_text("No related overlaps are shown by the current filters.")
        page.evaluate("document.dispatchEvent(new CustomEvent('gridlock:project-click', {detail:{projectId:'desc-p41'}}))")
        expect(page.locator("#status")).to_have_text("No related overlaps are shown by the current filters.")
        page.locator("#filters-toggle").click()
        page.locator("#filter-clear").click()
        expect(page.locator("#overlap-count")).to_have_text("489 pairs")
        page.evaluate("document.dispatchEvent(new CustomEvent('gridlock:project-click', {detail:{projectId:'desc-p41'}}))")
        expect(page.locator("#project-overlaps li")).to_have_count(14)
        page.evaluate("document.dispatchEvent(new CustomEvent('gridlock:project-click', {detail:{projectId:'desc-p3'}}))")
        expect(page.locator("#project-overlaps")).to_have_text("Location unknown; proximity cannot be assessed.")
        expect(page.locator("#status")).to_have_text("Location unknown; proximity cannot be assessed.")
        page.evaluate("document.dispatchEvent(new CustomEvent('gridlock:project-click', {detail:{projectId:'desc-p1'}}))")
        expect(page.locator("#project-overlaps")).to_have_text("This placed project has no overlap within 40 km in the loaded plans.")
        expect(page.locator("#no-overlap")).to_have_text("97 of 230 projects are not in computed pairs; 49 locations unknown")
        browser.close()


def assert_selection(page, payload):
    pair = payload["overlap"]
    expect(page.locator("#overlap-detail-heading")).to_have_text(f"Overlap #{pair['rank']}")
    assert page.url.endswith(f"#overlap={pair['id']}")
    assert page.evaluate("async () => (await import('/web/js/state.js')).state.selectedOverlapId") == pair["id"]
    visible_rows = page.locator(f'[data-overlap-id="{pair["id"]}"] button')
    if visible_rows.count():
        expect(visible_rows).to_have_attribute("aria-pressed", "true")
    highlighted = page.locator('[data-testid="project-feature"][data-selected="true"]').evaluate_all("els => els.map(el => el.dataset.projectId).sort()")
    assert highlighted == sorted([pair["a"], pair["b"]])
    page.locator(".legend").evaluate("el => el.open = true")
    page.get_by_role("button", name="Print report", exact=True).click()
    page.wait_for_function("() => window.printCalls > 0")
    page.evaluate("window.printCalls = 0")
    selected = page.locator("#print-selected")
    for key in ("project_a", "project_b"):
        assert payload[key]["properties"]["name"] in selected.text_content()


def test_filtered_deep_link_history_and_invalid_links_use_visible_selection(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.printCalls = 0; window.print = () => window.printCalls++")
        first = page.request.get(f"{live_server}/api/overlaps/{MCINTOSH}").json()
        second_id = "sertp-p68-a0289a__sertp-p72-81610d"
        second = page.request.get(f"{live_server}/api/overlaps/{second_id}").json()
        page.goto(f"{live_server}/?band=lt_40km#overlap={MCINTOSH}")
        expect(page.locator("#overlap-state")).to_contain_text("outside the current filters")
        assert_selection(page, first)
        page.evaluate("id => { location.hash = 'overlap=' + id; }", second_id)
        assert_selection(page, second)
        page.go_back()
        assert_selection(page, first)
        page.go_forward()
        assert_selection(page, second)
        for pair_id, message in [("invalid", "Unknown overlap link"), ("desc-p41__sertp-p999-deadbe", "stale")]:
            page.evaluate("id => { location.hash = 'overlap=' + id; }", pair_id)
            expect(page.locator("#overlap-state")).to_contain_text(message)
            assert page.evaluate("async () => (await import('/web/js/state.js')).state.selectedOverlapId") is None
            expect(page.locator('[data-testid="project-feature"][data-selected="true"]')).to_have_count(0)
            page.get_by_role("button", name="Print report", exact=True).click()
            page.wait_for_function("() => window.printCalls > 0")
            page.evaluate("window.printCalls = 0")
            assert "No overlap selected" in page.locator("#print-selected").text_content()
        browser.close()


@pytest.mark.parametrize("width,theme", [(1440, "light"), (390, "dark")])
def test_answer_first_blocks_keep_citations_and_visible_honesty(live_server, width, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        page.goto(f"{live_server}/#overlap={MCINTOSH}")
        detail = page.locator("#overlap-content")
        expect(detail).to_contain_text("Possible saving (estimate): $54,000 to $161,000")
        expect(detail.locator(".detail-block")).to_have_count(6)
        assert detail.locator(".detail-block").evaluate_all("nodes => nodes.every(n => n.querySelector(':scope > .detail-answer') && n.querySelectorAll(':scope > ul > li').length <= 3 && n.querySelector(':scope > details'))")
        expect(detail.locator("[data-src='assumption']").first).to_be_visible()
        expect(detail).to_contain_text("Not verified: the plans do not show shared work.")
        assert detail.get_by_role("link").count() == 2
        for link in detail.get_by_role("link").all():
            expect(link).to_be_visible()
            assert link.get_attribute("href").startswith("/api/sources/")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        run = Path.home() / "dev" / "gridlock-runs" / "web-T1.7"
        run.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(run / f"detail-{width}-{theme}.png"))
        browser.close()


def test_failed_detail_does_not_retain_prior_selection(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server}/#overlap={MCINTOSH}")
        expect(page.locator("#overlap-content")).to_contain_text("McIntosh")
        pair_id = "sertp-p68-a0289a__sertp-p72-81610d"
        page.route(f"**/api/overlaps/{pair_id}", lambda route: route.fulfill(status=503, body="Unavailable"))
        page.evaluate("id => { location.hash = 'overlap=' + id; }", pair_id)
        expect(page.locator("#overlap-state")).to_contain_text("Could not load this overlap detail")
        assert page.evaluate("async () => (await import('/web/js/state.js')).state.selectedOverlapId") is None
        expect(page.locator('[data-testid="project-feature"][data-selected="true"]')).to_have_count(0)
        browser.close()


def test_every_project_and_pair_detail_has_readable_expanded_evidence(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        texts = page.evaluate("""async () => {
          const { renderOverlapDetail } = await import('/web/js/overlap-detail.js');
          const { projectSummary } = await import('/web/js/project-detail.js');
          const projects = (await (await fetch('/api/projects')).json()).features;
          const pairs = await (await fetch('/api/overlaps')).json();
          const byId = new Map(projects.map(p => [p.properties.id, p]));
          const content = document.querySelector('#overlap-content');
          document.querySelector('#overlap-detail').hidden = false;
          const texts = [];
          for (const project of projects) {
            content.replaceChildren(projectSummary(project));
            content.querySelectorAll('details').forEach(d => d.open = true);
            texts.push({id:project.properties.id, text:content.innerText});
          }
          for (const pair of pairs) {
            renderOverlapDetail({overlap:pair, project_a:byId.get(pair.a), project_b:byId.get(pair.b), savings:pair.savings}, content, document.querySelector('#overlap-detail-heading'));
            content.querySelectorAll('details').forEach(d => d.open = true);
            const copy = Array.from(content.querySelectorAll('*')).filter(n => !n.closest('[data-src]'))
              .flatMap(n => Array.from(n.childNodes).filter(c => c.nodeType === Node.TEXT_NODE).map(c => c.textContent)).join(' ');
            texts.push({id:pair.id, text:content.innerText, copy});
          }
          return texts;
        }""")
        assert len(texts) == 719
        for view in texts:
            assert not FORBIDDEN.search(view["text"]), view
            assert not re.search(r"\b(?:undefined|NaN|null)\b|\[object", view["text"]), view
            assert not re.search(r"[\u2013\u2014]|\b(?:seamless|unleash|revolutionize|BETA)\b", view.get("copy", "")), view
        browser.close()
