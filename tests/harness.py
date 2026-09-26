"""Port ownership checks shared by the test server fixture."""

import os
import socket


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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            listener.bind(("127.0.0.1", port))
        except OSError as exc:
            raise RuntimeError(f"test port {port} is already bound") from exc
