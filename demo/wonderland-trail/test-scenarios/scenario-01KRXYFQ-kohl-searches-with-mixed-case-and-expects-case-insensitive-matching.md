## Scenario 229: Kohl searches with mixed case and expects case-insensitive matching

**GUID:** 01KRXYFQH721FMRYBB1WJJ1A0F
**Severity:** silent-wrongness

**Setup:**

Kohl has notes with 'Experiment', 'EXPERIMENT', and 'experiment' in various places. She opens search.

**Trigger:**

Kohl types 'ExPerIMent' (mixed case) into the search input.

**Expected:**

All three variations are found because search is case-insensitive. Results show all matching notes.

**Concern:**

If case sensitivity leaks through, Kohl has to remember the exact capitalization she used, which is frustrating and violates her mental model of search.

**Property:**

Case-insensitive substring search treats mixed-case queries as lowercase for matching.
