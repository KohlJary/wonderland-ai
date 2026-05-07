## Test Scenario 003: Jamie App Close and Reopen

**Source Story:** story-008-jamie-closes-the-app-and-reopens-it-hours-later

**Narrative:**
Jamie closes the app after 20 minutes of use. Hours later, a new translation request arrives and Jamie reopens the app. The app should feel continuous, not like a fresh start.

**Acceptance Criteria:**
- Session persists across app close/reopen
- Session ID is identical before and after closure
- All session state is intact (threads, settings, language pairs)
- No re-login or re-authentication is required on reopen
- No stale-session timeout discards old data

**Severity:** CRITICAL

**Test File:** `tests/test_session_close_reopen_jamie.py`

**Test Cases:**
1. `test_jamie_session_survives_app_closure_and_reopen` — Core recovery across closure
2. `test_jamie_no_stale_session_timeout` — Absence of expiration timeout
3. `test_jamie_all_prior_state_available_on_reopen` — Complete state restoration
4. `test_jamie_thread_list_unchanged_after_reopen` — Threads are intact
5. `test_jamie_settings_unchanged_after_reopen` — Settings are preserved
6. `test_jamie_no_re_login_required_on_reopen` — Direct session access via ID
7. `test_jamie_multiple_sequential_closes_and_reopens` — Multiple cycles work
8. `test_jamie_server_has_newer_data_than_cached_session` — Conflict resolution (TBD)
9. `test_jamie_session_id_stable_across_all_operations` — ID never changes
10. `test_jamie_concurrent_closes_and_reopens_on_multiple_devices` — Multi-device resilience

**Backend Implementation Requirement:**
- Session must be persisted to a backing store (IndexedDB in M1)
- GET /sessions/{id} must reliably retrieve old sessions
- No session expiration (or expiration >> hours)
- Session ID is the canonical lookup key

**Concern:**
Story 008 confusion flags mention: "Unclear whether scroll position / viewport state is part of 'session' or a fast-follow." These tests assume session = focus session record + language pairs + threads. Scroll/viewport deferred to later work. Also: "conflict resolution if server has newer data" — tests placeholder this as "trust server," but contract should clarify.
