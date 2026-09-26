"""Downloads preserve the server matrix; Letter reports preserve plan evidence."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import pytest
from playwright.sync_api import expect, sync_playwright


def open_reports(page):
    page.locator(".legend summary").click()
    expect(page.get_by_role("button", name="Print report", exact=True)).to_be_visible()


@pytest.mark.parametrize("pair_id,source_page", [
    ("desc-p41__sertp-p107-9bc088", 107),
    ("desc-p41__sertp-p111-fe1e3b", 111),
])
def test_mcintosh_detail_and_print_preserve_work_location_limits(live_server, pair_id, source_page):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.print = () => { window.printCalls = 1; }")
        page.goto(f"{live_server}/#overlap={pair_id}")
        payload = page.request.get(f"{live_server}/api/overlaps/{pair_id}").json()
        pair = payload["overlap"]
        detail = page.get_by_test_id("overlap-detail")
        expect(detail.locator('[data-src="touch_detail"]')).to_have_text(pair["touch_detail"])
        expect(detail.locator('[data-src="can_share"]')).to_have_text(pair["can_share"])
        expect(detail).to_contain_text("Verify work locations")
        expect(detail).to_contain_text("Deerfield Switching Station, location not stated")
        if source_page == 111:
            expect(detail).to_contain_text("6.7-mile Goshen (Savannah)–Georgia Pacific (Rincon)")
            expect(detail).to_contain_text("does not establish work at McIntosh")
        open_reports(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        selected = page.locator("#print-selected")
        expect(selected.locator('[data-src="touch_detail"]')).to_have_text(pair["touch_detail"])
        expect(selected.locator('[data-src="can_share"]')).to_have_text(pair["can_share"])
        assert selected.locator('a[href$="#page=41"]').count() >= 1
        assert selected.locator(f'a[href$="#page={source_page}"]').count() >= 1
        browser.close()


@pytest.mark.parametrize("params", [
    {},
    {"utility": ["Dominion Energy SC", "Georgia Power"], "band": "touching", "cross_state": "true"},
    {"year_min": "2199"},
])
def test_csv_matches_current_filters_and_visible_ranked_count(live_server, params):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("request", lambda request: external.append(request.url)
                if urlsplit(request.url).netloc != urlsplit(live_server).netloc else None)
        page.goto(live_server)
        open_reports(page)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        if params:
            page.locator("#filters-toggle").click()
            if "year_min" in params or "cross_state" in params:
                page.locator("#more-filters summary").click()
            for utility in params.get("utility", []):
                page.get_by_label(utility, exact=True).check()
            if "band" in params:
                page.locator("#filter-band").select_option(params["band"])
                page.locator("#filter-cross-state").select_option(params["cross_state"])
            if "year_min" in params:
                page.locator("#filter-year-min").fill(params["year_min"])
                page.locator("#filter-year-min").press("Tab")
        query = urlencode(params, doseq=True)
        pairs = page.request.get(f"{live_server}/api/overlaps?{query}").json()
        assert bool(pairs) == ("year_min" not in params)
        expect(page.get_by_test_id("overlap-row")).to_have_count(len(pairs))
        expect(page.locator("#overlap-count")).to_have_text(f"{len(pairs)} pairs")
        control = page.get_by_role("button", name="Export CSV", exact=True)
        expect(control).to_be_enabled()
        control.focus()
        with page.expect_download() as received:
            page.keyboard.press("Enter")
        download = received.value
        assert download.suggested_filename == "gridlock-overlaps.csv"
        raw = Path(download.path()).read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf")
        assert raw == page.request.get(f"{live_server}/api/export/overlaps.csv?{query}").body()
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
        assert [row["Overlap ID"] for row in rows] == [pair["id"] for pair in pairs]
        assert [int(row["Rank"]) for row in rows] == [pair["rank"] for pair in pairs]
        assert [float(row["Distance km"]) for row in rows] == [pair["distance_km"] for pair in pairs]
        assert all(row["Coordination status"] == "" for row in rows)
        assert "Coordination status" in raw.decode("utf-8-sig")
        assert errors == [] and external == []
        browser.close()


@pytest.mark.parametrize("width,theme", [(1440, "light"), (390, "dark")])
def test_letter_print_contains_selected_pair_sources_and_screening_assumptions(live_server, width, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}'); window.print = () => {{ window.printCalls = (window.printCalls || 0) + 1; }}")
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("request", lambda request: external.append(request.url)
                if urlsplit(request.url).netloc != urlsplit(live_server).netloc else None)
        page.goto(f"{live_server}/?band=touching&cross_state=true")
        open_reports(page)
        first = page.get_by_test_id("overlap-row").first
        expect(first).to_be_visible()
        pair_id = first.get_attribute("data-overlap-id")
        detail = page.request.get(f"{live_server}/api/overlaps/{pair_id}").json()
        first.locator("button").click()
        expect(page.locator("#overlap-content")).to_contain_text(detail["project_a"]["properties"]["name"])
        button = page.get_by_role("button", name="Print report", exact=True)
        button.focus()
        page.keyboard.press("Enter")
        page.wait_for_function("() => window.printCalls === 1")
        report = page.locator("#print-report")
        selected = report.locator("#print-selected")
        content = selected.text_content()
        pair = detail["overlap"]
        for value in [pair["id"], pair["touch_reason"], pair["touch_detail"], pair["band_label"],
                      f'{pair["distance_km"]} km', f'{pair["year_gap"]} years', detail["savings"]["basis"]]:
            assert value in content
        for key in ("project_a", "project_b"):
            props = detail[key]["properties"]
            for value in (props["name"], props["utility"], props["accuracy"], props["source"]["doc"]):
                assert value in content
            assert selected.locator(f'a[href$="#page={props["source"]["page"]}"]').count() >= 1
        assert "$54,000 to $161,000" in content
        assert "possibly touching" in content
        assert "Team screening assumption" in report.text_content()
        assert "1% to 3%" in report.text_content()
        assert "shared asset" in report.text_content()
        assert "Independent student project" in report.text_content()
        assert "band: touching" in report.text_content() and "cross_state: true" in report.text_content()
        assert report.locator(".coordination-status").evaluate_all("nodes => nodes.every(node => node.textContent === '')")
        pair_count = len(page.request.get(f"{live_server}/api/overlaps?band=touching&cross_state=true").json())
        assert report.locator("tbody tr").count() == pair_count
        page.emulate_media(media="print")
        expect(page.locator(".workspace")).not_to_be_visible()
        expect(report).to_be_visible()
        run = Path.home() / "dev" / "gridlock-runs" / "web-2-T2.9"
        run.mkdir(parents=True, exist_ok=True)
        pdf = page.pdf(path=str(run / f"letter-{width}-{theme}.pdf"), prefer_css_page_size=True)
        assert b"/MediaBox [0 0 612 792]" in pdf
        # A phone initiates the same Letter document; inspect at paper width after triggering.
        page.set_viewport_size({"width": 1440 if width == 1440 else 816, "height": 1056})
        assert report.evaluate("el => el.scrollWidth <= el.clientWidth + 1")
        assert report.locator("td, th").evaluate_all("nodes => nodes.every(el => el.scrollWidth <= el.clientWidth + 1)")
        page.screenshot(path=str(run / f"letter-{width}-{theme}.png"), full_page=True)
        assert errors == [] and external == []
        browser.close()


def test_empty_print_and_download_failure_recover(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.print = () => { window.printCalls = (window.printCalls || 0) + 1; }")
        page.goto(f"{live_server}/?year_min=2199")
        open_reports(page)
        control = page.get_by_role("button", name="Export CSV", exact=True)
        expect(control).to_be_enabled()
        page.route("**/api/export/overlaps.csv*", lambda route: route.fulfill(status=503, body="unavailable"))
        control.click()
        expect(page.locator("#export-status")).to_contain_text("Could not export CSV")
        expect(control).to_be_enabled()
        page.unroute("**/api/export/overlaps.csv*")
        with page.expect_download():
            control.click()
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        assert "No overlap selected" in page.locator("#print-report").text_content()
        assert "No ranked overlaps match the current filters" in page.locator("#print-report").text_content()
        browser.close()


def test_print_failure_and_filtered_load_error_do_not_print_stale_results(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.print = () => { window.printCalls = (window.printCalls || 0) + 1; }")
        page.goto(live_server)
        open_reports(page)
        first = page.get_by_test_id("overlap-row").first
        expect(first).to_be_visible()
        pair_id = first.get_attribute("data-overlap-id")
        first.locator("button").click()
        expect(page.locator("#overlap-content")).not_to_be_empty()
        page.route(f"**/api/overlaps/{pair_id}", lambda route: route.fulfill(status=503, body="unavailable"))
        page.get_by_role("button", name="Print report", exact=True).click()
        expect(page.locator("#export-status")).to_contain_text("Could not prepare print report")
        assert page.evaluate("window.printCalls || 0") == 0
        page.unroute(f"**/api/overlaps/{pair_id}")
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        page.route("**/api/overlaps?band=touching", lambda route: route.fulfill(status=503, body="unavailable"))
        page.locator("#filters-toggle").click()
        page.locator("#filter-band").select_option("touching")
        expect(page.get_by_test_id("error-state")).to_be_visible()
        expect(page.get_by_role("button", name="Export CSV", exact=True)).to_be_disabled()
        expect(page.get_by_role("button", name="Print report", exact=True)).to_be_disabled()
        browser.close()


def test_download_keeps_server_escaped_cells_and_print_treats_names_as_text(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.print = () => { window.printCalls = 1; }")
        page.goto(live_server)
        open_reports(page)
        first = page.get_by_test_id("overlap-row").first
        expect(first).to_be_visible()
        pair_id = first.get_attribute("data-overlap-id")
        detail = page.request.get(f"{live_server}/api/overlaps/{pair_id}").json()
        hostile = '<img src="https://invalid.example/image" onerror="window.injected=1">'
        detail["project_a"]["properties"]["name"] = hostile
        page.route(f"**/api/overlaps/{pair_id}", lambda route: route.fulfill(json=detail))
        first.locator("button").click()
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        assert hostile in page.locator("#print-selected").text_content()
        assert page.locator("#print-report img, #print-report script").count() == 0
        assert page.evaluate("window.injected || 0") == 0
        raw = b"\xef\xbb\xbfRank,Project A,Distance km\r\n1,'=SUM(1),-1.5\r\n"
        page.route("**/api/export/overlaps.csv*", lambda route: route.fulfill(
            body=raw, content_type="text/csv", headers={"Content-Disposition": 'attachment; filename="gridlock-overlaps.csv"'}))
        with page.expect_download() as received:
            page.get_by_role("button", name="Export CSV", exact=True).click()
        assert Path(received.value.path()).read_bytes() == raw
        browser.close()


def test_selection_change_cancels_pending_print_with_a_visible_message(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("""(() => {
          window.print = () => { window.printCalls = (window.printCalls || 0) + 1; };
          const original = window.fetch;
          window.fetch = (url, options) => {
            if (window.delayPrint && String(url).startsWith('/api/overlaps/')) {
              window.delayPrint = false;
              return new Promise(resolve => { window.releasePrint = () => resolve(original(url, options)); });
            }
            return original(url, options);
          };
        })();""")
        page.goto(f"{live_server}/?band=touching")
        open_reports(page)
        first = page.get_by_test_id("overlap-row").first
        expect(first).to_be_visible()
        first.locator("button").click()
        expect(page.locator("#overlap-content")).not_to_be_empty()
        page.evaluate("window.delayPrint = true")
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => typeof window.releasePrint === 'function'")
        page.locator("#overlap-back").click()
        page.get_by_test_id("overlap-row").nth(1).locator("button").click()
        page.evaluate("window.releasePrint()")
        expect(page.locator("#export-status")).to_contain_text("Selection changed")
        assert page.evaluate("window.printCalls || 0") == 0
        expect(page.get_by_role("button", name="Print report", exact=True)).to_be_enabled()
        browser.close()


def test_approximate_distant_pair_print_does_not_claim_possibly_touching(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.print = () => { window.printCalls = 1; }")
        pairs = page.request.get(f"{live_server}/api/overlaps?band=lt_40km").json()
        pair = next(item for item in pairs if item["accuracy_pair"] == "approximate")
        assert pair["distance_km"] >= 8
        page.goto(f'{live_server}/?band=lt_40km#overlap={pair["id"]}')
        expect(page.locator("#overlap-content")).not_to_be_empty()
        open_reports(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        content = page.locator("#print-selected").text_content()
        assert pair["id"] in content and pair["band_label"] in content
        assert "Approximate locations" in content
        assert "possibly touching" not in content
        browser.close()
