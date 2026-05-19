## Scenario 009: Kohl saves a note, and the timestamps are generated server-side — not by the client

**GUID:** 01KRXSC2B76HKK0C1NK7MRJY5Y
**Severity:** degradation

**Setup:**

Kohl's browser is set to a different timezone than the server (e.g., client is UTC-8, server is UTC+0). She saves a note with title='Test'. The editor did not set any timestamp fields; they are empty/null in the POST body.

**Trigger:**

The backend receives POST /api/notes with {title: 'Test', body: '', tag_names: []} (no created_at or updated_at fields). The backend inserts the row and sets created_at and updated_at to the server's current time.

**Expected:**

The response returns {id: 4, title: 'Test', body: '', created_at: '2024-01-15T18:30:00Z', updated_at: '2024-01-15T18:30:00Z'} in ISO8601 (UTC). When Kohl retrieves this note later, the timestamps match the server's clock, not her browser's clock. If she saves the same note again (PATCH /api/notes/{id}), only updated_at changes; created_at remains unchanged.

**Concern:**

If the schema allows the client to submit created_at/updated_at, or if the backend doesn't set these fields, Kohl's timestamps will be inconsistent (some from her timezone, some from server, some missing). This breaks audit trails and makes sorting by date unreliable (degradation, not breakage, because the app still works but time ordering is wrong).

**Property:**

created_at and updated_at are set server-side on every insert and update; clients do not provide these values.

**Implies:**
- POST /api/notes request body does not include created_at or updated_at
- Backend sets created_at = NOW() on insert, updated_at = NOW() on insert and on every PATCH
- Response always includes both timestamps in ISO8601 UTC format
- created_at is immutable (never changes after insert); updated_at changes on every write
