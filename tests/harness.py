"""Port ownership checks shared by the test server fixture."""

import os
import socket
import time


def required_test_port() -> int:
    raw = os.environ.get("GRIDLOCK_TEST_PORT")
    if raw is None:
        raise RuntimeError("GRIDLOCK_TEST_PORT is required; never use the demo port")
    try:
        port = int(raw)
    except ValueError as exc:
        raise RuntimeError("GRIDLOCK_TEST_PORT must be an integer") from exc
    if port < 1 or port > 65535 or port == 8765:
        raise RuntimeError("GRIDLOCK_TEST_PORT must be a valid private test port")
    return port


def require_free_loopback_port(port: int) -> None:
    deadline = time.monotonic() + 10
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            # Windows can retain a just-closed test server's port briefly.
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                listener.bind(("127.0.0.1", port))
                return
            except OSError as exc:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                    probe.settimeout(0.1)
                    occupied = probe.connect_ex(("127.0.0.1", port)) == 0
                if occupied or time.monotonic() >= deadline:
                    raise RuntimeError(f"test port {port} is already bound") from exc
        time.sleep(0.05)
