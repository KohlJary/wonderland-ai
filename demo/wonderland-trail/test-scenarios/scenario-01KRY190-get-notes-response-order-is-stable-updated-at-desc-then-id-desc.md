## Scenario 251: GET /notes response order is stable: updated_at DESC, then id DESC

**GUID:** 01KRY190Z3094B2DF4C3RP2H5D
**Severity:** degradation

**Setup:**

Database contains three notes: A (updated_at=T, id=1), B (updated_at=T, id=3), C (updated_at=T, id=2) — all with the same timestamp.

**Trigger:**

Frontend calls GET /notes.

**Expected:**

GET /notes returns notes in order B (id=3), C (id=2), A (id=1) — secondary sorted by id DESC when timestamps tie.

**Concern:**

The code uses .order_by(Note.updated_at.desc(), Note.id.desc()), which is correct. But if two notes have the EXACT same timestamp (to the microsecond), the order is deterministic only if the secondary sort applies. This is correct behavior, but I want to verify it holds under concurrent saves.

**Property:**

For any two notes with equal updated_at, the one with higher id appears first in the response.
