## Scenario 035: Leap second (Jun 30 2025): clock inserts 23:59:60 UTC, session at boundary

**Severity:** curiosity

**Setup:**

Leap second at UTC midnight (rare, IERS-announced). Derek's session completes at exactly 23:59:60 UTC. Phone supports; backend may not.

**Trigger:**

Timestamp '23:59:60' sent to backend.

**Expected:**

Backend normalizes or rejects. No crash. Session attributed to correct day.

**Concern:**

Delightful edge case. Most systems ignore leap seconds (extremely rare). But timestamp handling should be explicit.

**Property:**

Timestamp format unambiguous + supported by both ends. Leap seconds probably not in contract (unless NIST-grade).
