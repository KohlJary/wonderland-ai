## Test Scenario 002: Session duration integrity and boundary validation

**Feature:** Feature 001 (Start, run, complete focus session)
**Severity:** silent-wrongness

### Setup

A session started at 09:00:00 UTC with 25-minute duration. The timer is firing at exactly 09:25:00 UTC (1500 seconds later). Backend receives session completion request at that moment.

### Trigger

Client sends session completion request with start_time=09:00:00, duration_seconds=1500, end_time=09:25:00.

### Expected

Backend persists the session with end_time=09:25:00, duration_seconds=1500. History queries will show the session in full. The recorded duration matches the actual elapsed time.

### Concern

If the backend doesn't validate the duration_seconds field against (end_time - start_time), a malicious or buggy client could claim a session was 25 minutes when it was actually 5 seconds. This is **silent wrongness**: history looks right but the data is corrupted. Users would see inflated session counts and total focus time.

### Property

For all session records S, |duration_seconds - (end_time - start_time).total_seconds()| < 1 (tolerance for rounding).

### Implies

- **Backend validation**: Validate duration_seconds on every session POST; reject if it doesn't match (end_time - start_time) within tolerance.
