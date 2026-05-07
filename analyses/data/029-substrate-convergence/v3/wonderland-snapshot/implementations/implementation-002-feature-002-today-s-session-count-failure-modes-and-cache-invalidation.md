## Implementation 002: Feature 002: Today's session count failure modes and cache invalidation

**Side:** frontend
**Ticket:** Feature-002: Review today's session count at a glance
**Contract:** contract-note-004 (GET /api/session-counts/today returns {count, total_focus_minutes}; always-fresh query, indexed by completed_at; frontend caches with midnight reset)
**Ready for review:** no

**Approach:**

Test file encodes 15+ failure-mode scenarios covering: midnight boundary handling (off-by-one date errors), count aggregation correctness (focus-only, not breaks), cache validity and backend freshness (no backend caching), response format consistency (both count and total_focus_minutes always present), and performance with large history. Tests verify the count query is indexed and that backend always returns current state.

**Client State:**

Frontend cache strategy (fetch on startup, increment on completion, reset at midnight, re-fetch on app-return-to-foreground) is specified in contract-note-004; these tests verify backend provides the fresh data.

**Files:**
- tests/test_feature_002_failure_modes.py: 12.9KB of 6 test classes with 15 scenarios

**Known Limitations:**
- Midnight boundary tests require time mocking to test precisely.
- Performance tests with large datasets (100k+ records) may need separate load-testing harness.
- Frontend cache invalidation logic is beyond backend scope; frontend tests should be in Jest.
