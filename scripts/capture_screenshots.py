"""Capture the screenshots in docs/screenshots/ and the sample report, from a local GridLock server.

Usage (from the repository root, with the SETUP virtual environment and the test browser installed):
    python scripts/capture_screenshots.py [--port 8853] [--out docs/screenshots] [--google]

It starts its own server on a test port with AI briefs off, drives the page with Playwright's Chromium and
saves one PNG per feature, plus docs/sample-report.pdf (the Letter print report for the touching pairs).
--google also captures the Satellite view; it needs the runner's own Maps key and internet access.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import Page, expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def start_server(port: int, google: bool) -> subprocess.Popen:
    env = os.environ.copy()
    env.update(GRIDLOCK_AI="off", GRIDLOCK_GOOGLE="on" if google else "off", GRIDLOCK_TEST_PORT=str(port),
               PYTHONPATH=str(ROOT))
    server = subprocess.Popen([sys.executable, "-m", "server"], cwd=ROOT, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"server exited with code {server.returncode}")
        try:
            with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=0.5):
                return server
        except OSError:
            time.sleep(0.25)
    server.terminate()
    raise RuntimeError("server did not start")


class Shooter:
    def __init__(self, browser, url: str, out: Path):
        self.browser, self.url, self.out = browser, url, out
        self.top = None

    def page(self, width=1440, height=900, theme="light", path="", dismiss=True) -> Page:
        page = self.browser.new_page(viewport={"width": width, "height": height}, color_scheme=theme)
        page.add_init_script(f"localStorage.setItem('gridlock-theme', '{theme}')")
        page.goto(f"{self.url}/{path}")
        expect(page.locator(".overlap-button").first).to_be_visible(timeout=20000)
        page.evaluate("async () => { window.__gl = (await import('/web/js/state.js')).state; }")
        page.wait_for_function("window.__gl.initialMapFitted && !window.__gl.map._animatingZoom", timeout=20000)
        dismiss_button = page.get_by_role("button", name="Dismiss tour invitation")
        if dismiss and dismiss_button.is_visible():
            dismiss_button.click()
        self.settle(page)
        return page

    @staticmethod
    def settle(page: Page, ms: int = 1200) -> None:
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(ms)

    def save(self, page: Page, name: str) -> None:
        self.settle(page, 600)
        page.screenshot(path=str(self.out / f"{name}.png"))
        print("saved", name)

    def open_top_pair(self, page: Page) -> None:
        page.get_by_test_id("overlap-row").first.locator("button").click()
        expect(page.locator("#overlap-content .score-detail")).to_be_visible()
        expect(page.locator("#brief-copy")).to_be_enabled(timeout=15000)

    def reveal(self, page: Page, selector: str, open_details: bool = True) -> None:
        block = page.locator(selector).first
        if open_details:
            block.evaluate("el => el.querySelectorAll('details').forEach(d => d.open = true)")
        block.evaluate("el => el.scrollIntoView({block: 'start'})")

    def search(self, page: Page, place: str) -> None:
        box = page.locator("#search-input")
        box.fill(place)
        expect(page.locator("#search-options option")).not_to_have_count(0)
        box.press("Enter")
        expect(page.get_by_test_id("search-selection")).to_contain_text(place)

    def zoom_to(self, page: Page, project_id: str) -> None:
        page.evaluate("""async (id) => {
          const features = (await (await fetch('/api/projects')).json()).features;
          const feature = features.find(f => f.properties.id === id);
          window.__gl.map.fitBounds(L.geoJSON(feature).getBounds(), {padding: [140, 140], maxZoom: 12});
        }""", project_id)
        page.wait_for_function("!window.__gl.map._animatingZoom")
        page.evaluate("id => document.dispatchEvent(new CustomEvent('gridlock:project-click', {detail: {projectId: id}}))",
                      project_id)
        expect(page.locator("#project-detail")).to_be_visible()


def capture(shooter: Shooter, google: bool) -> None:
    s = shooter
    api = s.browser.new_page()
    pairs = api.request.get(f"{s.url}/api/overlaps").json()
    projects = api.request.get(f"{s.url}/api/projects").json()["features"]
    api.close()
    top = pairs[0]["id"]

    page = s.page()
    s.save(page, "01-overview")
    page.close()

    page = s.page(dismiss=False)
    page.locator("#tour-launch").click()
    for _ in range(2):
        page.get_by_role("button", name="Next", exact=True).click()
    expect(page.locator("#tour-body")).to_contain_text("Score =")
    s.save(page, "02-tour-ranking")
    page.close()

    page = s.page()
    s.search(page, "Savannah")
    s.save(page, "03-search-savannah")
    s.open_top_pair(page)
    s.save(page, "04-top-pair")
    s.reveal(page, "#overlap-content .overlap-projects", open_details=False)
    s.save(page, "05-sources")
    s.reveal(page, "#overlap-content .savings-detail")
    s.save(page, "06-savings")
    s.reveal(page, "#overlap-content .score-detail")
    s.save(page, "07-score")
    s.reveal(page, "#brief-panel", open_details=False)
    s.save(page, "08-brief")
    page.close()

    page = s.page()
    year = page.locator("#timeline-year")
    expect(year).to_be_enabled()
    year.fill("2028")
    year.dispatch_event("input")
    s.save(page, "09-timeline-2028")
    page.close()

    page = s.page()
    page.locator("#filters-toggle").click()
    before = page.locator("#overlap-count").text_content()
    page.locator("#filter-band").select_option("touching")
    expect(page.locator("#overlap-count")).not_to_have_text(before)
    s.save(page, "10-filters")
    page.close()

    page = s.page()
    s.search(page, "Savannah")
    page.locator("#search-input").press("Tab")
    expect(page.locator("#explore-area")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.locator("#area-panel")).to_be_visible()
    expect(page.locator("#area-projects li").first).to_be_attached(timeout=15000)
    s.save(page, "11-explore-area")
    page.close()

    routed = next(f for f in projects if (f.get("geometry") or {}).get("type") == "MultiLineString")
    page = s.page()
    s.zoom_to(page, routed["properties"]["id"])
    s.save(page, "12-route-along-existing-lines")
    page.close()

    town = next((f for f in projects if f["properties"].get("town_only")), None)
    if town:
        page = s.page()
        s.zoom_to(page, town["properties"]["id"])
        s.save(page, "13-town-only-location")
        page.close()

    page = s.page()
    page.locator(".legend summary").click()
    s.save(page, "14-legend-and-reports")
    page.close()

    page = s.page(theme="dark", path=f"#overlap={top}")
    expect(page.locator("#overlap-content .score-detail")).to_be_visible()
    s.save(page, "15-dark-theme")
    page.close()

    page = s.page(width=390, height=844)
    s.save(page, "16-phone-list")
    page.close()
    page = s.page(width=390, height=844, path=f"#overlap={top}")
    expect(page.locator("#overlap-content .score-detail")).to_be_visible()
    s.save(page, "17-phone-pair")
    page.close()

    page = s.page(path=f"?band=touching#overlap={top}")
    expect(page.locator("#overlap-content .score-detail")).to_be_visible()
    page.evaluate("window.print = () => { window.__printed = true; }")
    page.locator(".legend summary").click()
    page.get_by_role("button", name="Print report", exact=True).click()
    page.wait_for_function("window.__printed === true")
    page.emulate_media(media="print")
    page.set_viewport_size({"width": 816, "height": 1056})
    s.save(page, "18-print-report")
    page.pdf(path=str(s.out.parent / "sample-report.pdf"), format="Letter", print_background=True)
    print("saved sample-report.pdf")
    page.close()

    page = s.page()
    expect(page.locator("#start-here button").first).to_be_visible()
    page.locator("#start-here").evaluate("el => el.scrollIntoView({block: 'center'})")
    s.save(page, "19-start-here-and-impact")
    page.locator("#area-mode-toggle").click()
    expect(page.locator("#area-mode-toggle")).to_have_attribute("aria-pressed", "true")
    s.save(page, "20-area-tool")
    page.close()

    page = s.page(path=f"#overlap={top}")
    expect(page.locator("#pair-tracker")).to_be_visible()
    page.locator("#tracker-status").select_option("Contacted")
    page.locator("#tracker-notes").fill("Example: ask Dominion Energy SC where the Deerfield switching station will be.")
    page.locator("#pair-tracker").evaluate("el => el.scrollIntoView({block: 'center'})")
    s.save(page, "21-coordination-tracker")
    page.close()

    if google:
        page = s.page(path=f"#overlap={top}")
        page.get_by_role("button", name="Satellite", exact=True).click()
        expect(page.locator(".basemap-status")).to_contain_text("Satellite", timeout=20000)
        s.settle(page, 3000)
        s.save(page, "22-google-satellite")
        page.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8853)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "screenshots")
    parser.add_argument("--google", action="store_true")
    args = parser.parse_args()
    if args.port == 8765:
        parser.error("use a test port, not the demo port 8765")
    args.out.mkdir(parents=True, exist_ok=True)
    server = start_server(args.port, args.google)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                capture(Shooter(browser, f"http://127.0.0.1:{args.port}", args.out), args.google)
            finally:
                browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == "__main__":
    main()
