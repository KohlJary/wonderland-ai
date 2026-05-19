## Ticket 050: Tag key generation uses array index instead of stable tag ID

**GUID:** 01KRXY8N72Z4D9MTVGKMDB1MFA
**Sources:** kohl-organizes-notes-with-optional-tags, feature-005-kohl-organizes-notes-with-optional-tags
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``feature-005-kohl-organizes-notes-with-optional-tags`` (change-required):

**Concern:** Using index as part of a key is an anti-pattern in React. If a note's tags are updated (e.g., user removes 'research' from the middle of a 3-tag list), the remaining tags will be re-keyed and their DOM nodes will be torn down and recreated, causing loss of focus, animation state, or other node-associated state. More importantly, the code has access to `tag_ids`, which are stable identifiers — using them would be correct.

**Request:** Use `tag_ids` instead of array index for the key. You'll need to modify the Note interface to include a parallel `tag_ids` array with the same order as `tag_names`, then use `key={`tag-${note.tag_ids[index]}`}`. Alternatively, if tag_ids and tag_names are not guaranteed to be in the same order, refactor to iterate over tag_ids with a lookup into tag_names.

**Location:** ``frontend/src/NoteList.tsx:99``

**Acceptance:**
- Use `tag_ids` instead of array index for the key. You'll need to modify the Note interface to include a parallel `tag_ids` array with the same order as `tag_names`, then use `key={`tag-${note.tag_ids[index]}`}`. Alternatively, if tag_ids and tag_names are not guaranteed to be in the same order, refactor to iterate over tag_ids with a lookup into tag_names.
