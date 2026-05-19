# Contract Note 002: Search endpoint shape

**GUID:** 01KRXS2K5Z8J9N4M1H2G3K4L5
**State:** proposed
**Contract Version:** (unlocked)

## Current Shape

No search endpoint yet (only CRUD list, which returns all notes without filtering).

## Proposed Change

Add `GET /api/search` endpoint with query parameters for text search, tag filtering, and pagination.

### Request Shape
- `query` (optional): string, case-insensitive substring match on title OR body
- `tags` (optional): comma-separated tag names, AND logic (note must have ALL tags)
- `page` (optional): integer ≥0, 0-indexed page number, default 0
- `limit` (optional): integer 1-100, results per page, default 20

### Response Shape
```json
{
  "results": [
    {
      "id": int,
      "title": string,
      "body": string,
      "tag_names": [string],
      "tag_ids": [int],
      "created_at": ISO8601-string,
      "updated_at": ISO8601-string
    }
  ],
  "total": int,            // total count of matching notes across all pages
  "page": int,             // current page (echoed from request)
  "limit": int,            // items per page (echoed from request)
  "has_more": bool         // true if (offset + limit) < total
}
```

### Semantics
- **Text search:** case-insensitive substring (LIKE) on title OR body; optional
- **Tag filtering:** AND logic — note must have ALL specified tags; optional
- **Pagination:** 0-indexed, OFFSET/LIMIT model; empty results if page is beyond available
- **Ordering:** by updated_at DESC, then id DESC (deterministic across equal timestamps)
- **Total count:** computed before pagination; reflects all matching notes in database

## Source

Ticket 012: Backend search endpoint for notes by title and content search.

User need (Kohl can find past notes by title or content search) requires text search + filtering + pagination to keep frontend UX responsive at scale.

## Frontend Impact (Tweedledee)

This is a new endpoint you will consume. You will:
- Bind the query string inputs (text search box, tag filter chips, pagination controls) to these query parameters
- Parse the response and render results with pagination UI (previous/next, page count, result count)
- Handle empty-results case (query produced no matches)
- Handle out-of-bounds page (page parameter too high returns empty results list but has_more=false)

This does not change the existing CRUD endpoints or their contract.

## Backend Impact (Tweedledum)

Schema / implementation:
- Added SearchResponse Pydantic model (paginated result envelope)
- Search filtering logic: SQLAlchemy ilike() for text, Note.tags.any() for AND-joined tag filtering
- Pagination: OFFSET/LIMIT with total count query before pagination

Database:
- No schema changes; search uses existing Note, Tag, note_tags tables
- SQLite LIKE is case-insensitive by default (good for this use case)
- Tag filtering via the existing many-to-many association (note_tags table)

Performance characteristics:
- Text search: linear table scan (no full-text-search index yet); acceptable for <10k notes
- Tag filtering: join through note_tags; efficient with existing FK indices
- Pagination: count() query + LIMIT/OFFSET; total_count is recomputed per request (could cache at scale, but v1 is simple)

Known limitations:
- No full-text-search index (SQLite FTS would require schema change; deferred to v2 if search becomes slow)
- No search highlighting / snippet generation (frontend would need to truncate/preview body manually)
- No relevance ranking (all matching notes weighted equally; ordered only by timestamp)

## Resolution

Proposed — awaiting Tweedledee's assessment of frontend impact and contract fit.
