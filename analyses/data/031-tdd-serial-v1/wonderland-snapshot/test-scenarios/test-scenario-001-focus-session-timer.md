## Test Scenario: Focus Session Timer (Feature 001)

**Feature:** focus-session-timer
**Concern:** Pinning the boundary behaviors between frontend countdown display, pause/resume mechanics, alert timing, and backend event logging.

---

## Frontend Scenarios

### 1. **Countdown Accuracy**
**Severity:** critical
**Scenario:** Marcus starts a 25-minute focus session. Timer displays MM:SS format and decrements every ~1000ms.
**What could go wrong:** 
- Jittery tick (100ms variance) makes display jump unpredictably
- Decimal seconds leak into the display ("25:00.5")
- Elapsed time does not track with displayed time
**Test:** `tests/test_focus_session_timer_frontend.py::test_timer_counts_down_every_1000ms`

### 2. **Alert on Completion**
**Severity:** critical
**Scenario:** Timer reaches 0:00. Visual indicator changes color, animation plays, audio alert triggers.
**What could go wrong:**
- Audio fails silently; Marcus never hears the alert
- Alert fires out of order (sound before animation)
- Alert fires multiple times if code re-runs at 0:00
**Test:** `tests/test_focus_session_timer_frontend.py::test_timer_plays_alert_on_completion`

### 3. **Pause Halts Countdown**
**Severity:** high
**Scenario:** At 10 minutes elapsed (15 minutes remaining), Marcus clicks Pause. Display freezes.
**What could go wrong:**
- Pause button disabled but timer keeps counting (user thinks it's paused but it isn't)
- Elapsed_ms continues incrementing while button is disabled
- Button state does not reflect actual pause state
**Test:** `tests/test_focus_session_timer_frontend.py::test_pause_halts_countdown`

### 4. **Resume Continues from Pause**
**Severity:** high
**Scenario:** Marcus paused at 15:00 remaining. Clicks Resume. Timer continues from 15:00.
**What could go wrong:**
- Resume resets the timer to 25:00 instead of continuing
- Pause/resume sequence leaves the timer in inconsistent state
- Resume button does not become visible/clickable after pause
**Test:** `tests/test_focus_session_timer_frontend.py::test_resume_continues_from_pause_point`

### 5. **Skip During Active Session**
**Severity:** high
**Scenario:** At 12:00 remaining, Marcus clicks Skip. Timer immediately completes.
**What could go wrong:**
- Skip does not complete the session (button click is ignored)
- Skip at 12:00 still waits for timer to reach 0:00
- Alert plays when it shouldn't (or doesn't play when it should)
**Test:** `tests/test_focus_session_timer_frontend.py::test_skip_during_active_triggers_completion`

### 6. **Skip During Paused Session**
**Severity:** medium
**Scenario:** Marcus paused at 15:00 and clicks Skip. Timer completes immediately.
**What could go wrong:**
- Skip is disabled while paused
- Skip while paused leaves the session in 'paused' state instead of 'completed'
**Test:** `tests/test_focus_session_timer_frontend.py::test_skip_during_pause_triggers_completion`

### 7. **Browser Tab Focus Loss (Unresolved in Story, Implementation Decision Required)**
**Severity:** medium
**Scenario:** Marcus starts timer and switches to another browser tab. 25 minutes elapse. He switches back. What happens?
**What could go wrong:**
- Timer pauses when tab loses focus, but never resumes when tab regains focus → alert never fires
- Timer pauses but user doesn't know (no UI indicator)
- Alert fires silently because tab was not focused → user misses it
**Implementation choice for M5:** Timer CONTINUES running when tab loses focus. Alert fires when time reaches 0, regardless of visibility. If tab regains focus after time has elapsed, alert fires immediately.
**Test:** `tests/test_focus_session_timer_frontend.py::test_tab_loses_focus_during_countdown`

