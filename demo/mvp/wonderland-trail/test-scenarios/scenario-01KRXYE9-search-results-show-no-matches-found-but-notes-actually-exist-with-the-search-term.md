## Scenario 209: Search results show 'No matches found' but notes actually exist with the search term

**GUID:** 01KRXYE929PR8CE0PNGR2QFKHQ
**Severity:** silent-wrongness

**Setup:**

Kohl has a note with title 'Gradient Scaling Ablation'. She searches for 'gradient'. The backend search endpoint uses case-insensitive ILIKE matching, which should find the note.

**Trigger:**

Search is submitted. Backend returns empty results [].

**Expected:**

The search result includes the note ('Gradient Scaling Ablation' matches 'gradient' case-insensitively).

**Concern:**

If the backend search is case-sensitive by mistake, or if the search index is not synced with the database (e.g., FTS5 index is stale after note creation), the backend returns no results even though the note exists. Frontend displays 'No matches found'. Kohl believes her note doesn't exist, when in fact it does.

**Property:**

For all searches Q and existing notes N whose title or body contains Q (case-insensitive), the backend returns N in the results list.

**Implies:**
- Implies backend concern: Verify that search uses case-insensitive matching (ILIKE or lower() comparison) and that full-text index is re-indexed on every note write (CRUD endpoints must update FTS5 index). Flag for Tweedledum.
