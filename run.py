#!/usr/bin/env python3
"""Set up (once) and start GridLock with Python alone, on Windows, macOS or Linux.

    python run.py               set up if needed, then start GridLock and open http://127.0.0.1:8765
    python run.py --no-map      skip the optional street map download (the app shows its outline map)
    python run.py --setup-only  set up without starting
    python run.py --no-browser  do not open a browser
    python run.py --port 8780   use another port (Google Maps works only on 8765)
    python run.py --google      also offer Google Maps and Satellite (needs your own key; see RUNNING.md)

On macOS and Linux use `python3 run.py`; on Windows `py run.py` also works. It needs Python 3.12 and, the
first time, internet access to install the pinned packages. It uses the same environment as SETUP and
START (~/dev/gridlock-venv, or GRIDLOCK_VENV), so either way of starting works afterwards.
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = Path(os.environ.get("GRIDLOCK_VENV") or Path.home() / "dev" / "gridlock-venv")
APP_MODULES = "import fastapi, uvicorn, pydantic, numpy, shapely, pyproj, pypdf"


def venv_python() -> Path | None:
    for candidate in (VENV / "Scripts" / "python.exe", VENV / "bin" / "python"):
        if candidate.exists():
            return candidate
    return None


def find_python312() -> list[str] | None:
    """This interpreter if it is 3.12, otherwise a Python 3.12 on the PATH (or the Windows py launcher)."""
    if sys.version_info[:2] == (3, 12):
        return [sys.executable]
    candidates = [["py", "-3.12"]] if os.name == "nt" else []
    candidates += [["python3.12"], ["python3"], ["python"]]
    for command in candidates:
        executable = shutil.which(command[0])
        if not executable:
            continue
        try:
            probe = subprocess.run([executable, *command[1:], "-c", "import sys; print(sys.version_info[:2] == (3, 12))"],
                                   capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.stdout.strip() == "True":
            return [executable, *command[1:]]
    return None


def run(command: list[str], **kwargs) -> int:
    return subprocess.run(command, cwd=ROOT, **kwargs).returncode


def setup(no_map: bool) -> Path:
    python = venv_python()
    if python is None:
        base = find_python312()
        if base is None:
            print("GridLock needs Python 3.12.")
            print("  Windows: install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH')")
            print("  macOS:   install it from https://www.python.org/downloads/ (or: brew install python@3.12)")
            print("  Linux:   sudo apt install python3.12 python3.12-venv (or your distribution's Python 3.12)")
            print("Then run this again.")
            sys.exit(3)
        print(f"Creating GridLock's Python 3.12 environment in {VENV} ...")
        VENV.parent.mkdir(parents=True, exist_ok=True)
        if run([*base, "-m", "venv", str(VENV)]) != 0 or venv_python() is None:
            print("Could not create the Python environment. On Linux, install python3.12-venv and run this again.")
            sys.exit(3)
        python = venv_python()
        print("Installing the pinned packages (the first time only; a few minutes) ...")
        if run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "--requirement",
                str(ROOT / "requirements.txt")]) != 0:
            print(f"The package install did not finish. Check the internet connection, delete {VENV} and run this again.")
            sys.exit(3)
    if run([str(python), "-c", APP_MODULES]) != 0:
        print(f"GridLock's Python environment is incomplete; delete {VENV} and run this again.")
        sys.exit(3)
    print("Python environment: OK")
    if no_map:
        print("Street map: skipped (the app shows its outline map; run again without --no-map to add it)")
    elif run([str(python), str(ROOT / "scripts" / "get_map.py")]) != 0:
        print("Street map: not downloaded (the app still runs with its outline map; run this again later)")
    return python


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def start(python: Path, port: int, browser: bool, google: bool) -> int:
    url = f"http://127.0.0.1:{port}/"
    if not port_free(port):
        print(f"Port {port} is already in use: GridLock may already be running at {url}")
        print("Open that address, or start another copy with --port 8780.")
        return 3
    env = dict(os.environ, GRIDLOCK_AI="off", GRIDLOCK_TEST_PORT=str(port))
    if google:
        env["GRIDLOCK_GOOGLE"] = "on"
    server = subprocess.Popen([str(python), "-m", "server"], cwd=ROOT, env=env)
    deadline = time.monotonic() + 90
    while True:
        if server.poll() is not None:
            print("GridLock stopped while starting; see the messages above.")
            return server.returncode or 1
        try:
            with urllib.request.urlopen(f"{url}api/health", timeout=1):
                break
        except OSError:
            if time.monotonic() > deadline:
                print("GridLock did not answer within 90 seconds; see the messages above.")
                server.terminate()
                return 1
            time.sleep(0.5)
    print(f"GridLock is running at {url}  (press Ctrl+C here to stop it)")
    if browser:
        webbrowser.open(url)
    try:
        return server.wait()
    except KeyboardInterrupt:
        print("Stopping GridLock ...")
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up (once) and start GridLock on Windows, macOS or Linux.")
    parser.add_argument("--no-map", action="store_true", help="skip the optional street map download")
    parser.add_argument("--setup-only", action="store_true", help="set up without starting")
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser")
    parser.add_argument("--port", type=int, default=8765, help="port to serve on (default 8765)")
    parser.add_argument("--google", action="store_true", help="offer Google Maps and Satellite (your own key)")
    args = parser.parse_args()
    if sys.version_info < (3, 8):
        sys.exit("Run this with Python 3.12 (python3 run.py on macOS and Linux, py run.py on Windows).")
    python = setup(args.no_map)
    if args.setup_only:
        print("Setup complete. Start GridLock with: python run.py")
        return
    sys.exit(start(python, args.port, not args.no_browser, args.google))


if __name__ == "__main__":
    main()