### 8. **MM:SS Display Format**
**Severity:** low
**Scenario:** Timer displays time with leading zeros. 5 minutes 3 seconds = "05:03", not "5:3".
**What could go wrong:**
- Leading zeros missing: "5:3", "25:0"
- Separator is wrong: "0503", "05.03"
**Test:** `tests/test_focus_session_timer_frontend.py::test_display_format_mm_ss_with_leading_zeros`

---

## Backend Scenarios

### 9. **Log Session Completion Event**
**Severity:** critical
**Scenario:** Frontend POSTs a `session_completed` event when timer reaches 0:00 and user does not skip.
```json
{
  "session_id": "<UUID>",
  "type": "focus",
  "duration_ms": 1500000,
  "completed_at": "2025-01-15T14:30:45Z"
}
```
Server logs the event to database.
**What could go wrong:**
- Event is not persisted (HTTP 200 returned but no DB row created)
- Required fields are not validated (garbage data accepted)
- Event appears to log but has null/wrong values in DB
**Test:** `tests/test_focus_session_timer_backend.py::test_post_session_completed_event_logs_to_database`

### 10. **Session ID Validation**
**Severity:** high
**Scenario:** Frontend POSTs event with missing, empty, or malformed session_id.
**What could go wrong:**
- Invalid session_id is accepted into database
- No error response (HTTP 200 despite invalid input)
- Error response does not name the offending field
**Test:** `tests/test_focus_session_timer_backend.py::test_session_completed_requires_valid_session_id`

### 11. **Duration Validation (Positive Only)**
**Severity:** high
**Scenario:** Frontend POSTs duration_ms = -1, 0, or nonsense value.
**What could go wrong:**
- Negative duration accepted (user can log a session that ran for -5 minutes?)
- Zero duration creates ambiguous state (is it a completed session or incomplete?)
**Test:** `tests/test_focus_session_timer_backend.py::test_session_completed_requires_positive_duration_ms`

### 12. **Timestamp Format Validation (ISO8601)**
**Severity:** high
**Scenario:** Frontend POSTs `completed_at` in non-ISO8601 format: "1234567890" (unix), "Jan 15 2025", or missing.
**What could go wrong:**
- Non-ISO8601 timestamps accepted
- Server cannot parse completed_at for daily review queries (Feature 003)
- Timezone information lost
**Test:** `tests/test_focus_session_timer_backend.py::test_session_completed_requires_iso8601_timestamp`

### 13. **Idempotency: Duplicate Session ID Handling**
**Severity:** critical
**Scenario:** Frontend POSTs the same `session_id` twice (e.g., retry after network timeout).
- First POST: HTTP 200, event logged
- Second POST (identical): HTTP 200, but no new row created
**What could go wrong:**
- Duplicate event rows created (breaks daily review count, streak calculation)
- Second POST returns error instead of succeeding (forces client to retry indefinitely)
- No idempotency guarantee; system enters inconsistent state
**Invariant:** session_id is a unique key in the events table. The system must guarantee exactly-once semantics for session completions.
**Test:** `tests/test_focus_session_timer_backend.py::test_idempotency_duplicate_session_ids_do_not_create_duplicate_events`

### 14. **Session Type Enum Validation**
**Severity:** medium
**Scenario:** Frontend POSTs `type` = "yoga", "meditation", or any unrecognized string.
**What could go wrong:**
- Unknown session types accepted into database (breaks downstream queries that assume type ∈ {focus, break})
- Daily review (Feature 003) counts unknown types in the total
- Streak calculation (Feature 005) includes unknown types
**Test:** `tests/test_focus_session_timer_backend.py::test_session_type_enum_validation`

### 15. **Pause Does Not Trigger Completion Event**
**Severity:** high
**Scenario:** Marcus pauses mid-session. No event is sent to backend. Later he resumes and completes.
**What could go wrong:**
- Pause triggers a completion event (counts as "session done" even though paused)
- Event is logged but with wrong duration (partial elapsed time instead of full duration)
- Resume creates a second event (duplicate completion)
**Implementation note from contract:** Event logging only happens on:
1. Completion (timer reaches 0:00, user does not skip)
2. Skip (user clicks skip, regardless of time)
Pause does NOT trigger an event.
**Test:** `tests/test_focus_session_timer_backend.py::test_pause_does_not_trigger_completion_event`

