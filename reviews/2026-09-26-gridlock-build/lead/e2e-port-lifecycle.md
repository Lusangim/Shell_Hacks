# LEAD e2e port lifecycle repair — 2026-09-26

After the shell module fix, API's definitive gate produced 343 passing tests and 15 setup errors in `tests/e2e/test_project_detail.py`. The first traceback was `live_server -> require_free_loopback_port(8772) -> listener.bind -> PermissionError [WinError 10013]`, then `RuntimeError: test port 8772 is already bound`. Port 8772 was free immediately after the gate. This was a transient bind denial between e2e modules; no product assertion failed.

- RED: the new lifecycle check expected session scope and failed with `assert 'module' == 'session'`. A new auxiliary-port check failed collection because the helper did not exist.
- Change: run the production `live_server` once per Python suite; assign two synthetic shell servers deterministic lane-derived loopback ports; give the standalone shell and audit gate invocations fresh lane-derived ports. Keep the primary lane port occupied check before every gate and the per-server bind guard. The test command still begins with its assigned lane port.
- Focused GREEN: harness plus shell tests, 26 passed.
- Main quick gate GREEN: 258 Python, 18 shell, 18 browser audits; `QUICK GATE PASS`.
- Baseline increased from 257 to 258 for the new port-mapping regression check.

The API lane needs to sync this commit and run its own gate. This report records only the lead's checks; the prior API gate remains red until that rerun.
