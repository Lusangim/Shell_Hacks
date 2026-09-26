"""The test server never attaches to a different lane's occupied port."""

import socket
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.harness import require_free_loopback_port, required_test_port


def test_port_is_required(monkeypatch):
    monkeypatch.delenv("GRIDLOCK_TEST_PORT", raising=False)
    with pytest.raises(RuntimeError, match="GRIDLOCK_TEST_PORT"):
        required_test_port()


def test_busy_port_fails_before_server_launch():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        with pytest.raises(RuntimeError, match="already bound"):
            require_free_loopback_port(port)


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
