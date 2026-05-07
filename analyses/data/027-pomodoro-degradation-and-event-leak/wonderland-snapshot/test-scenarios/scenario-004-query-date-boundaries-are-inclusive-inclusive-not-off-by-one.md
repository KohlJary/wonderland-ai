## Scenario 004: Query date boundaries are inclusive-inclusive, not off-by-one

**Severity:** degradation

**Setup:**

Query for calendar day 2024-01-16. Sessions created at: 00:30 (just after midnight), 14:00 (afternoon), 23:59:59 (just before midnight).

**Trigger:**

GET /sessions?fromDate=2024-01-16&toDate=2024-01-16 (single calendar day query).

**Expected:**

All three sessions returned. Date boundaries inclusive at both ends: [00:00:00, 23:59:59.999] on that calendar day.

**Concern:**

Backend interprets boundaries as precise wall-clock times: [00:00 UTC, 00:00 UTC) (empty). Or treats toDate as exclusive (off-by-one). Or doesn't account for timezones, does math in UTC. Degradation: user sees zero sessions for a day they worked, or sessions from wrong day.

**Property:**

For all date-range queries: fromDate/toDate are calendar dates (inclusive both ends), converted to [YYYY-MM-DDTXX:XX:XX local, YYYY-MM-DDTXX:XX:XX+23:59:59 local], then to UTC for database comparison.

**Implies:**
- Query parsing: dates converted to timezone-aware boundaries before querying — flag for Tweedledum.
- Timezone awareness: backend must know user's timezone to compute correct boundaries — flag for contract.
- Test data: cover day boundaries with timezone mismatches — flag for test harness.
