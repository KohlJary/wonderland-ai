## Test Scenario 003: History Query and Statistics Invariants

**Feature:** View session history and statistics (feature-003)
**Persona:** Technical — invariant validation, not persona-driven
**Stack span:** backend
**Severity:** high

**Concern:**

The history and statistics queries depend on invariants that affect reliability of user-facing reports:

- Date boundaries are UTC midnight on the backend (frontend normalizes local midnight)
- Date range boundaries are inclusive on both ends (from_date and to_date both inclusive)
- Pagination handles concurrent inserts without duplicates or skipped records (cursor-based, not offset-limit)
- Stats aggregation handles zero-session cases (no divide-by-zero)
- Stats accuracy across date boundaries is correct (session counted in the day it started)

These constraints ensure the user's history reflects reality without race conditions or boundary bugs.

**Test Coverage:**

Implemented in `tests/test_feature_003_edge_cases.py`:

- `test_today_query_uses_utc_midnight_boundaries` — enforces UTC boundary semantics
- `test_date_range_query_boundaries_are_inclusive` — ensures inclusive boundaries
- `test_pagination_handles_concurrent_inserts` — validates cursor-based pagination robustness
- `test_stats_aggregation_with_no_sessions` — handles empty result sets gracefully
- `test_stats_accuracy_across_multiple_days` — validates date grouping and counting

**Failure Mode Anticipated:**

History queries could fail if:
- Boundary bugs exclude sessions on the exact start/end date
- Pagination uses offset-limit (vulnerable to concurrent inserts causing duplicates)
- Stats calculation divides by zero or crashes on empty sets
- Date grouping is off-by-one (session counted in wrong day)
- Timezone assumptions differ between frontend and backend

If any of these occur, the user's history becomes untrustworthy or misleading.

**When This Test Passes:**

History queries are accurate, pagination is robust to concurrent changes, and stats reflect the actual session data.
