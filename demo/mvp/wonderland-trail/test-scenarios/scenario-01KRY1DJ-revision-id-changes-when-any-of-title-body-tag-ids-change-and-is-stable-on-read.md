## Scenario 338: revision_id changes when any of [title, body, tag_ids] change, and is stable on read

**GUID:** 01KRY1DJHRX8TH9EM6XEXWJ9BF
**Severity:** degradation

**Setup:**

Note with title='Rust', body='async/await', tag_ids=[1, 3], updated_at='2025-01-18T14:30:00Z', revision_id='hash_A'.

**Trigger:**

(1) Fetch (no modifications). (2) Update body. (3) Update title. (4) Update tag_ids. (5) Fetch again (no modifications).

**Expected:**

(1) revision_id='hash_A' (read does not compute new hash). (2) revision_id changes to 'hash_B'. (3) revision_id changes to 'hash_C'. (4) revision_id changes to 'hash_D'. (5) revision_id='hash_D' (stable).

**Concern:**

If hash is computed from wrong fields (includes created_at, excludes body), collision detection breaks. If hash is re-computed on every read, same note appears to change every fetch, breaking collision detection entirely.

**Property:**

revision_id(note) is a pure function of exactly [title, body, sorted_tag_ids, updated_at]. No other fields included. If any of these four change, revision_id must change. If none change, revision_id must stay same.

**Implies:**
- Implies code: document which fields are in the hash: title, body, tag_ids (sorted), updated_at only.
- Implies code review: verify hash does not include created_at, id, or random values.
