## Test Scenario 002: Kenji Settings Change Mid-Session

**Source Story:** story-007-kenji-adds-a-new-language-pair-mid-session

**Narrative:**
Kenji is actively moderating Japanese→English threads. A new client arrives needing Chinese→English support. He adds the language pair without losing his active threads or requiring a session reload.

**Acceptance Criteria:**
- New language pair appears in the active list immediately
- Existing threads remain active and unaffected
- Settings persist after adding the new pair
- No session interrupt or reload occurs
- Session ID remains stable

**Severity:** CRITICAL

**Test File:** `tests/test_session_settings_change_midstream_kenji.py`

**Test Cases:**
1. `test_kenji_adds_language_pair_mid_session` — Core non-blocking settings operation
2. `test_kenji_existing_threads_unaffected_by_new_pair` — Existing state is not cleared
3. `test_kenji_settings_persist_across_session` — Settings stick until session ends
4. `test_kenji_can_add_multiple_pairs_sequentially` — Multiple additions work
5. `test_kenji_settings_broadcast_to_server_timing` — Contract: when does sync happen?
6. `test_kenji_session_not_reloaded_on_settings_change` — No reload triggered
7. `test_kenji_cannot_modify_completed_session_settings` — Completed sessions immutable

**Backend Implementation Requirement:**
- PATCH /sessions/{id} must support settings updates without full reload
- Settings operations must be idempotent
- Completed sessions must reject further modifications

**Concern:**
The exact contract shape for language pairs is TBD. Tests include placeholders for how pairs are stored (nested in session vs. separate endpoint). Contract note on pair semantics needed before M5 implementation.
