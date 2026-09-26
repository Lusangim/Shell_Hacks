"""The test server never attaches to a different lane's occupied port."""

import socket
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.harness import require_free_loopback_port, required_test_port
from tests import harness


def test_port_is_required(monkeypatch):
    monkeypatch.delenv("GRIDLOCK_TEST_PORT", raising=False)
    with pytest.raises(RuntimeError, match="GRIDLOCK_TEST_PORT"):
        required_test_port()


def test_busy_port_fails_before_server_launch():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        started = time.monotonic()
        with pytest.raises(RuntimeError, match="already bound"):
            require_free_loopback_port(port)
        assert time.monotonic() - started < 0.5


def test_recently_closed_server_port_is_reusable():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        with socket.create_connection(("127.0.0.1", port)) as client:
            peer, _ = listener.accept()
            peer.sendall(b"x")
            peer.close()
            assert client.recv(1) == b"x"
    require_free_loopback_port(port)


def test_transient_windows_bind_denial_retries_past_three_seconds(monkeypatch):
    """A just-closed fixture port can deny bind without an active listener."""
    attempts = 0
    ticks = 0

    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def setsockopt(self, *_args):
            return None

        def settimeout(self, *_args):
            return None

        def bind(self, _address):
            nonlocal attempts
            attempts += 1
            if attempts <= 45:
                raise PermissionError(10013, "transient Windows bind denial")

        def connect_ex(self, _address):
            return 10061  # No process is listening on the denied port.

    def monotonic():
        nonlocal ticks
        ticks += 1
        return ticks / 10

    monkeypatch.setattr(harness, "socket", SimpleNamespace(
        AF_INET=socket.AF_INET, SOCK_STREAM=socket.SOCK_STREAM,
        SOL_SOCKET=socket.SOL_SOCKET, SO_REUSEADDR=socket.SO_REUSEADDR,
        socket=lambda *_args: FakeSocket(),
    ))
    monkeypatch.setattr(harness, "time", SimpleNamespace(monotonic=monotonic, sleep=lambda _seconds: None))

    require_free_loopback_port(8770)
    assert attempts == 46


def test_server_socket_guard_rejects_non_loopback():
    guard = Path(__file__).parent / "e2e" / "guard"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(guard)
    probe = (
        "import os, socket; assert os.environ.get('GRIDLOCK_SOCKET_GUARD_ACTIVE') == '1'; s=socket.socket(); "
        "\ntry: s.connect(('198.51.100.1', 80))"
        "\nexcept PermissionError: pass"
        "\nelse: raise SystemExit('non-loopback connection was allowed')"
    )
    result = subprocess.run([sys.executable, "-c", probe], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_verify_refuses_an_occupied_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        env = os.environ.copy()
        env["GRIDLOCK_TEST_PORT"] = str(listener.getsockname()[1])
        result = subprocess.run(
            ["cmd", "/c", str(Path(__file__).resolve().parents[1] / "VERIFY.cmd")],
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 3, result.stdout + result.stderr
