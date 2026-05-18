## Scenario 250: GET /notes/{id} single-note fetch also scales efficiently

**GUID:** 01KRY190Z3094B2DF4C3RP2H5C
**Severity:** degradation

**Setup:**

Kohl opens a note from the list and the frontend wants to fetch just that note by id.

**Trigger:**

Frontend calls GET /notes/{id}.

**Expected:**

GET /notes/{id} returns the single note with all tags eagerly loaded in a single or two queries, not N queries.

**Concern:**

Same N+1 risk as /notes endpoint. If tags relationship is lazy-loaded, accessing note.tags in to_dict() will trigger a query.

**Property:**

GET /notes/{id} must complete in constant time (at most 2 queries).

**Implies:**
- Implies same eager-loading optimization needed as /notes.
