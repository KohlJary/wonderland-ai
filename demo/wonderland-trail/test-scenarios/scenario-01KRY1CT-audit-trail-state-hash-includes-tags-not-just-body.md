## Scenario 331: Audit trail state hash includes tags, not just body

**GUID:** 01KRY1CT9RYR088A6WTPTNAHTD
**Severity:** silent-wrongness

**Setup:**

Kohl saves a note with title "research", body "methods", tags ["ML"]. The revision_id = hash(saved_state). Later, she edits by removing the tag (body and title unchanged) and saves again with tags [].

**Trigger:**

The second save completes. The new revision_id is returned.

**Expected:**

The two revision_ids are different, because the saved states differ (one has tags, one doesn't). Collision detection can distinguish 'note with ML tag' from 'note without tags' based on revision_id.

**Concern:**

The implementation might hash only the body (or title+body) and ignore tags. Both saves produce the same revision_id even though the states differ. Collision detection fails to detect the tag change, and Tab A might silently overwrite Tab B's tag removal.

**Property:**

The revision_id (hash of saved_state) includes all mutable fields: title, body, tag_ids. Removing, adding, or modifying a tag changes the revision_id. Two saved states that differ in any mutable field have different revision_ids.

**Implies:**
- Hash must include: title, body, tag_ids (and their exact values)
- Hash must not include: id, created_at, updated_at (immutable or server-generated)
- Definition of 'saved_state' for hashing is critical: must include exactly the fields the user intends to persist
