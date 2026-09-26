"""Isolated e2e server; never attaches to the founder's demo process."""

import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from tests.harness import require_free_loopback_port, required_test_port


ROOT = Path(__file__).resolve().parents[1]


def pytest_configure(config):
    """Keep each lane's temporary tests inside its writable run folder."""
    port = required_test_port()
    run_root = Path.home() / "dev" / "gridlock-runs" / "pytest"
    run_root.mkdir(parents=True, exist_ok=True)
    base = run_root / f"port-{port}"
    if base.parent.resolve() != run_root.resolve():
        raise RuntimeError("pytest temporary path escaped the run root")
    config.option.basetemp = str(base)


@pytest.fixture(scope="session")
def live_server():
    port = required_test_port()
    require_free_loopback_port(port)
    root = Path(os.environ.get("GRIDLOCK_TEST_ROOT", ROOT)).resolve()
    env = os.environ.copy()
    env["GRIDLOCK_AI"] = "off"
    guard = ROOT / "tests" / "e2e" / "guard"
    env["PYTHONPATH"] = os.pathsep.join((str(guard), str(root)))
    process = subprocess.Popen(
        [sys.executable, "-m", "server"],
        cwd=root,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 15
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"test server exited with code {process.returncode}")
            try:
                with urlopen(f"{url}/api/health", timeout=0.5) as response:
                    if response.status == 200:
                        yield url
                        return
            except (URLError, TimeoutError):
                pass
            time.sleep(0.05)
        raise RuntimeError(f"test server did not start on port {port}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
