# Test Scenario 003: Feature 001 — Pause duration accumulates correctly across multiple pauses

**Feature:** Run a focused work session with built-in break
**Severity:** HIGH
**Concern:** A session can be paused multiple times (pause→resume→pause→resume→complete). Each pause increments Session.paused_duration_ms. On completion, session_duration_ms = elapsed - paused_duration_ms. If paused_duration_ms does not accumulate correctly, the recorded session duration is wrong.

## Scenario

User starts a 25-minute session, pauses after 5 minutes, resumes, pauses again after 8 more minutes, resumes, and lets it run to completion. Total pause time: 5 + 8 = 13 minutes. Total elapsed wall-clock time: 25 + 13 = 38 minutes. Session duration recorded should be 25 minutes (minus the pause time).

## Assertion

SessionRecord.session_duration_ms = (elapsed_wall_clock - paused_duration_ms). Multiple pause-resume cycles correctly accumulate the paused_duration_ms on each pause transition. The final recorded duration reflects the active (unpaused) time only.

## Failure Mode

Paused time not accumulated (e.g., only the last pause is counted, or pauses are not accumulated at all) results in a recorded session duration that is longer than actual focus time.

## Test Implementation

See `tests/test_feature_001_state_machine.py::test_pause_duration_accumulation`.
