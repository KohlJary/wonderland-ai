# Test Scenario 004: Feature 001 — Clock drift reconciliation (>1s deviation triggers hard reset)

**Feature:** Run a focused work session with built-in break
**Severity:** MEDIUM
**Concern:** Frontend manages a transient timer display (client-side countdown) while the backend is the source of truth. If the client's system clock drifts >1s from the server's, the frontend's display can become stale. Per the contract, a >1s deviation triggers a hard reset.

## Scenario

Frontend's local timer is running with client-side elapsed tracking. An update from the backend (Session state snapshot) arrives. The backend's derived elapsed time differs from the frontend's local elapsed by more than 1 second.

## Assertion

Frontend detects the deviation >1s and resets its local elapsed counter to match the backend's derived elapsed (started_at + current_time - paused_duration_ms). The visual timer jumps to the correct value. Subsequent updates reconcile without jumping (clock is synced).

## Failure Mode

If clock drift is not detected and corrected, the frontend's displayed timer drifts further from the actual elapsed time. The user sees a countdown that no longer matches the actual focus time, causing confusion at session completion.

## Test Implementation

See `tests/test_feature_001_state_machine.py::test_clock_drift_hard_reset`.
