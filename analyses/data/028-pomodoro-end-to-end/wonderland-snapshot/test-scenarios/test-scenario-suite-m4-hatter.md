# Mad Hatter Test Scenario Suite — M4 Tea Party

**Thread:** test-scenarios (M4)
**Persona:** Mad Hatter, QA / Testing
**Total Scenarios:** 19 edge-case scenarios across 6 features
**Status:** All scenarios documented and mapped to pytest test files

## Scenario Index

### Feature 001: Start a focus session (Timer authority & client-server reconciliation)

1. **Client Clock Drift >5s Triggers Resync** (silent-wrongness)
   - File: `tests/test_feature_001_timer_authority.py::test_client_drift_greater_than_5_seconds_triggers_resync`
   - Concern: Client's local time math diverges from server truth; must resync on poll if drift >5s
   
2. **Duplicate Start Requests Idempotent** (breakage)
   - File: `tests/test_feature_001_timer_authority.py::test_duplicate_start_with_different_durations_is_deterministic`
   - Concern: Network flake causes retry; backend must return same session, not create duplicate
   
3. **Server Timeout While Client Offline** (degradation)
   - File: `tests/test_feature_001_timer_authority.py::test_server_timeout_fires_while_client_offline`
   - Concern: Session must complete server-side even if client never polls; timeout is independent
   
4. **Completion Timestamp Precise at Transition** (silent-wrongness)
   - File: `tests/test_feature_001_timer_authority.py::test_completed_at_set_exactly_at_transition_moment`
   - Concern: completed_at must be exact to prevent downstream duration calculations being wrong

### Feature 002: Take a break (Break state machine & transitions)

5. **Break Duration from User Settings** (degradation)
   - File: `tests/test_feature_002_break_state_machine.py::test_break_duration_from_user_settings_not_hardcoded`
   - Concern: Break uses configured duration from Settings, not hardcoded default
   
6. **Skip Idempotent Across Timeout Race** (degradation)
   - File: `tests/test_feature_002_break_state_machine.py::test_skip_break_idempotent_across_race_with_timeout`
   - Concern: Skip and timeout firing simultaneously must not corrupt state; one must win
   
7. **History Records Configured Duration Not Actual** (silent-wrongness)
   - File: `tests/test_feature_002_break_state_machine.py::test_break_duration_recorded_in_history_is_configured_duration_not_actual`
   - Concern: Even if skipped instantly, history shows configured duration, not 0 elapsed

### Feature 003: Review today's sessions (Session history queries)

8. **History Strictly Descending by Completed_at** (degradation)
   - File: `tests/test_feature_003_history_boundaries.py::test_history_ordered_descending_by_completed_at_strictly`
   - Concern: Ordering must be stable across queries; no UI flicker
   
9. **Query Boundary Respects UTC Midnight** (degradation)
   - File: `tests/test_feature_003_history_boundaries.py::test_history_query_boundary_includes_sessions_at_since_timestamp`
   - Concern: Sessions completed yesterday evening (local) but early today (UTC) are included
   
10. **Empty History Returns Empty Array** (degradation)
    - File: `tests/test_feature_003_history_boundaries.py::test_empty_history_returns_empty_array_not_error`
    - Concern: New user with zero sessions gets [], not error; app doesn't crash on first launch

### Feature 004: Track statistics (Statistics aggregation)

11. **Week Boundaries Inclusive Both Ends** (silent-wrongness)
    - File: `tests/test_feature_004_statistics_temporal.py::test_week_boundary_is_inclusive_both_ends_in_utc`
    - Concern: Session at Sunday 23:59 UTC must be included; off-by-one breaks week totals
    
12. **Week Boundaries Respect UTC Not Local TZ** (silent-wrongness)
    - File: `tests/test_feature_004_statistics_temporal.py::test_week_boundary_respects_utc_not_local_timezone`
    - Concern: Elena (UTC-8) sees data aligned to UTC weeks, not her local perception
    
