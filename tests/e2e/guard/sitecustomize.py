"""Deny the tested server's outbound TCP connections outside loopback."""

import ipaddress
import os
import socket


_connect = socket.socket.connect
_connect_ex = socket.socket.connect_ex


def _check(address: object) -> None:
    if not isinstance(address, tuple) or not address:
        return
    host = address[0]
    if host == "localhost":
        return
    try:
        if ipaddress.ip_address(host).is_loopback:
            return
    except ValueError:
        pass
    raise PermissionError("non-loopback socket blocked by GridLock test guard")


def _guarded_connect(self: socket.socket, address: object) -> None:
    _check(address)
    return _connect(self, address)


def _guarded_connect_ex(self: socket.socket, address: object) -> int:
    _check(address)
    return _connect_ex(self, address)


socket.socket.connect = _guarded_connect
socket.socket.connect_ex = _guarded_connect_ex
os.environ["GRIDLOCK_SOCKET_GUARD_ACTIVE"] = "1"
