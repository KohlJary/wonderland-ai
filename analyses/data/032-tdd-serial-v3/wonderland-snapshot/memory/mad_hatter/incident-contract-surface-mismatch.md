# Incident: Contract Surface Mismatch in Focus Session Tests

**Date:** M4 Focus Session iteration 1
**Severity:** blocking for M5
**Root Cause:** Story requires pause/resume; contracts don't define the interface

## The Issue

I wrote three test files for the focus session feature:

1. `test_focus_session_with_visual_countdown.py` — tests POST /sessions/log (completion logging)
   - Aligns with contracts 001, 003, 005
   - ✓ Contract-aligned

2. `test_focus_session_user_journey.py` + `test_focus_session_edge_cases.py` — test stateful session API
   - Assumes `POST /sessions/focus`, `GET /sessions/{id}`, `PATCH /sessions/{id}` for pause/resume
   - ✗ Contradicts contracts (no pause/resume interface defined)

## Why This Happened

The story explicitly requires pause/resume in acceptance criteria. I wrote scenarios to cover that requirement. But the contracts (001 & 005) specify ephemeral client-side sessions with only completion event logging. I did not surface the contradiction during scenario generation — I flagged it as an implicit question ("contract-001 must finalize pause interface") but did not block scenario emission.

This is on me: **scenario sprawl + skipping contract-boundary discipline**.

## Decision Point

The pair must choose before M5:

1. **Include pause/resume in v1** — expand contracts to define state persistence, pause/resume endpoints, idempotence semantics.
2. **Descope pause/resume to v2** — I'll drop the pause/resume test scenarios; coverage limits to the contracted surface (completion logging + timer drift + idempotence).

Until the pair decides, the test surface is incomplete and the story's requirements are only partially testable.

## Lesson

Contract boundaries are load-bearing. I should have stopped scenario generation at the point I realized "I don't know if pause/resume is backend or client-side per the contract" and surfaced it as a blocker, rather than writing scenarios that assumed an answer.
