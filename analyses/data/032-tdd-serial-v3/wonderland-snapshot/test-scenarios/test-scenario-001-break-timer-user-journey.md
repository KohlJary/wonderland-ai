## Test Scenario: Keisha sets break duration and it starts automatically when focus ends

**Severity:** breakage

**Setup:**
Keisha has launched the app. No session is running. Break duration is at default (300 seconds).

**Trigger:**
Keisha sets break duration to 600 seconds via settings UI. Focus session starts and runs to completion. Timer should transition to break timer.

**Expected:**
Break timer starts automatically, showing 600 seconds remaining. The timer counts down at the correct rate (1 second per second). When 0 is reached, session marks as completed.

**Concern:**
The contracts don't explicitly say when the break timer starts: immediately when focus completes, or only after the user acknowledges a notification? Also, is the break session created in the backend (via POST /sessions/log), or is it ephemeral client-side until completion? Keisha's story implies seamless auto-start, so I'm assuming: (1) Focus completion immediately triggers break timer on client, (2) Break completion POSTs to /sessions/log once (idempotent). But if backend needs to create the break session first, there's a race.

**Property:**
For all break durations D in [60, 1800] seconds, if a focus session completes and break_duration_seconds = D, then the break timer's remaining_seconds should be in range [D - 1, D] (allowing 1 second clock drift).

**Implies:**
- Depends on Contract-002 (settings storage) — frontend must read break_duration_seconds from localStorage and apply to next session.
- Depends on Contract-001 (session model) — backend must accept POST /sessions/log for break sessions with type='break'.
- Depends on Contract-003 (session completion event) — frontend must POST when break timer reaches 0.

**Test Files:**
- `tests/test_break_timer_user_journey.py::test_keisha_sets_break_duration_and_it_starts_automatically_on_focus_end`

---

## Test Scenario: Keisha adjusts break duration before break starts (no focus session running yet)

**Severity:** breakage

**Setup:**
Focus session is running. Break timer has not yet started (focus is still active, ~2 minutes remaining).

**Trigger:**
Keisha opens settings and changes break duration from 300 to 900 seconds. Focus session then ends.

**Expected:**
When focus completes, the break timer starts with 900 seconds (the new setting), not 300. No race between setting-update and auto-start.

**Concern:**
If the break timer is queued or pre-calculated during focus, a late setting change might not propagate. If settings are read only once at app startup, changes mid-session won't be visible until next app launch. Keisha's story says 'adjust without losing my default', implying changes take effect next session. But does 'next session' mean 'immediately after current session ends' or 'next app launch'? Assuming immediate.

**Property:**
Let D1 = break duration at app start, D2 = break duration after user updates settings mid-focus-session. When the focus session ends, the break timer's configured duration should be D2, not D1.

**Implies:**
- Depends on how frontend caches vs. reads settings. If settings are a singleton loaded once, mid-session updates won't apply. If settings are read fresh on each session end, they will.
- No backend implication (settings are client-local per Contract-002).

**Test Files:**
- `tests/test_break_timer_user_journey.py::test_keisha_adjusts_break_duration_mid_focus_and_new_duration_applies`

---

## Test Scenario: Break timer completion event is idempotent (fires twice, only one session recorded)

**Severity:** silent-wrongness

**Setup:**
Break session is running. Timer has reached 0 and the completion event has fired once (session logged to backend).

**Trigger:**
Due to network retry or event-bus replay, the same completion event fires again (same timestamp, same session ID). Backend receives two POST /sessions/log requests with identical payloads.

**Expected:**
Backend treats the second request as idempotent: it returns 200 OK (or 409 Conflict if the contract allows it), but does NOT create a duplicate session record. Daily history includes the session exactly once.

**Concern:**
If the backend isn't idempotent, the second POST creates a duplicate session. Daily history shows the user worked 50 minutes instead of 25. Analytics are corrupted. This is silent wrongness — the UI looks fine, but the data is wrong. Contracts say frontend will retry with exponential backoff, and idempotency is on the backend to handle duplicates. But contracts don't name the idempotency key or strategy yet.

**Property:**
For any session S with completion event E, if E is delivered twice to POST /sessions/log, the resulting session record in the database is exactly one, not two.

**Implies:**
- Depends on Contract-003 (session completion event) — backend needs to define idempotency. Either: (1) use a session_id + completed_at timestamp as the key, or (2) add an event_id field to the payload.
- This might block M5 if the contract doesn't define the idempotency strategy. Tweedledum: if this is unclear, raise a concern.

**Test Files:**
- `tests/test_break_timer_edge_cases.py::test_break_completion_event_is_idempotent_no_duplicate_sessions`

---

## Test Scenario: Break timer display never shows negative remaining seconds

**Severity:** silent-wrongness

