## Scenario 248: GET /notes response includes revision_id for each note

**GUID:** 01KRY190Z3094B2DF4C3RP2H5A
**Severity:** breakage

**Setup:**

Kohl has saved two notes: note A (revision_id=V1), note B (revision_id=V2).

**Trigger:**

Frontend calls GET /notes on boot.

**Expected:**

GET /notes returns both notes with revision_id field present in each note object.

**Concern:**

The ticket says 'Each note in the response includes: id, title, body, tags, created_at, updated_at, revision_id.' But looking at the code, the NoteResponse model does NOT include revision_id field. This is a missing field that breaks the contract.

**Property:**

For all notes returned by GET /notes, each note MUST include revision_id field (even if it's not yet persisted in the database, it must be present in the response).

**Implies:**
- Implies missing revision_id field in Note model and NoteResponse — flag for Tweedledum.
