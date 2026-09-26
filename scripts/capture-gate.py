"""Capture the current local demo at desktop and phone sizes."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.harness import require_free_loopback_port, required_test_port


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    port = required_test_port()
    require_free_loopback_port(port)
    args.output.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["GRIDLOCK_AI"] = "off"
    process = subprocess.Popen(
        [sys.executable, "-m", "server"],
        cwd=Path.cwd(),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"server exited with code {process.returncode}")
            try:
                with urlopen(f"{url}/api/health", timeout=0.5) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError):
                time.sleep(0.05)
        else:
            raise RuntimeError("server health timeout")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for width, height, name in (
                (1440, 900, "desktop-1440.png"),
                (390, 844, "phone-390.png"),
            ):
                page = browser.new_page(
                    viewport={"width": width, "height": height}, device_scale_factor=1
                )
                page.goto(url)
                page.get_by_test_id("overlap-row").first.wait_for()
                page.wait_for_function(
                    "document.querySelectorAll('[data-testid=project-feature]').length === 181"
                )
                page.screenshot(path=str(args.output / name), full_page=False)
                print(
                    f"{name}: rows={page.get_by_test_id('overlap-row').count()}, "
                    f"projects={page.get_by_test_id('project-feature').count()}"
                )
                page.close()
            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    main()
