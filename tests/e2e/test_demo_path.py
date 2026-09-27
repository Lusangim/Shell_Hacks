"""G2 core demo path through local search, evidence, source PDF and export."""

from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

from tests.e2e.ui_helpers import open_more


def test_search_pair_detail_sources_and_export_stay_connected(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        errors, external = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("request", lambda request: external.append(request.url)
                if urlsplit(request.url).netloc != urlsplit(live_server).netloc else None)

        page.goto(live_server)
        expect(page.get_by_test_id("overlap-row").first).to_be_visible()
        search = page.locator("#search-input")
        search.fill("Savannah")
        expect(page.locator("#search-options option")).not_to_have_count(0)
        search.press("Enter")
        expect(page.get_by_test_id("search-selection")).to_contain_text("Savannah city")

        expected_pair = page.request.get(f"{live_server}/api/overlaps").json()[0]
        first = page.get_by_test_id("overlap-row").first
        assert first.get_attribute("data-overlap-id") == expected_pair["id"]
        first.locator("button").click()
        detail = page.get_by_test_id("overlap-detail")
        expect(detail).to_be_visible()
        expect(detail).to_contain_text("unverified")
        source_links = detail.get_by_role("link")
        expect(source_links).to_have_count(2)
        for link in source_links.all():
            href = link.get_attribute("href")
            assert href and href.startswith("/api/sources/") and "#page=" in href
            response = page.request.get(f"{live_server}{href.split('#', 1)[0]}")
            assert response.status == 200
            assert response.headers["content-type"].startswith("application/pdf")

        open_more(page)
        page.locator(".legend summary").click()
        with page.expect_download() as received:
            open_more(page)
            page.get_by_role("button", name="Export CSV", exact=True).click()
        download = received.value
        assert download.suggested_filename == "gridlock-overlaps.csv"
        raw = Path(download.path()).read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf")
        assert raw == page.request.get(f"{live_server}/api/export/overlaps.csv").body()
        assert errors == [] and external == []
        browser.close()