13. **Membership Duration Computed Server-side** (degradation)
    - File: `tests/test_feature_004_statistics_temporal.py::test_membership_duration_days_computed_server_side`
    - Concern: Server time used, not client time; protects against user clock skew

### Feature 005: Customize durations (Settings validation)

14. **Validation Enforces [1, 180] Bounds** (degradation)
    - File: `tests/test_feature_005_validation_and_idempotency.py::test_settings_validation_rejects_out_of_bounds_values`
    - Concern: 0 and 181 rejected; system accepts only valid durations
    
15. **Partial Update Preserves Omitted Fields** (degradation)
    - File: `tests/test_feature_005_validation_and_idempotency.py::test_partial_settings_update_doesnt_touch_omitted_field`
    - Concern: PATCH one field without resetting the other to default
    
16. **Active Session Unaffected by Settings Change** (degradation)
    - File: `tests/test_feature_005_validation_and_idempotency.py::test_active_session_duration_not_retroactively_changed`
    - Concern: Settings change doesn't retroactively extend/shrink active session
    
17. **Settings PATCH Idempotent** (degradation)
    - File: `tests/test_feature_005_validation_and_idempotency.py::test_settings_patch_is_idempotent`
    - Concern: Retry of same PATCH returns identical result, no side effects

### Feature 006: Understand tracking duration (Launch date & membership)

18. **Launch Date Immutable** (breakage)
    - File: `tests/test_feature_006_launch_date.py::test_launch_date_is_immutable_even_after_session_deletion`
    - Concern: Once set, launch_date never changes, even if all sessions deleted
    
19. **Launch Date is Exact Timestamp Not Midnight** (degradation)
    - File: `tests/test_feature_006_launch_date.py::test_launch_date_is_exact_timestamp_not_normalized_to_midnight`
    - Concern: Preserves second-level precision; days_tracked calculation depends on it
    
20. **New User Has Null Launch Date** (degradation)
    - File: `tests/test_feature_006_launch_date.py::test_new_user_with_zero_sessions_has_no_launch_date`
    - Concern: Not a placeholder date; null/omitted until first session completes

## Test Files Created

- `tests/test_feature_001_timer_authority.py` — 4 edge-case tests
- `tests/test_feature_002_break_state_machine.py` — 3 edge-case tests
- `tests/test_feature_003_history_boundaries.py` — 3 edge-case tests
- `tests/test_feature_004_statistics_temporal.py` — 3 edge-case tests
- `tests/test_feature_005_validation_and_idempotency.py` — 4 edge-case tests
- `tests/test_feature_006_launch_date.py` — 8 happy-path + 2 edge-case tests

**Total test functions:** 27 (including happy paths for Feature 006)
**All tests fail red** (no production code exists yet)

## Design Notes

**Scope discipline:** Each scenario is bounded to its feature's stack_span. System-wide invariants (e.g., "all sessions must reference valid user") are M6 (Caterpillar) territory. I'm testing the seams between components and the edge cases that constitute failure modes within a feature's boundary.

**Severity vocabulary:**
- **Breakage** (1 scenario): System stops working
- **Silent-wrongness** (7 scenarios): System appears to work but produces wrong output (most dangerous)
- **Degradation** (11 scenarios): System works but worse than promised

**Severity underclaimed.** Temptation exists to call some of these "breakage" to get attention; I'm resisting that. Underclaim if anything.

**Property-based form:** Where applicable, each scenario includes a property-based statement of what must be true for all inputs in that class. These form the test contract that M5 implementation must satisfy.

**Idempotency is load-bearing.** Multiple scenarios (2, 6, 17) test idempotent behavior because network flakes are guaranteed to happen. Every mutation endpoint must be safe to retry.

**Timezone is a seam.** Multiple scenarios (9, 12) test timezone handling because UTC vs. local is where systems break. The contract is: operate in UTC server-side; user's local timezone is frontend concern only.
