## Test Scenario 006: Abandon a session without affecting history

**Source:** feature-006-abandon-a-session-without-affecting-history
**Persona:** Jordan, 29, a consultant
**Severity:** high (feature definition is core to the v1 scope)
**Concern:** Session lifecycle, immutability, and historical accuracy

---

## Happy Path

**Scenario: Jordan abandons an interrupted session**

1. Jordan starts a 25-minute focus session
2. 10 minutes in, a calendar alert pops — urgent meeting
3. Jordan taps the "Stop" or "Abandon" button
4. A confirmation dialog appears: "This session will not be saved"
5. Jordan confirms
6. The app returns to the idle state
7. Jordan checks "Today's Sessions" — the abandoned session is not listed
8. After the meeting, Jordan starts a fresh session
9. **Observable outcome:** The abandoned session is completely gone from history; only completed sessions count

---

## Failure Modes

**Hatter's Breakdown:**

1. **Abandoned session still counts in today's total** — Jordan abandons, but count increases anyway
   - **Why this matters:** Feature is useless if abandoned sessions aren't actually removed
   - **Severity:** high (feature failure)

2. **Abandoned session appears in historical queries** — Jordan queries last week, abandoned session is listed
   - **Why this matters:** Historical data is inaccurate; user's analysis is misleading
   - **Severity:** high (silent wrongness)

3. **Cannot abandon completed session** — somehow the API allows abandoning a finished session
   - **Why this matters:** Completed sessions should be immutable; feature should only work on active sessions
   - **Severity:** medium (edge case, but violates invariant)

4. **Abandoning twice fails on second attempt** — Jordan accidentally taps twice; second DELETE returns 500
   - **Why this matters:** User gets error instead of graceful idempotency
   - **Severity:** medium (defensive UX)

5. **Abandon succeeds but session still active** — DELETE returns 204, but session is still running
   - **Why this matters:** User is confused; timer might keep counting
   - **Severity:** high (breakage)

6. **Race condition: abandon vs. complete** — Jordan starts to tap complete, connection drops, retries send abandon
   - **Why this matters:** Session ends up in undefined state (deleted or completed?)
   - **Severity:** low (rare, but possible with poor networking)

7. **Abandoned session hard-deleted, no audit trail** — backend removes the session entirely from DB
   - **Why this matters:** User loses visibility into why sessions are missing
   - **Severity:** low (nice-to-have for v1, required for long-term support)

8. **User isolation violation** — Jordan abandons their session; someone else's session is deleted
   - **Why this matters:** Privacy/security violation
   - **Severity:** high (breakage; critical when multi-user is added)

9. **Abandon button is hidden** — feature exists in API, but frontend can't find the button
   - **Why this matters:** User can't actually use the feature
   - **Severity:** high (UX failure; but primarily frontend concern)

10. **Response format inconsistent with other endpoints** — DELETE returns different JSON structure than POST/PATCH
    - **Why this matters:** Frontend expects one format, gets another; parsing fails
    - **Severity:** medium (frontend defensive coding should handle this, but it's inelegant)

---

## Test Implementation

See `tests/test_session_006_abandon.py`:

- **Happy path:** `TestAbandonSessionHappyPath` — Jordan abandons, new session starts, history is clean
- **Edge cases:** `TestAbandonSessionEdgeCases` — idempotency, immutability, race conditions, etc.

**Red-green target:** All tests in `tests/test_session_006_abandon.py` should fail until M5 implements:
- DELETE /sessions/{id} endpoint
- Soft delete: sets is_deleted=true (preserves audit trail)
- Excluded from all queries: GET /sessions/today, GET /sessions/range, etc.
- Idempotent: DELETE on already-deleted session returns 204 or 404 (not 500)
- Prevents abandonment of completed sessions (returns 409 or 403)
- Returns 200 or 204 (per contract)
- Allows new session to start immediately after abandon (1-active invariant not violated)
