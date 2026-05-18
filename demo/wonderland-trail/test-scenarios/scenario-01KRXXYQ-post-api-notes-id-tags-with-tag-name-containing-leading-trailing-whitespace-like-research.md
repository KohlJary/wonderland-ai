## Scenario 168: POST /api/notes/{id}/tags with tag_name containing leading/trailing whitespace like '  research  '

**GUID:** 01KRXXYQD08R1GFPSWEN113271
**Severity:** degradation

**Setup:**

Request with tag_name='  research  ' (spaces before and after).

**Trigger:**

POST /api/notes/{id}/tags with the above.

**Expected:**

Whitespace is stripped (tag stored as 'research'), or request is rejected.

**Concern:**

TagCreate.tag_name has min_length=1 but no strip(). The string '  research  ' (length 13) is accepted. The tag '  research  ' is created, distinct from 'research'. Users see a tag with invisible spaces.

**Property:**

Tag names are whitespace-normalized (leading/trailing spaces stripped) before storage.

**Implies:**
- Implies input validation on tag_name normalization — flag for Tweedles.
