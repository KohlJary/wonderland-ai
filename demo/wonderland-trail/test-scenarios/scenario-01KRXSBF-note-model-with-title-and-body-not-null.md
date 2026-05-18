## Scenario 002: Note model with title and body NOT NULL

**GUID:** 01KRXSBF5S803EBBPVQ3MVFZ1J
**Severity:** silent-wrongness

**Setup:**

Note table exists with schema that marks title and body as required

**Trigger:**

Attempt to insert a Note with title=NULL (e.g., via raw SQL or ORM layer if validation is bypassed)

**Expected:**

Database rejects the insert with a NOT NULL constraint violation

**Concern:**

If nullable=False is not set on the SQLAlchemy columns, the ORM will allow NULL values to be inserted. But the frontend and endpoints (tickets 011, 012) will assume title and body are always present. This is the worst class of bug — the system accepts data it shouldn't, then downstream code fails in confusing ways.
