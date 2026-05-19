## Scenario 272: The audit trail includes revision_id and timestamp with sufficient precision to order saves chronologically

**GUID:** 01KRY19VMP015JW631HNJ74GC6
**Severity:** curiosity

**Setup:**

Two saves of the same note happen in rapid succession (within 1ms of each other on a fast machine).

**Trigger:**

Save 1 at wall-clock time 2026-05-18T17:13:21.123456Z, Save 2 at 2026-05-18T17:13:21.123789Z (663 microseconds later).

**Expected:**

The audit log has two entries with distinct timestamps (differing in the microsecond field). The revision_ids are distinct (because updated_at is part of the hash). Querying the audit log and sorting by timestamp produces the correct chronological order.

**Concern:**

If the timestamp in the audit log is only precise to seconds (or even milliseconds), two rapid saves might have the same timestamp, making the chronological order ambiguous. Or if the audit log stores timestamps in the database's default timezone rather than UTC, reconstructing the sequence requires timezone conversion.

**Property:**

For all audit log entries for the same note, the (timestamp, id) pair uniquely identifies the order of saves (where id is the audit log primary key, which auto-increments). Timestamps have microsecond precision and are stored in UTC.
