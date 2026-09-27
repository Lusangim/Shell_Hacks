"""Browser checks for the map and ranked-list shell."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from playwright.sync_api import expect, sync_playwright
from tests.harness import auxiliary_test_port, require_free_loopback_port


ROOT = Path(__file__).resolve().parents[2]
MALICIOUS_NAME = '<img src=x onerror="window.injected=true">'


def _project(index: int, *, located: bool = True, name: str | None = None) -> dict:
    project_id = f"desc-p{index}" if index % 2 else f"sertp-p{index}-abcdef"
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-81.8 + index * 0.08, 32.1 + index * 0.1]}
        if located else None,
        "properties": {
            "id": project_id,
            "utility": "Dominion Energy SC" if index % 2 else "Georgia Power",
            "utility_basis": "stated",
            "name": name or f"Test project {index}",
            "description": f"Test description {index}",
            "in_service": "2028",
            "year": 2028,
            "voltage_kv": [230],
            "accuracy": "exact" if index % 3 else "approximate",
            "location_source": "Test location source" if located else None,
            "source": {"doc": "Synthetic test plan", "page": index, "url": "/test-plan.pdf"},
        },
    }


PROJECTS = [_project(index, name=MALICIOUS_NAME if index == 1 else None) for index in range(1, 13)]
PROJECTS.append(_project(13, located=False))
OVERLAPS = [
    {
        "id": f"{PROJECTS[index - 1]['properties']['id']}__{PROJECTS[index]['properties']['id']}",
        "a": PROJECTS[index - 1]["properties"]["id"],
        "b": PROJECTS[index]["properties"]["id"],
        "rank": index,
        "band": "lt_8km",
        "band_label": "Under 8 km",
        "distance_km": 2.5,
        "a_year": 2028,
        "b_year": 2028,
        "accuracy_pair": "approximate" if index % 3 == 0 else "exact",
    }
    for index in range(1, 12)
]
BASEMAP = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Georgia", "kind": "state"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[-82.5, 31.4], [-81.2, 31.4], [-81.2, 33], [-82.5, 33], [-82.5, 31.4]]],
            },
        },
        {
            "type": "Feature",
            "properties": {"name": "Savannah city", "kind": "city_label", "state": "GA"},
            "geometry": {"type": "Point", "coordinates": [-81.196492, 32.018043]},
        },
    ],
}


@pytest.fixture(scope="module")
def shell_server():
    port = auxiliary_test_port(1000)
    require_free_loopback_port(port)
    responses = {
        "/api/projects": {"type": "FeatureCollection", "features": PROJECTS},
        "/api/overlaps": OVERLAPS,
        "/api/meta": {
            "source_documents": [
                {"doc": "Synthetic test plan", "date": "2025-01-01", "url": "/test-plan.pdf"}
            ],
            "no_overlap_count": 1,
            "stage_counts": {"kept": len(PROJECTS), "placed": len(PROJECTS) - 1, "overlaps": len(OVERLAPS)},
            "unmapped_count": 1,
        },
        "/api/basemap": BASEMAP,
        "/api/map-config": {"google_enabled": False, "google_key": None, "offline_available": False},
    }

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT), **kwargs)

        def end_headers(self):
            self.send_header("Content-Security-Policy", "default-src 'self'")
            super().end_headers()

        def do_GET(self):  # noqa: N802
            route = self.path.split("?", 1)[0]
            if route == "/":
                self.path = "/web/index.html"
            if route in responses:
                body = json.dumps(responses[route]).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            super().do_GET()

        def log_message(self, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_shell_server_reused_within_module():
    """Avoid repeated Windows binds for the same shell test module."""
    assert shell_server._fixture_function_marker.scope == "module"


def test_shell_server_exposes_offline_map_config(shell_server):
    with urlopen(f"{shell_server}/api/map-config", timeout=2) as response:
        assert response.status == 200
        assert json.load(response) == {
            "google_enabled": False,
            "google_key": None,
            "offline_available": False,
        }


@pytest.fixture
def api_shell_server(tmp_path):
    fixture_dir = ROOT / "tests" / "fixtures" / "api"
    for name in ("projects.json", "overlaps.json", "meta.json", "basemap.json"):
        shutil.copyfile(fixture_dir / name, tmp_path / name)
    port = auxiliary_test_port(2000)
    require_free_loopback_port(port)
    env = os.environ.copy()
    env["GRIDLOCK_ARTIFACT_DIR"] = str(tmp_path)
    env["GRIDLOCK_AI"] = "off"
    env["GRIDLOCK_TEST_PORT"] = str(port)
    process = subprocess.Popen(
        [os.environ["GRIDLOCK_PY"], "-m", "server"],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 15
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"API server exited with code {process.returncode}")
            try:
                with urlopen(f"{url}/api/health", timeout=0.5) as response:
                    if response.status == 200:
                        yield url
                        return
            except (URLError, TimeoutError):
                pass
            time.sleep(0.05)
        raise RuntimeError("API server did not start")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_shell_loads_from_the_real_api_factory(api_shell_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.goto(api_shell_server)
        projects = page.request.get(f"{api_shell_server}/api/projects").json()
        overlaps = page.request.get(f"{api_shell_server}/api/overlaps").json()
        expect(page.get_by_test_id("project-feature")).to_have_count(
            sum(project["geometry"] is not None for project in projects["features"])
        )
        expect(page.get_by_test_id("overlap-row")).to_have_count(len(overlaps))
        expect(page.get_by_role("status").first).to_contain_text("ranked opportunities loaded")
        assert errors == []
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_shell_renders_all_placed_projects_and_ranked_rows_without_console_errors(shell_server, width, height):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        errors = []
        external_requests = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        page.on("request", lambda request: external_requests.append(request.url) if not request.url.startswith(shell_server) else None)
        page.goto(shell_server)
        api_projects = page.request.get(f"{shell_server}/api/projects").json()
        api_overlaps = page.request.get(f"{shell_server}/api/overlaps").json()
        api_basemap = page.request.get(f"{shell_server}/api/basemap").json()
        expect(page.get_by_test_id("project-feature")).to_have_count(
            sum(project["geometry"] is not None for project in api_projects["features"])
        )
        expect(page.get_by_test_id("project-casing")).to_have_count(
            sum(project["geometry"] is not None for project in api_projects["features"])
        )
        expect(page.get_by_test_id("basemap-feature")).to_have_count(len(api_basemap["features"]))
        expect(page.get_by_test_id("overlap-row")).to_have_count(len(api_overlaps))
        assert len(api_overlaps) >= 10
        expect(page.get_by_text("Location unknown (1)")).to_be_visible()
        expect(page.locator("#editions")).to_contain_text("2025-01-01")
        expect(page.get_by_test_id("overlap-row").first.locator('[data-src="source"]')).to_have_count(2)
        assert errors == []
        assert external_requests == []
        if width == 390:
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
            expect(page.get_by_test_id("bottom-sheet")).to_be_visible()
            sheet_layout = page.evaluate("""() => ({
              rowBottom: document.querySelectorAll('[data-testid="overlap-row"]')[1].getBoundingClientRect().bottom,
              viewportBottom: window.innerHeight,
              panelTop: document.querySelector('.panel').getBoundingClientRect().top
            })""")
            assert sheet_layout["rowBottom"] <= sheet_layout["viewportBottom"], sheet_layout
        browser.close()


def test_malicious_project_name_is_text_in_list_and_map_tooltip(shell_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(shell_server)
        name = page.get_by_test_id("overlap-row").first.locator('[data-src="name"]').first
        expect(name).to_have_text(MALICIOUS_NAME)
        page.get_by_test_id("project-feature").first.hover()
        tooltip = page.locator(".leaflet-tooltip")
        expect(tooltip).to_contain_text(MALICIOUS_NAME)
        expect(tooltip).to_contain_text("Synthetic test plan, p. 1")
        assert page.locator("img[src='x']").count() == 0
        assert page.evaluate("window.injected === undefined")
        browser.close()


def test_map_project_click_selects_a_ranked_overlap(shell_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(shell_server)
        expect(page.get_by_test_id("project-feature")).to_have_count(12)
        page.get_by_test_id("project-feature").first.click()
        expect(page.get_by_test_id("overlap-row").first.locator("button")).to_have_attribute("aria-pressed", "true")
        expect(page.locator('[data-testid="project-feature"][data-selected="true"]')).to_have_count(2)
        expect(page.get_by_role("status").first).to_have_attribute("data-src", "utility")
        browser.close()


def test_accuracy_is_encoded_in_line_style_and_unknowns_stay_unmapped(shell_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(shell_server)
        expect(page.get_by_test_id("project-feature")).to_have_count(12)
        exact = page.locator('[data-project-id="desc-p1"]')
        approximate = page.locator('[data-project-id="desc-p3"]')
        # These fixture projects are single sites: an exact site is a filled dot and an approximate
        # site a hollow ring (a dash barely showed on a small filled dot). Dashed approximate lines
        # are checked on real routes in test_location_look.py.
        assert exact.get_attribute("stroke-dasharray") is None
        expect(exact).to_have_attribute("fill-opacity", "1")
        expect(approximate).to_have_attribute("fill-opacity", "0")
        expect(approximate).to_have_attribute("data-look", "approximate")
        assert page.locator('[data-project-id="desc-p13"]').count() == 0
        expect(page.get_by_text("Location unknown (1)")).to_be_visible()
        browser.close()


def test_svg_project_paths_use_the_ranked_list_for_accessibility(shell_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(shell_server)
        paths = page.get_by_test_id("project-feature")
        expect(paths).to_have_count(12)
        expect(page.get_by_test_id("overlap-row")).to_have_count(11)
        assert page.evaluate("""() => Array.from(document.querySelectorAll('[data-testid="project-feature"]'))
          .every(path => !path.hasAttribute('aria-label') && path.getAttribute('tabindex') === '-1')""")
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_tab_traversal_skips_map_paths_and_marks_map_focus(shell_server, width, height):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(shell_server)
        expect(page.get_by_test_id("project-feature")).to_have_count(12)
        map_outline_unfocused = page.locator("#map").evaluate("element => getComputedStyle(element).outline")
        focus_stops = []
        for _ in range(24):
            page.keyboard.press("Tab")
            focus_stops.append(page.evaluate("""() => ({
              tag: document.activeElement.tagName.toLowerCase(),
              id: document.activeElement.id,
              classes: document.activeElement.getAttribute('class') || '',
              outline: getComputedStyle(document.activeElement).outline
            })"""))
        assert not any(stop["tag"] == "path" for stop in focus_stops), focus_stops
        map_stops = [stop for stop in focus_stops if stop["id"] == "map"]
        assert map_stops and map_stops[0]["outline"] != map_outline_unfocused, focus_stops
        assert any("overlap-button" in stop["classes"] for stop in focus_stops), focus_stops
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_basemap_city_is_text_without_stock_marker_or_tab_stop(shell_server, width, height):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(shell_server)
        expect(page.get_by_test_id("basemap-feature")).to_have_count(2)
        expect(page.get_by_test_id("city-label")).to_have_text("Savannah city")
        assert page.locator("img.leaflet-marker-icon").count() == 0
        for _ in range(20):
            page.keyboard.press("Tab")
            assert page.evaluate("document.activeElement.tagName.toLowerCase()") != "img"
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 900), (390, 844)])
def test_full_basemap_keeps_city_labels_sparse(shell_server, width, height):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        basemap = (ROOT / "data" / "build" / "basemap.json").read_text(encoding="utf-8")
        page.route("**/api/basemap", lambda route: route.fulfill(status=200, content_type="application/json", body=basemap))
        page.goto(shell_server)
        expect(page.get_by_test_id("project-feature")).to_have_count(12)
        expect(page.locator('path[data-testid="basemap-feature"]')).to_have_count(2)
        visible_labels = page.locator('[data-testid="city-label"]:visible')
        assert 1 <= visible_labels.count() <= 14
        names = visible_labels.all_text_contents()
        assert "Savannah city" in names and "North Augusta city" in names
        assert page.evaluate("""() => {
          const boxes = Array.from(document.querySelectorAll('.city-label-visible'))
            .map(label => label.getBoundingClientRect());
          return boxes.every((a, i) => boxes.slice(i + 1).every(b =>
            a.right <= b.left || b.right <= a.left || a.bottom <= b.top || b.bottom <= a.top));
        }""")
        assert page.locator("img.leaflet-marker-icon").count() == 0
        browser.close()


def test_first_map_view_contains_savannah_and_augusta(shell_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        basemap = (ROOT / "data" / "build" / "basemap.json").read_text(encoding="utf-8")
        page.route("**/api/basemap", lambda route: route.fulfill(status=200, content_type="application/json", body=basemap))
        page.goto(shell_server)
        expect(page.get_by_test_id("project-feature")).to_have_count(12)
        assert page.evaluate("""async () => {
          const { state } = await import('/web/js/state.js');
          const bounds = state.map.getBounds();
          return bounds.contains([32.08, -81.10]) && bounds.contains([33.47, -81.97]);
        }""")
        browser.close()


def test_dark_theme_is_set_before_styles_and_recolors_map(shell_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.add_init_script("localStorage.setItem('gridlock-theme', 'dark')")
        page.goto(shell_server)
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")
        expect(page.get_by_test_id("project-feature")).to_have_count(12)
        assert page.evaluate("""() => {
          const css = getComputedStyle(document.documentElement);
          return document.querySelector('[data-testid="project-feature"]').getAttribute('stroke')
            === css.getPropertyValue('--dominion').trim();
        }""")
        page.get_by_role("button", name="Switch to light theme").click()
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        assert page.evaluate("""() => {
          const css = getComputedStyle(document.documentElement);
          return document.querySelector('[data-testid="project-feature"]').getAttribute('stroke')
            === css.getPropertyValue('--dominion').trim();
        }""")
        browser.close()


def test_theme_toggle_works_when_storage_is_disabled(shell_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(color_scheme="light")
        page.add_init_script("""Storage.prototype.getItem = () => { throw new Error('storage disabled'); };
          Storage.prototype.setItem = () => { throw new Error('storage disabled'); };""")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(shell_server)
        expect(page.get_by_test_id("overlap-row")).to_have_count(11)
        page.get_by_role("button", name="Switch to dark theme").click()
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")
        expect(page.get_by_role("status").first).to_contain_text("Theme preference will reset on reload")
        assert errors == []
        browser.close()


def test_shell_has_loading_empty_and_error_recovery(shell_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.route("**/api/overlaps", lambda route: route.fulfill(status=200, content_type="application/json", body="[]"))
        page.goto(shell_server)
        expect(page.get_by_test_id("empty-state")).to_be_visible()
        page.unroute("**/api/overlaps")
        page.route("**/api/overlaps", lambda route: route.fulfill(status=503, content_type="application/json", body='{"error":{"code":"unavailable","message":"Unavailable"}}'))
        page.reload()
        expect(page.get_by_test_id("error-state")).to_be_visible()
        expect(page.get_by_role("button", name="Try again")).to_be_visible()
        browser.close()
