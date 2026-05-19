## Scenario: Audit trail state hash includes tags, not just body

**Severity:** silent-wrongness

**Setup:**
Kohl saves a note with title "research", body "methods", tags ["ML"]. The revision_id = hash(saved_state). Later, she edits the note by removing the tag (body and title unchanged). She saves again with title "research", body "methods", tags []. The new revision_id is computed.

**Trigger:**
The second save completes. The new revision_id is returned to the client.

**Expected:**
The two revision_ids are different, because the saved states differ (one has tags, one doesn't). The audit_log has two entries with distinct revision_ids. The collision detection logic (or any client trying to validate state) can distinguish "note with ML tag" from "note without tags" based on revision_id.

**Concern:**
The implementation might hash only the note's body (or title + body) and ignore tags. In this case:
- First save: title="research", body="methods", tags=["ML"] → revision_id = hash("research" + "methods")
- Second save: title="research", body="methods", tags=[] → revision_id = hash("research" + "methods")
- Both revision_ids are identical, even though the states differ

Later, if Tab A loads the note (gets revision_id = hash1) and Tab B saves with tags removed (saves revision_id = hash1), Tab A's next save attempt will not detect a collision (because the revision_ids match), even though the tag state changed. Tab A might then re-add the ML tag, overwriting Tab B's removal, silently losing data.

**Property:**
The revision_id (hash of saved_state) includes all mutable fields: title, body, tag_ids. Removing, adding, or modifying a tag changes the revision_id. Two saved states that differ in any mutable field have different revision_ids.

**Implies:**
- Hash must include: title, body, tag_ids (and their exact values, not just counts)
- Hash must not include: id, created_at, updated_at (immutable or server-generated, not part of user's save)
- Definition of "saved_state" for hashing is critical: must include exactly the fields the user intends to persist
