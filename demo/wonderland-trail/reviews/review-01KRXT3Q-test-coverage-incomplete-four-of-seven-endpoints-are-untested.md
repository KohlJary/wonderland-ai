## Review 010: Test coverage incomplete — four of seven endpoints are untested

**GUID:** 01KRXT3QP1KXYAN3TVS8RW3PNR
**Files reviewed:** tests/test_notes.py
**Verdict:** request-changes

### Findings

#### change-required: PUT, DELETE, GET list, and tag endpoints have zero test coverage
**Location:** tests/test_notes.py, missing tests
**Quote:**

```
Current tests cover: POST /api/notes (✓), GET /api/notes/{id} (✓). Missing: PUT /api/notes/{id}, DELETE /api/notes/{id}, GET /api/notes, POST /api/notes/{id}/tags, DELETE /api/notes/{id}/tags/{tag_id}.
```

**Read:** Ticket 010 acceptance criteria state: 'All endpoints are tested via pytest with at least happy-path + one error case per endpoint.' Five of seven endpoints ship with zero test coverage. PUT could fail to update tags, DELETE could fail to cascade, GET list could return wrong order, tag operations could be non-idempotent.
**Concern:** Untested code ships with unknown correctness. Common failure modes (PUT fails to update tags, DELETE orphans records, list returns wrong order, tag association fails) would be caught by tests but are currently invisible.
**Request:** Add tests for all seven endpoints: (1) test_put_note_title_only, test_put_note_tags_only, test_put_note_not_found, test_put_note_invalid_title. (2) test_delete_note_success, test_delete_note_not_found, test_delete_note_cascades_tags. (3) test_get_notes_empty_list, test_get_notes_reverse_chronological_order, test_get_notes_multiple. (4) test_associate_tag_success, test_associate_tag_creates_new_tag, test_associate_tag_not_found. (5) test_remove_tag_success, test_remove_tag_not_found. Each test verifies response shape and status code match contract.
