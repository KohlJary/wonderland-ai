## Scenario 164: POST /notes with tag_names=['research', 'Research', 'RESEARCH'] (case-sensitivity deduplication)

**GUID:** 01KRXXYQD08R1GFPSWEN11326X
**Severity:** curiosity

**Setup:**

Request with tag names differing only in case.

**Trigger:**

POST /api/notes with tag_names=['research', 'Research', 'RESEARCH'].

**Expected:**

Either: (a) one tag is created (case-insensitive), or (b) three tags are created (case-sensitive). Current code deduplicates on exact string match, so three tags are created.

**Concern:**

The deduplication in _associate_tags uses 'if tag_name not in seen' (exact string match). 'research' and 'Research' are different, so both are inserted into the tags table. Three rows are created. Users might expect 'research' and 'Research' to be the same tag.

**Property:**

Tag name deduplication follows consistent case-sensitivity semantics (either all case-sensitive or all case-insensitive).

**Implies:**
- Implies a contract clarification: are tags case-sensitive or not? — flag for Alice and Cat.
