## Scenario 252: GET /notes returns timestamps in ISO8601 format with Z suffix (UTC)

**GUID:** 01KRY190Z3094B2DF4C3RP2H5E
**Severity:** silent-wrongness

**Setup:**

Kohl saves a note at 2024-03-15T14:32:45.123456 UTC.

**Trigger:**

Frontend calls GET /notes.

**Expected:**

GET /notes returns created_at and updated_at as ISO8601 strings with Z suffix: '2024-03-15T14:32:45.123456Z'.

**Concern:**

The to_dict() method on Note includes ensure_tz_aware(), which should return ISO8601 with Z suffix. But if SQLite or SQLAlchemy returns naive datetimes, the code assumes UTC. If the conversion is wrong, timestamps could be off by hours, breaking merge logic.

**Property:**

For all timestamps in GET /notes response, the format is ISO8601 with Z suffix, and the timezone is UTC.
