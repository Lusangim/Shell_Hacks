"""Browser-only coordination notes follow pairs into list, print and CSV."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright


AXE = (Path(__file__).parent / "vendor" / "axe.min.js").read_text(encoding="utf-8")


def first_pair(page):
    row = page.get_by_test_id("overlap-row").first
    expect(row).to_be_visible()
    return row.get_attribute("data-overlap-id")


def open_pair(page, pair_id):
    page.locator(f'[data-overlap-id="{pair_id}"] button').click()
    expect(page.locator("#pair-tracker")).to_be_visible()


def set_tracking(page, status="Contacted", note="Call the planning team."):
    page.get_by_label("Coordination status", exact=True).select_option(status)
    page.get_by_label("Notes", exact=True).fill(note)
    expect(page.locator("#tracker-save-state")).to_have_text("Saved")


def csv_rows(raw):
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))


def download_csv(page):
    page.locator(".legend summary").click()
    with page.expect_download() as received:
        page.get_by_role("button", name="Export CSV", exact=True).click()
    return Path(received.value.path()).read_bytes()


def test_status_note_persist_chip_and_default_removes_entry(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        pair_id = first_pair(page)
        open_pair(page, pair_id)
        set_tracking(page)
        page.reload()
        expect(page.locator("#pair-tracker")).to_be_visible()
        expect(page.get_by_label("Coordination status", exact=True)).to_have_value("Contacted")
        expect(page.get_by_label("Notes", exact=True)).to_have_value("Call the planning team.")
        page.get_by_role("button", name="Back to ranked overlaps").click()
        expect(page.locator(f'[data-overlap-id="{pair_id}"] .tracker-chip')).to_have_text("Contacted")
        open_pair(page, pair_id)
        page.get_by_label("Coordination status", exact=True).select_option("Not started")
        expect(page.locator("#tracker-save-state")).to_have_text("Saved")
        assert page.evaluate("id => !Object.hasOwn(JSON.parse(localStorage.getItem('gridlock-tracker-v1')), id)", pair_id)
        page.get_by_role("button", name="Back to ranked overlaps").click()
        expect(page.locator(f'[data-overlap-id="{pair_id}"] .tracker-chip')).to_have_count(0)
        browser.close()


def test_print_report_fills_selected_and_ranked_status(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("window.print = () => { window.printCalls = (window.printCalls || 0) + 1; }")
        page.goto(live_server)
        pair_id = first_pair(page)
        open_pair(page, pair_id)
        set_tracking(page)
        page.locator(".legend summary").click()
        page.get_by_role("button", name="Print report", exact=True).click()
        page.wait_for_function("() => window.printCalls === 1")
        expect(page.locator("#print-selected .coordination-status")).to_contain_text("Contacted")
        expect(page.locator("#print-selected .coordination-status")).to_contain_text("Call the planning team.")
        rank = page.locator("#print-report tbody tr").first.locator(".coordination-status")
        expect(rank).to_contain_text("Contacted")
        expect(rank).to_contain_text("Call the planning team.")
        expect(page.locator("#print-report tbody tr").nth(1).locator(".coordination-status")).to_be_empty()
        browser.close()


@pytest.mark.parametrize("note,expected", [("Call, then meet.\r\nBring plans.", "Call, then meet.\nBring plans."),
                                            ("=SUM(1,1)", "'=SUM(1,1)")])
def test_csv_changes_only_tracked_cells_and_escapes_formula(live_server, note, expected):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        pair_id = first_pair(page)
        open_pair(page, pair_id)
        set_tracking(page, note=note)
        server = page.request.get(f"{live_server}/api/export/overlaps.csv").body()
        actual = download_csv(page)
        before, after = csv_rows(server), csv_rows(actual)
        assert len(before) == len(after)
        for original, changed in zip(before, after):
            assert original.keys() == changed.keys()
            for key in original:
                if original["Overlap ID"] == pair_id and key in ("Coordination status", "Notes"):
                    assert changed[key] == ("Contacted" if key == "Coordination status" else expected)
                else:
                    assert changed[key] == original[key]
        assert actual.startswith(b"\xef\xbb\xbf")
        assert b"\r\n" in actual
        browser.close()


def test_untracked_csv_keeps_server_bytes(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(live_server)
        first_pair(page)
        server = page.request.get(f"{live_server}/api/export/overlaps.csv").body()
        assert download_csv(page) == server
        browser.close()


def test_storage_disabled_keeps_detail_and_list_working(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.add_init_script("""Object.defineProperty(window, 'localStorage', {
          get() { throw new DOMException('blocked', 'SecurityError'); }
        });""")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.goto(live_server)
        pair_id = first_pair(page)
        open_pair(page, pair_id)
        expect(page.locator("#pair-tracker")).to_contain_text("Tracking needs browser storage, which is off in this browser")
        expect(page.locator("#overlap-content")).not_to_be_empty()
        page.get_by_role("button", name="Back to ranked overlaps").click()
        expect(page.locator(f'[data-overlap-id="{pair_id}"]')).to_be_visible()
        assert errors == []
        browser.close()


@pytest.mark.parametrize("width,height,theme", [(1440, 900, "light"), (1440, 900, "dark"),
                                                 (390, 844, "light"), (390, 844, "dark")])
def test_widget_axe_and_keyboard_status(live_server, width, height, theme):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        page.goto(live_server)
        pair_id = first_pair(page)
        open_pair(page, pair_id)
        violations = page.evaluate(AXE + "\nwindow.axe.run(document, {runOnly: {type:'tag', values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}})")["violations"]
        assert [(item["id"], item["nodes"][0]["target"]) for item in violations] == []
        select = page.get_by_label("Coordination status", exact=True)
        select.focus()
        page.keyboard.press("c")
        page.keyboard.press("Tab")
        expect(select).to_have_value("Contacted")
        expect(page.locator("#tracker-save-state")).to_have_text("Saved")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
        if width == 390:
            assert select.evaluate("node => node.getBoundingClientRect().height") >= 44
            assert page.get_by_label("Notes", exact=True).evaluate("node => node.getBoundingClientRect().height") >= 44
        browser.close()
