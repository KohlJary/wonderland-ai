## Scenario 215: Concurrent searches by two users: search modifies note state or sorting order

**GUID:** 01KRXYEG9WMJ0GPZ2FAHJSYB4Z
**Severity:** silent-wrongness

**Setup:**

User A searches for 'test'. While User A is reading results, User B adds a note matching 'test'. Search response is built as a list; if sorting happens during iteration, result order may be inconsistent.

**Trigger:**

GET /api/notes/search?q=test from User A; concurrent note creation by User B

**Expected:**

User A sees results consistent with the state at the start of the search (snapshot semantics), or sees a disclaimer that results may include new notes added during search.

**Concern:**

If the backend builds the result list by iterating over notes and appending matches, and the notes table is modified during iteration, the result set may be incomplete, duplicated, or out of order. Silent wrongness because the response looks valid but is subtly wrong.

**Property:**

For all concurrent search operations, the response must be either a consistent snapshot of the database state at T0, or must clearly indicate that later-added notes may appear.
