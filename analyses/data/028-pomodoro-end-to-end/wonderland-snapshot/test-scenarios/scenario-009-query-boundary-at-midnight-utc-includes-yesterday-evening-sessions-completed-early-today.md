## Scenario 009: Query boundary at midnight UTC includes yesterday evening sessions completed early today

**Severity:** degradation

**Setup:**

James (UTC-8) starts session 11 PM local (7 AM UTC next day). Completes 11:05 PM local (7:05 AM UTC next day). Queries since_timestamp=today_utc_midnight.

**Trigger:**

Backend applies filter in UTC.

**Expected:**

Session appears because completed_at >= since_timestamp (both in today UTC).

**Concern:**

If query uses local timezone, boundary misaligned. Session filtered out incorrectly.

**Property:**

For all completed sessions with completed_at >= since_timestamp_utc, session appears in /sessions/history?since_timestamp=...
