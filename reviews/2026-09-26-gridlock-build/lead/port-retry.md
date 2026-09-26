# LEAD — transient Windows test-port bind denial (2026-09-26)

WEB T2.5a and API T3.4a each saw intermittent `WinError 10013` while `tests/harness.py::require_free_loopback_port` retried a just-closed lane port. An independent read-only check found no listener on 8777 after the WEB gate. The harness already distinguishes an active listener and fails that case immediately; its three-second wait was too short for the observed transient denial.

Test first: `test_transient_windows_bind_denial_retries_past_three_seconds` simulates 45 denied binds with a refused connection probe, then a successful bind after more than three simulated seconds. RED: `1 failed`, `RuntimeError: test port 8770 is already bound` from the three-second deadline. The smallest fix extends the transient-only deadline to ten seconds. GREEN: `tests/test_harness.py` **6 passed in 0.70s**, including the existing occupied-port fast failure and recently-closed reuse checks. No check was weakened or skipped; the live-listener branch still raises immediately. Full main quick gate follows the next integrated WEB merge.

2026-09-26 — A refused connection after a Windows bind denial is a transient candidate, while a listening process remains an immediate port-ownership failure.
