## Implementation 006: Request field rename: tag_ids → tag_names

**GUID:** 01KRXSYVJ71X0T692PYKBT3FM3
**Side:** backend
**Ticket:** request-field-mismatch-tag-ids-vs-tag-names
**Contract:** contract-note-001/v1 + contract-note-004/v1: POST /notes {title, body?, tag_names?: str[]}; PUT /notes/{id} {title?, body?, tag_names?: str[]}. Response continues to return tags as list of strings (per current to_dict() implementation), pending follow-on work on response shape.
**Ready for review:** yes

**Approach:**

Updated Pydantic request models (NoteCreate, NoteUpdate) to use field name `tag_names: list[str]` instead of `tag_ids`. All endpoint handlers now reference `payload.tag_names` instead of `payload.tag_ids`. Module docstring updated to reflect correct contract shape. Tests updated to send tag_names in request bodies.

**Invariants Enforced:**
- tag_names field contains non-empty strings (validated by Pydantic Field constraints and _associate_tags logic)
- tag names are auto-created on first reference (idempotent per schema)
- tag association is atomic — all tag operations in a single POST/PUT are transactional

**Schema Changes:**

None — this is a request shape rename only, no schema migration required.

**Failure Modes Handled:**
- Empty tag_names: accepted (defaults to empty list)
- Invalid tag_name (exceeds length): caught by Pydantic validation before DB operation
- Tag name conflict: backend auto-creates tags by name, so name conflicts are idempotent (same name → same tag row)

**Files:**
- src/backend/api/notes.py: module docstring (2 lines), NoteCreate class (1 field + docstring), NoteUpdate class (1 field), create_note handler (1 ref), update_note handler (1 ref)
- tests/test_notes.py: test_post_note_with_tags (1 field), test_post_note_with_body_and_tags (1 field)

**Known Limitations:**
- Response shape mismatch deferred: Contract Note 004 specifies response should include {tag_names: [string], tag_ids: [integer]}, but current implementation returns tags as simple list of strings. This is accepted for v1 per Tweedledee's design choice (frontend preference for simpler response), pending formalization in a separate contract note if needed.
