"""Downloads preserve the server matrix; Letter reports preserve plan evidence."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from urllib.parse import urlencode, urlsplit

import pytest
from playwright.sync_api import expect, sync_playwright

from tests.e2e.ui_helpers import close_more, open_more


def open_reports(page):
    open_more(page)
    expect(page.get_by_role("button", name="Print report", exact=True)).to_be_visible()


FORBIDDEN_REPORT = re.compile(
    r"\b(?:desc-p\d+|sertp-p\d+-[a-f0-9]+|TAP\d+)\b|"
    r"\b[a-z]+(?:_[a-z0-9]+)+\b|\bdata[\\/]|\b[A-Za-z]:[\\/]|"
    r"\b(?:undefined|NaN|null)\b|\[object"
)


def assert_readable_report(report):
    assert not FORBIDDEN_REPORT.search(report.text_content())
    assert report.locator("details:not([open])").count() == 0


@pytest.mark.parametrize("width", [1440, 390])
def test_ranked_print_qualifies_only_inferred_utilities(live_server, width):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.add_init_script("window.print = () => { window.printCalls = 1; }")
        page.goto(live_server)
        expect(page.locator(".overlap-button").first).to_be_visible()
        open_reports(page)
        open_more(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        projects = {item["properties"]["id"]: item["properties"] for item in
                    page.request.get(f"{live_server}/api/projects").json()["features"]}
        pairs = page.request.get(f"{live_server}/api/overlaps").json()
        labels = page.locator('#print-report tbody [data-src="utility"]').all_text_contents()
        expected = [projects[pair[key]]["utility"] +
                    (" (inferred)" if projects[pair[key]]["utility_basis"] == "inferred_from_location" else "")
                    for pair in pairs for key in ("a", "b")]
        assert "Georgia Power (inferred)" in expected
        assert "Dominion Energy SC" in expected
        assert labels == expected
        browser.close()


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
        open_more(page)
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
        open_more(page)
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
        close_more(page)
        first.locator("button").click()
        expect(page.locator("#overlap-content")).to_contain_text(detail["project_a"]["properties"]["name"])
        open_more(page)
        button = page.get_by_role("button", name="Print report", exact=True)
        button.focus()
        page.keyboard.press("Enter")
        page.wait_for_function("() => window.printCalls === 1")
        report = page.locator("#print-report")
        selected = report.locator("#print-selected")
        content = selected.text_content()
        pair = detail["overlap"]
        gap = pair["year_gap"]
        gap_words = "Same in-service year" if gap == 0 else f'{gap} year{"" if gap == 1 else "s"} apart'
        for value in [f'Overlap #{pair["rank"]}', "Shared named endpoint", pair["touch_detail"], pair["band_label"],
                      f'{pair["distance_km"]} km', gap_words,
                      detail["savings"]["basis"].replace(pair["a"], f'{detail["project_a"]["properties"]["utility"]} project')]:
            assert value in content
        for key in ("project_a", "project_b"):
            props = detail[key]["properties"]
            for value in (props["name"], props["utility"], props["accuracy"], props["source"]["doc"]):
                assert value in content
            assert selected.locator(f'a[href$="#page={props["source"]["page"]}"]').count() >= 1
        assert "$62,000 to $264,000" in content
        assert "possibly touching" in content
        assert "Team unit-cost file" in report.text_content()
        assert "escalated to 2026 at 4% a year" in report.text_content()
        assert "shared asset" in report.text_content()
        assert "Independent student project" in report.text_content()
        assert "Distance band: Touching" in report.text_content() and "Cross-state: Yes" in report.text_content()
        assert "Possible saving (estimate): $62,000 to $264,000" in content
        assert_readable_report(report)
        assert report.locator(".coordination-status").evaluate_all("nodes => nodes.every(node => node.textContent === '')")
        pair_count = len(page.request.get(f"{live_server}/api/overlaps?band=touching&cross_state=true").json())
        assert report.locator("tbody tr").count() == pair_count
        page.emulate_media(media="print")
        expect(page.locator(".workspace")).not_to_be_visible()
        expect(report).to_be_visible()
        assert page.locator("html").evaluate("el => getComputedStyle(el).colorScheme") == "light"
        assert page.locator("body").evaluate("el => getComputedStyle(el).backgroundColor") == "rgb(255, 255, 255)"
        assert report.evaluate("el => getComputedStyle(el).color") == "rgb(0, 0, 0)"
        run = Path.home() / "dev" / "gridlock-runs" / "web-2-T1.7"
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
        open_more(page)
        control = page.get_by_role("button", name="Export CSV", exact=True)
        expect(control).to_be_enabled()
        page.route("**/api/export/overlaps.csv*", lambda route: route.fulfill(status=503, body="unavailable"))
        control.click()
        expect(page.locator("#export-status")).to_contain_text("Could not export CSV")
        expect(control).to_be_enabled()
        page.unroute("**/api/export/overlaps.csv*")
        with page.expect_download():
            control.click()
        open_more(page)
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
        close_more(page)
        first.locator("button").click()
        expect(page.locator("#overlap-content")).not_to_be_empty()
        page.route(f"**/api/overlaps/{pair_id}", lambda route: route.fulfill(status=503, body="unavailable"))
        open_more(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        expect(page.locator("#export-status")).to_contain_text("Could not prepare print report")
        assert page.evaluate("window.printCalls || 0") == 0
        page.unroute(f"**/api/overlaps/{pair_id}")
        open_more(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        page.route("**/api/overlaps?band=touching", lambda route: route.fulfill(status=503, body="unavailable"))
        page.locator("#filters-toggle").click()
        page.locator("#filter-band").select_option("touching")
        expect(page.get_by_test_id("error-state")).to_be_visible()
        open_more(page)
        expect(page.get_by_role("button", name="Export CSV", exact=True)).to_be_disabled()
        expect(page.get_by_role("button", name="Print report", exact=True)).to_be_disabled()
        browser.close()


def test_download_keeps_server_escaped_cells_and_print_treats_names_as_text(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        external = []
        page.on("request", lambda request: external.append(request.url)
                if urlsplit(request.url).netloc != urlsplit(live_server).netloc else None)
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
        close_more(page)
        first.locator("button").click()
        open_more(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        assert hostile in page.locator("#print-selected").text_content()
        assert page.locator("#print-report img, #print-report script").count() == 0
        assert page.evaluate("window.injected || 0") == 0
        raw = b"\xef\xbb\xbfRank,Project A,Distance km\r\n1,'=SUM(1),-1.5\r\n"
        page.route("**/api/export/overlaps.csv*", lambda route: route.fulfill(
            body=raw, content_type="text/csv", headers={"Content-Disposition": 'attachment; filename="gridlock-overlaps.csv"'}))
        with page.expect_download() as received:
            open_more(page)
            page.get_by_role("button", name="Export CSV", exact=True).click()
        assert Path(received.value.path()).read_bytes() == raw
        assert external == []
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
        close_more(page)
        first.locator("button").click()
        expect(page.locator("#overlap-content")).not_to_be_empty()
        page.evaluate("window.delayPrint = true")
        open_more(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => typeof window.releasePrint === 'function'")
        close_more(page)
        page.locator("#overlap-back").click()
        page.get_by_test_id("overlap-row").nth(1).locator("button").click()
        page.evaluate("window.releasePrint()")
        expect(page.locator("#export-status")).to_contain_text("Selection changed")
        assert page.evaluate("window.printCalls || 0") == 0
        open_more(page)
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
        open_more(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        content = page.locator("#print-selected").text_content()
        assert f'Overlap #{pair["rank"]}' in content and pair["band_label"] in content
        assert "Approximate locations" in content
        assert "possibly touching" not in content
        assert_readable_report(page.locator("#print-report"))
        browser.close()


@pytest.mark.parametrize("rank", [1, 3])
def test_print_readable_selected_and_full_ranked_evidence(live_server, rank):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.print = () => { window.printCalls = 1; }")
        pairs = page.request.get(f"{live_server}/api/overlaps").json()
        pair = pairs[rank - 1]
        payload = page.request.get(f'{live_server}/api/overlaps/{pair["id"]}').json()
        page.goto(f'{live_server}/#overlap={pair["id"]}')
        expect(page.locator("#overlap-detail-heading")).to_have_text(f"Overlap #{rank}")
        open_reports(page)
        open_more(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        report = page.locator("#print-report")
        assert_readable_report(report)
        rows = report.locator("tbody tr")
        assert rows.count() == len(pairs)
        assert rows.locator("td:first-child").all_text_contents() == [str(item["rank"]) for item in pairs]
        assert rows.locator('[data-src="distance_km"]').all_text_contents() == [f'{item["distance_km"]} km' for item in pairs]
        assert rows.locator('[data-src="band_label"]').all_text_contents() == [item["band_label"] for item in pairs]
        assert rows.locator(".coordination-status").evaluate_all("nodes => nodes.every(node => node.textContent === '')")
        features = page.request.get(f"{live_server}/api/projects").json()["features"]
        projects = {feature["properties"]["id"]: feature["properties"] for feature in features}
        assert rows.locator('[data-src="name"]').all_text_contents() == [projects[item[key]]["name"] for item in pairs for key in ("a", "b")]
        assert rows.locator('[data-src="utility"]').all_text_contents() == [
            projects[item[key]]["utility"] +
            (" (inferred)" if projects[item[key]]["utility_basis"] == "inferred_from_location" else "")
            for item in pairs for key in ("a", "b")]
        assert rows.locator('[data-src="source"]').all_text_contents() == [
            f'{projects[item[key]]["source"]["doc"]}, p. {projects[item[key]]["source"]["page"]}'
            for item in pairs for key in ("a", "b")]
        for key in ("project_a", "project_b"):
            props = payload[key]["properties"]
            selected = report.locator("#print-selected")
            assert props["name"] in selected.text_content()
            assert props["description"] in selected.text_content()
            assert props["utility"] in selected.text_content()
            assert selected.locator(f'a[href$="#page={props["source"]["page"]}"]').count() >= 1
        page.emulate_media(media="print")
        expect(report.locator('#print-selected [data-src="description"]').first).to_be_visible()
        expect(report.locator('#print-selected [data-src="savings_basis"]')).to_be_visible()
        browser.close()


def test_print_labels_all_filters_and_unknown_assumptions_without_codes(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.print = () => { window.printCalls = 1; }")
        pair_id = "desc-p41__sertp-p107-9bc088"
        payload = page.request.get(f"{live_server}/api/overlaps/{pair_id}").json()
        payload["savings"]["assumption_ids"].append("unknown_assumption_v9")
        page.route(f"**/api/overlaps/{pair_id}", lambda route: route.fulfill(json=payload))
        query = urlencode({"utility": "Dominion Energy SC", "voltage_kv": "230", "year_min": "2026",
                           "year_max": "2030", "project_type": "new_line", "band": "lt_40km", "cross_state": "false"})
        page.goto(f"{live_server}/?{query}#overlap={pair_id}")
        expect(page.locator("#overlap-detail-heading")).to_have_text("Overlap #1")
        open_reports(page)
        open_more(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        report = page.locator("#print-report")
        for label in ["Utility: Dominion Energy SC", "Voltage: 230 kV", "In service from: 2026",
                      "In service through: 2030", "Project type: New line", "Distance band: Under 40 km",
                      "Cross-state: No", "Assumption details unavailable"]:
            assert label in report.text_content()
        assert_readable_report(report)
        browser.close()


def test_print_follows_filtered_deep_link_and_history_and_clears_bad_links(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.print = () => { window.printCalls = (window.printCalls || 0) + 1; }")
        pair_ids = ["desc-p41__sertp-p107-9bc088", "desc-p41__sertp-p111-fe1e3b"]
        payloads = [page.request.get(f"{live_server}/api/overlaps/{pair_id}").json() for pair_id in pair_ids]
        page.goto(f"{live_server}/?band=lt_40km#overlap={pair_ids[0]}")
        open_reports(page)

        def check_pair(payload):
            expect(page.locator("#overlap-detail-heading")).to_have_text(f'Overlap #{payload["overlap"]["rank"]}')
            count = page.evaluate("window.printCalls || 0")
            open_more(page)
            page.get_by_role("button", name="Print report", exact=True).click()
            page.wait_for_function("count => window.printCalls === count + 1", arg=count)
            selected = page.locator("#print-selected")
            for key in ("project_a", "project_b"):
                assert payload[key]["properties"]["name"] in selected.text_content()
            assert "outside the current filters" in selected.text_content()
            assert_readable_report(page.locator("#print-report"))

        check_pair(payloads[0])
        page.evaluate("id => { location.hash = `overlap=${id}`; }", pair_ids[1])
        check_pair(payloads[1])
        page.go_back()
        check_pair(payloads[0])
        page.go_forward()
        check_pair(payloads[1])
        for bad, heading in [("invalid", "Unknown overlap link"), ("desc-p999__desc-p998", "Stale overlap link"),
                             (pair_ids[0], "Overlap detail unavailable")]:
            if bad == pair_ids[0]:
                page.route(f"**/api/overlaps/{bad}", lambda route: route.fulfill(status=503, body="unavailable"))
            page.evaluate("id => { location.hash = `overlap=${id}`; }", bad)
            expect(page.locator("#overlap-detail-heading")).to_have_text(heading)
            count = page.evaluate("window.printCalls")
            open_more(page)
            page.get_by_role("button", name="Print report", exact=True).click()
            page.wait_for_function("count => window.printCalls === count + 1", arg=count)
            expect(page.locator("#print-selected")).to_contain_text("No overlap selected")
            assert page.locator('#print-selected [data-src="name"]').count() == 0
        browser.close()


@pytest.mark.parametrize("status,reason", [("no_cost", "the plans do not size this pair, or these job types share nothing at this distance"),
                                         ("timing_too_far", "project timing is too far apart")])
def test_print_no_savings_remains_explicit_and_readable(live_server, status, reason):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.print = () => { window.printCalls = 1; }")
        pairs = page.request.get(f"{live_server}/api/overlaps").json()
        pair = next(item for item in pairs if item["savings"]["status"] == status)
        page.goto(f'{live_server}/#overlap={pair["id"]}')
        expect(page.locator("#overlap-detail-heading")).to_have_text(f'Overlap #{pair["rank"]}')
        open_reports(page)
        open_more(page)
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        expect(page.locator("#print-selected")).to_contain_text(f"No estimate: {reason}.")
        assert_readable_report(page.locator("#print-report"))
        browser.close()
