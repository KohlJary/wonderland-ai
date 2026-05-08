## Scenario 016: Break completion event is logged for daily review (feature 003 integration)

**Severity:** degradation

**Setup:**

A break session completes (timeout or skip). Break has duration_seconds=300.

**Trigger:**

Break session reaches status='completed'.

**Expected:**

An event is logged with at least: event_type or completion_type, session_id, duration_seconds, elapsed_ms. This event will be consumed by feature 003 to count completed/skipped breaks in daily review.

**Concern:**

Feature 003 depends on break completion events, but event schema is defined in feature 003 contract. If the logging mechanism differs between focus and break, feature 003 will fail. Cross-feature seam risk.

**Implies:**
- Implies feature 003 must define event schema before break logging is tested
- Implies feature 003 test to verify break events are captured
