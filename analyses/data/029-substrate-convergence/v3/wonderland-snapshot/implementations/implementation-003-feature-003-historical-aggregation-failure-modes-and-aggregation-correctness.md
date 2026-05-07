## Implementation 003: Feature 003: Historical aggregation failure modes and aggregation correctness

**Side:** frontend
**Ticket:** Feature-003: Inspect historical session data across weeks and all-time
**Contract:** contract-note-006 (GET /api/session-history/{weekly|all-time} returns {period, data: [{date (ISO8601), session_count, total_focus_duration_minutes, break_duration_minutes}]}; newest-first order; UTC dates in v1; optional zero-count days per endpoint type)
**Ready for review:** no

**Approach:**

Test file encodes 25+ failure-mode scenarios covering: zero-count day handling (sparse data), date ordering (newest-first), aggregation accuracy (no double-counting, correct sums), timezone limitations (v1 uses UTC), empty and large dataset handling, response format consistency (period, data array, per-day fields), date boundary conditions (year boundaries, leap years, DST transitions), and multi-day aggregation correctness.

**Client State:**

Frontend caching strategy: weekly fetches every 5 min + on app-return-to-foreground + midnight reset; all-time fetches once per session with user-driven refresh only. Tests verify backend provides correct sorted, aggregated data.

**Files:**
- tests/test_feature_003_failure_modes.py: 19.5KB of 9 test classes with 25 scenarios

**Open Questions for Pair:**
- Zero-count days: contract says weekly 'may omit' but should clarify if we include them. Test scenarios as optional.
- Timezone limitation (UTC v1): should add note in implementation artifact that this will be fixed in v1.1.

**Known Limitations:**
- DST and leap-year tests are low-priority for v1 but documented for completeness.
- All-time pagination is deferred per contract; tests as skip.
- Large dataset performance tests (10k+ records) may need dedicated load-test harness.