### 16. **Session Event Schema**
**Severity:** medium
**Scenario:** After posting a valid session_completed event, retrieve it and verify all fields.
**What could go wrong:**
- Required field is missing from response (e.g., no session_id, no created_at)
- Field names don't match contract (session_id vs. sessionId vs. sid)
- Data types wrong (duration_ms is string instead of number)
**Test:** `tests/test_focus_session_timer_backend.py::test_session_event_schema_includes_required_fields`

### 17. **Timestamp Timezone Awareness**
**Severity:** medium
**Scenario:** Server logs a session event. Both `completed_at` (from request) and `created_at` (server-generated) are ISO8601 with timezone info.
**What could go wrong:**
- Timezone information lost (no Z suffix; downstream queries can't compare timestamps across timezones)
- completed_at stored as string but not parsed as datetime (Feature 003 daily review query fails)
- created_at missing (can't sort events by server-received order)
**Test:** `tests/test_focus_session_timer_backend.py::test_session_event_timestamps_are_iso8601_and_timezone_aware`

### 18. **List Session Events**
**Severity:** medium
**Scenario:** Marcus completes three sessions. GET /api/sessions/events (or similar) returns all three.
**What could go wrong:**
- Endpoint does not exist
- Query returns empty list (events are logged but not retrievable)
- Events returned out of order (affects daily review sort)
**Test:** `tests/test_focus_session_timer_backend.py::test_get_session_events_lists_all_logged_completions`

### 19. **Contract Adherence: Endpoint Shape Matches Feature 001 Contract Note**
**Severity:** high
**Scenario:** Verify that backend implementation matches contract note 001: "Session State and Mutations (Feature 001)".
**What could go wrong:**
- Endpoint path is different from contract
- Request/response schema diverges from contract
- Contract was updated but implementation was not
**Test:** `tests/test_focus_session_timer_backend.py::test_contract_version_matches_session_state_and_mutations_v1`

---

## Cross-Stack Scenarios

### 20. **Pause-then-Complete Generates One Event, Not Two**
**Severity:** high
**Scenario:** Marcus starts timer → pauses at 15:00 → resumes → timer reaches 0:00.
**What could go wrong:**
- Two events logged (one on pause, one on completion) → daily review counts this as two sessions
- Event duration_ms reflects only the resumed portion (missing the earlier elapsed time)
- No event logged at all (the resume somehow cancels the earlier elapsed)
**Invariant:** A single continuous user intent (one timer start) should produce exactly one event, regardless of pause/resume cycles.
**Test:** Covered by combination of frontend pause/resume tests + backend event idempotency tests

---

## Observations for the Team

**Unresolved from story confusion-flags:**
1. **Tab focus loss behavior** — Story asks "does timer keep counting?" Implementation choice (timer continues, alert fires) is specified above; if the team disagrees, update and re-test.

**Contract gaps identified:**
1. Contract note 001 does not specify whether `pause` creates a pause-state event or not. Assuming not; if the team wants pause tracking (for analytics), add a scenario.
2. Contract does not specify the exact HTTP endpoint path (POST /api/sessions/completed vs. /api/events vs. etc.). Tweedledee and Tweedledum should nail this in contract negotiation before M5.

**Critical invariants pinned by these scenarios:**
1. `session_id` is unique; no duplicate events from the same session
2. Timer accuracy: ±50ms jitter is acceptable; >100ms is a bug
3. Pause/resume mechanics: multiple pause/resume cycles on one timer = exactly one completion event
4. Timestamps: all times are ISO8601 with timezone info (Z suffix)
5. Events are persisted immediately; no "batch" or "delay" logic in v1
