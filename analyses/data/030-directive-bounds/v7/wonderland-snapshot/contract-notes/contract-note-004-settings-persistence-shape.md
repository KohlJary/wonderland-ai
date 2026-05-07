## Contract Note 004: Settings persistence shape

**State:** tension_unresolved
**Contract Version:** (locked, validation policy needed)

**Current Shape:**

GET /settings returns: { focus_duration_seconds (int, default 1500), break_duration_seconds (int, default 300) }.
PATCH /settings { focus_duration_seconds: int, break_duration_seconds: int } updates and returns same shape.

**Tension:**

Backend validation enforcement. The proposal says "backend does not enforce duration constraints (frontend is responsible)." But test scenario test-scenario-010 ("Settings duration values must be validated and rejected if out-of-range") expects backend to reject PATCH requests with out-of-range values, returning 400 Bad Request.

Test expectations (from test_feature_003_edge_cases.py):
- focus_duration_seconds: must be 300-3600 (5-60 min)
- break_duration_seconds: must be 60-1800 (1-30 min)
- Out-of-range values should return 400 or 422 from PATCH /settings

Frontend impact: I'll validate on client-side (prevent user from entering invalid values via sliders). But the contract assumption for M5 implementation is:

**Defense in depth:** backend validates on receipt. If a frontend bug or malicious client sends invalid durations, backend rejects with 400 Bad Request and clear error message (e.g., "focus_duration_seconds must be between 300 and 3600 seconds"). Frontend sees the rejection, shows an error banner, and reverts the local state.

This is standard REST API hygiene — the boundary between client and server validates the contract at the boundary.

**Frontend Impact (Tweedledee):**

Frontend validates min/max bounds on client-side (5–60 min for session, 1–30 min for break) using sliders that don't allow out-of-range input. On user change, I optimistically update local state immediately and PATCH /settings async. If PATCH fails with 400/422 (validation error), I revert the local state and show an error banner. If PATCH fails with 5XX (server error) or timeout, I show a retry option. Settings apply to the next session only; in-progress sessions ignore setting changes.

**Backend Impact (Tweedledum):**

Backend stores per-user settings as mutable metadata. GET /settings returns current user's settings (or defaults if not yet set). PATCH /settings updates them, validates input:
- focus_duration_seconds must be 300 ≤ x ≤ 3600 (5–60 minutes)
- break_duration_seconds must be 60 ≤ x ≤ 1800 (1–30 minutes)

Out-of-range values are rejected with 400 Bad Request, error body includes clear message naming the invalid field and the valid range. Response on successful PATCH is the updated settings object.

**Decision Required:**

Does backend validate on PATCH /settings, or is validation frontend-only? Test scenarios assume backend validates. Recommend: **yes, backend validates** (standard defense-in-depth). If backend does not validate, test scenarios need adjustment.

**Notes:**

If Tweedledum agrees to backend validation, mark this contract agreed with the updated Backend Impact clause above. If backend validation is not feasible, escalate to Dodo to mediate between test expectations and implementation constraints.
