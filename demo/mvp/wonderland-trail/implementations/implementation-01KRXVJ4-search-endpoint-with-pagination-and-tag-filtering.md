## Implementation 016: Search endpoint with pagination and tag filtering

**GUID:** 01KRXVJ49KXXY411VNM30Q7FBP
**Side:** backend
**Ticket:** backend-search-endpoint-for-notes-by-title-and-content
**Contract:** search endpoint v1 (GET /api/search with query, tags, page, limit params; SearchResponse envelope with results, total, page, limit, has_more)
**Ready for review:** yes

**Approach:**

Added GET /api/search endpoint that builds a SQLAlchemy query with optional text search filter (ilike on title OR body) and tag filtering (any() for AND-joined tag matching). Applies LIMIT/OFFSET pagination with total count computed before pagination. Results ordered by updated_at DESC, id DESC for determinism.

**Invariants Enforced:**
- Text search is case-insensitive (SQLAlchemy ilike with %pattern% wildcards)
- Tag filtering uses AND logic: note must have ALL specified tags (via repeated Note.tags.any() filters)
- Pagination is well-bounded: limit capped at 100, page ≥0, offset computed as page * limit
- Total count reflects all matches in database, not just current page results
- Results ordered deterministically (updated_at DESC, id DESC) across pagination boundaries

**Schema Changes:**

None. Search uses existing Note, Tag, note_tags tables and associations.

**Failure Modes Handled:**
- Empty query: returns all notes (no text filter applied)
- Page beyond results: returns empty results array with has_more=false, total=correct count
- Invalid tag name in filter: returns no matches (Note.tags.any(Tag.name == <name>) filters silently)
- Limit ≥100: capped at 100 by Query validation; requests >100 rejected at pydantic validation layer

**Files:**
- src/backend/api/notes.py: added SearchResponse Pydantic model, search_notes() endpoint handler, Query parameter imports, sqlalchemy or_ import for text search filtering

**Open Questions for Pair:**
- Frontend pagination UI: do you want has_more flag, or prefer computing it from (current_page * limit) >= total?
- Empty query string: should /api/search?query= (empty string) match nothing or return all notes? (Currently matches nothing via LIKE '%%')

**Known Limitations:**
- No full-text-search index (SQLite FTS); acceptable for <10k notes, linear table scan at scale (deferred to v2)
- No snippet/highlight generation; frontend must preview body manually if needed
- No relevance ranking; matches weighted equally, ordered only by timestamp
