## Scenario 163: POST /notes with tag_names containing whitespace-only entries like ['research', '  ', 'experiment']

**GUID:** 01KRXXYQD08R1GFPSWEN11326W
**Severity:** degradation

**Setup:**

Request: {"title": "Test", "tag_names": ["research", "  ", "experiment"]}.

**Trigger:**

POST /api/notes with the above.

**Expected:**

Request is rejected (validation error), or whitespace is stripped and degenerate tag is not created.

**Concern:**

NoteCreate has no per-item validation on tag_names (no min_length on list items, no strip). A string '  ' (three spaces) passes validation as a valid tag name (length 3, non-empty per Pydantic). The Tag model has no validation either. _associate_tags creates a tag named '  ' in the database. Users see a blank tag in their UI.

**Property:**

All tag names are non-empty and non-whitespace after normalization.

**Implies:**
- Implies input validation tightening on tag_names list items — flag for Tweedles.
