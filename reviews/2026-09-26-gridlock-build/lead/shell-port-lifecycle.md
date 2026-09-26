# LEAD shell server lifecycle repair — 2026-09-26

API T3.2's lane quick gate finished its Python phase at 335 passed but encountered 11 shell e2e setup errors: Windows refused repeated binds to the lane's port 8772. The shell test module was starting and stopping the same server for each test.

- RED: `tests/e2e/test_shell.py::test_shell_server_reused_within_module` failed with `assert 'function' == 'module'`.
- Change: scope `shell_server` to the shell test module, retaining the fixture's occupied-port check before its first bind and its shutdown after the module.
- Focused GREEN: `tests/e2e/test_shell.py` — 18 passed.
- Main quick gate GREEN: 257 Python passed, 18 shell passed, 18 browser audits passed, `QUICK GATE PASS`.
- Baseline increased from 256 to 257 for the added regression check.

The API lane must sync this commit and rerun its own full gate. This report records only the lead's checks.
