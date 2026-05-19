## Contract Note 000: tag-browsing-endpoint-response-shape

**GUID:** 01KRY0A8ZQFT8R5KZPGPX0YS8W
**State:** agreed
**Contract Version:** tag-browsing-endpoint-get-tags-id-notes-v1

**Current Shape:**

GET /tags/{tag_id}/notes

**Proposed Change:**

New endpoint serving notes filtered by tag. Response shape:

```json
{
  "results": [
    {
      "id": int,
      "title": str,
      "body": str,
      "tag_names": [str],
      "tag_ids": [int],
      "created_at": ISO8601,
      "updated_at": ISO8601,
      "revision_id": str
    }
  ],
  "total_results": int,
  "page": int,
  "page_size": int,
  "has_more": bool
}
```

**Source:** feature-009-kohl-drafts-and-saves-experimental-notes-with-persistent-backup (tag browsing in note list view)

**Frontend Impact (Tweedledee):**

All three proposed design choices confirmed:

1. **Body always non-null:** Yes. Backend guarantees body is never NULL (defaults to empty string ""). SQLite schema enforces this; the Note model has body = Column(Text, nullable=False, default=""). Safe assumption for frontend.

2. **Pagination cap:** Yes. Implementing with default 20 per page, max 100 per page. Matches existing GET /api/search pagination contract (both use same bounds). Prevents DOS via page_size=999999.

3. **Full tag list:** Yes. All tags on each note will be returned. Matches pattern from existing GET /api/notes/{id} and GET /api/search endpoints (both return full tag list, not a subset). Frontend can render whatever it needs.

**Backend Impact (Tweedledum):**

All three assumptions are feasible and align with existing backend infrastructure:

- Query shape: `SELECT notes WHERE notes.id IN (SELECT note_id FROM note_tags WHERE tag_id = ?)`
- Ordering: updated_at DESC, then id DESC for determinism
- Pagination: 1-indexed pages, per_page offset/limit applied per contract
- Error semantics: 404 if tag_id doesn't exist (no empty results on missing tag)
- Body handling: never truncated server-side; frontend truncates for display if needed
- Revision_id: computed per existing contract (ticket-081 documents future caching plan)

**No breaking changes to existing contracts.** This is a new endpoint, doesn't modify existing POST/GET/PUT/DELETE semantics or response shapes.

**Resolution:** Agreed. Both sides have confirmed the design. Backend will implement GET /tags/{tag_id}/notes with this response shape. Ready for implementation.

**Resolution:**

Agreed. Both sides have confirmed the design...
