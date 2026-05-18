## Scenario 211: Empty query returns notes but user has no notes yet

**GUID:** 01KRXYEG9WMJ0GPZ2FAHJSYB4V
**Severity:** curiosity

**Setup:**

Fresh user account with zero notes in storage.

**Trigger:**

GET /api/notes/search?q= (empty string)

**Expected:**

Endpoint returns empty JSON array [] with 200 status.

**Concern:**

Acceptance says 'Empty query returns all notes in storage order.' If we return empty array on empty query, is that correct, or should we return 400 'query required'? The ticket doesn't specify the semantics of empty.

**Property:**

For all query strings Q (including empty string), the endpoint must return a valid JSON array.

**Implies:**
- Implies story underspecification — flag for Alice: does search UI allow empty query submission, or does the frontend prevent it?