**Setup:**
Break timer is running. Client-side elapsed time is calculated as (now - startTime). Session duration is 600 seconds.

**Trigger:**
600 seconds have elapsed since the break started. Client calculates remaining_seconds = (duration - elapsed). Due to clock skew, elapsed might exceed duration by a millisecond.

**Expected:**
GET /sessions/{id} returns remaining_seconds in range [0, 600]. Never negative. Never wrapping to a huge positive number (e.g., 2^31).

**Concern:**
If remaining is calculated as a signed integer and elapsed > duration, remaining goes negative. If it's unsigned, it wraps. Either way, the UI displays wrong information. Keisha sees '-1 seconds' or '4294967295 seconds' and loses trust in the timer. This is a classic off-by-one in the display layer, but it's silently broken — the API returns the wrong value, and the UI trusts it.

**Property:**
For any session S with duration D and elapsed time E, if E >= D, then remaining_seconds = max(0, D - E) (clamp to 0).

**Implies:**
- Backend-side: when calculating remaining_seconds, clamp to [0, duration].
- Frontend-side: when displaying remaining_seconds, also clamp (belt-and-suspenders).

**Test Files:**
- `tests/test_break_timer_edge_cases.py::test_break_timer_display_never_shows_negative_remaining_seconds`

---

## Test Scenario: Break timer can be skipped (user taps 'Skip Break', goes straight to next focus)

**Severity:** degradation

**Setup:**
Break timer is running. User has not yet skipped.

**Trigger:**
User taps 'Skip Break' button. A skip event is emitted. The app transitions to a new focus session (or idle state waiting for next focus).

**Expected:**
Break session is marked as 'skipped' (not 'completed'). No audio notification. UI shows focus mode (or idle) immediately. Daily history records the break as skipped (not part of total break time).

**Concern:**
Keisha's story says 'skip the break and go straight to the next focus session.' But the contracts don't mention a skip action. Does the skip flow through the same session-completion event (with status='skipped'), or a different endpoint? If it's not in the contract, M5 might not implement it, and the feature will be incomplete.

**Property:**
When a break session is skipped, its status should be 'skipped', not 'completed' or 'running'. It should not appear in daily break-time totals.

**Implies:**
- This scenario might expose a contract gap. Tweedledum: does Contract-001 or Contract-003 define a 'skip' action? If not, Keisha's acceptance criterion ('skip the break and go straight to the next focus session') is at risk.
- If skip is in-scope, it should be a PATCH /sessions/{id} { action: 'skip' } or a POST /sessions/{id}/skip, with idempotency.

**Test Files:**
- `tests/test_break_timer_user_journey.py::test_keisha_skips_break_and_goes_straight_to_next_focus`

---

## Test Scenario: Break timer pause and resume preserves remaining time

**Severity:** degradation

**Setup:**
Break timer is running with 300 seconds remaining (out of 600 total).

**Trigger:**
Keisha taps pause. The countdown should freeze. After 30 seconds of real time, she taps resume. The timer should still show 300 seconds remaining (the pause point), not 270.

**Expected:**
Break session status='running', remaining_seconds=300 (unchanged during pause window). After resume, remaining_seconds still <=300 (not 270).

**Concern:**
If pause doesn't freeze elapsed time, the countdown continues to advance even though the UI shows "paused." After resume, the timer jumps backward or forward, confusing the user.

**Property:**
If a session is paused at time T with remaining_seconds = R, and the wall-clock time advances by N seconds while the session stays paused, then remaining_seconds should still equal R when retrieved (or R + small_drift, depending on implementation).

**Implies:**
- Backend-side: pause action must record the pause time and not advance elapsed time while paused.
- Frontend-side: display remaining_seconds as frozen while paused.

**Test Files:**
- `tests/test_break_timer_edge_cases.py::test_break_timer_pause_and_resume_preserves_remaining_time`

---

## Test Scenario: Break completion while paused does not auto-complete

**Severity:** silent-wrongness

**Setup:**
Break timer is running. Keisha pauses it.

**Trigger:**
Due to a scheduler glitch or test artifact, the timer's "completion at 0 seconds" event still fires while the session is paused.

**Expected:**
Session status remains 'paused' (not 'completed'). No notification fires to Keisha until she explicitly resumes or skips.

**Concern:**
If the backend transitions the session to 'completed' whenever a completion event fires, it will ignore the paused state. The UI shows paused; the backend shows completed. Keisha resumes, and the app is confused.

**Property:**
Completion events should only transition status from 'running' to 'completed', never from 'paused' to 'completed'.

**Implies:**
- Backend-side: completion handler must check status before transitioning. Only 'running' -> 'completed' is valid. 'paused' -> 'completed' should be rejected or ignored.

**Test Files:**
- `tests/test_break_timer_edge_cases.py::test_break_completion_while_paused_does_not_auto_complete`
