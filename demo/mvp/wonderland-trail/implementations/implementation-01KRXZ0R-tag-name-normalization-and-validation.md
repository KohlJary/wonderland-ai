## Implementation 047: Tag name normalization and validation

**GUID:** 01KRXZ0RMYXZHF7GB0NS6ZXGRX
**Side:** backend
**Ticket:** ticket-01KRXYNM-whitespace-only-tag-names-accepted-and-stored-without-normalization
**Contract:** contract-note-01KRXYD0 (tag-name-normalization-and-validation-semantics, agreed v1): (1) Strip leading/trailing whitespace from all tag_names on input before validation or database write. (2) Reject (400 Bad Request) any tag_name that after stripping is empty string or whitespace-only. (3) Deduplicate tag_names within a single request (case-sensitive: ['research', 'research'] → ['research'], but ['research', 'Research'] → both). (4) Store tag names in normalized form (whitespace-stripped). (5) Case-sensitive: do NOT normalize case.
**Ready for review:** yes

**Approach:**

Added _normalize_and_validate_tag_names() helper that strips whitespace, rejects empty/whitespace-only tags (400 Bad Request), and deduplicates case-sensitively. Applied to both _associate_tags() and associate_tag() endpoints. Tags are now stored in normalized form.

**Invariants Enforced:**
- tag_names in requests are normalized (whitespace-stripped) before any processing: validation, storage, or lookup
- empty or whitespace-only tag names are rejected at request boundary (400 Bad Request), never persisted
- tag_names are deduplicated case-sensitively within a single note: ['research', 'research'] → one tag; ['research', 'Research'] → two tags
- tags are stored in normalized form (leading/trailing whitespace removed); no tag exists with raw leading/trailing whitespace

**Schema Changes:**

None; normalization happens in application code, not database. Tag.name column already exists with TEXT type; no migration required. Backward-compatible: existing tags with whitespace (if any) remain as-is; new/updated notes will have normalized tags.

**Failure Modes Handled:**
- Empty tag after stripping whitespace: 400 Bad Request (fail fast at endpoint, prevents downstream processing)
- Whitespace-only tag: 400 Bad Request (same as empty)
- Duplicate tag names in request: deduplicated and stored as one tag (case-sensitive comparison)

**Files:**
- src/backend/api/notes.py: added _normalize_and_validate_tag_names() helper function (lines 154-176); refactored _associate_tags() to call it (lines 179-202); refactored associate_tag() to normalize input (lines 306-325)

**Open Questions for Pair:**
- Frontend validation: should client-side validation mirror the server rules exactly (strip whitespace, reject empty), or is the server rejection sufficient? Per contract, client should validate too — confirm Tweedledee is enforcing this.

**Known Limitations:**
- Test environment cannot run pytest (fastapi import failure); code is syntactically valid but needs environment fix to verify test pass. Blocking: test_tag_names_with_whitespace_only_entries, test_post_associate_tag_with_whitespace_in_name expect 400 rejection; test_tag_names_case_sensitivity_deduplication expects three distinct tags. All tests updated to enforce contract.
