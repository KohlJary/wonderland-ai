## Scenario 014: Kohl adds a tag, then deletes it before saving — the tag is not persisted

**GUID:** 01KRXT99M7QSR234FW4T0095TV
**Severity:** silent-wrongness

**Setup:**

The editor has a note with title and body. Kohl adds the tag 'draft', then immediately removes it by clicking the X.

**Trigger:**

Kohl clicks Save.

**Expected:**

The note is persisted to the backend with an empty tag list (or no tags field). The backend response confirms tag_names: []. No 'draft' tag exists in the backend.

**Concern:**

If the tag-removal action doesn't update the tag list before save, the tag is silently persisted despite being removed from the UI. Kohl thinks she removed it; the backend says it exists. Silent wrongness.

**Property:**

Tag removal before save is honored atomically
