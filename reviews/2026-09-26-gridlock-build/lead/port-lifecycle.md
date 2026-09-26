# LEAD — test-server port lifecycle repair (2026-09-26)

T3.4a's lane gate twice reached the browser tests with all area assertions passing, then failed to bind port 8772 with WinError 10013 despite a ten-second transient retry. After the second run, `netstat` showed many 8772 `TIME_WAIT` sockets and no listening process. The function-scoped `live_server` fixture restarted the server for every browser case.

RED: `tests/test_harness.py::test_e2e_server_reused_within_module_and_released_before_shell_module` failed because the fixture scope was `function`. A trial session-scoped fixture passed 32 focused checks but made the full gate fail with 17 shell-fixture setup errors: `tests/e2e/test_shell.py` intentionally starts a different fixture server on the same lane port. The final module-scoped fixture shares one server across a browser module and releases it before the shell module.

GREEN: 49 focused harness, project-detail, search and shell tests passed. The main quick gate passed 235 Python tests, 17 shell tests and 18 browser audits. The occupied-port guard and its test remain intact. T3.4a still needs a lane gate rerun on this merged harness change before G2 release.
