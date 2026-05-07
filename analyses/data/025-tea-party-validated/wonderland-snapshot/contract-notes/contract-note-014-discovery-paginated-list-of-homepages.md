## Contract Note 014: Discovery: paginated list of homepages

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none yet

**Proposed Change:**

GET /discover?cursor=<cursor>&limit=10. No auth required. Return paginated list of active users' homepages, ordered by updated_at DESC. Each entry: {username, updated_at, preview (first 200 chars of rendered_html)}. Cursor is opaque (we generate it; it encodes updated_at + user_id for stable ordering). Use cursor pagination, not offset, to handle concurrent updates without skips. Optional query params: cursor, limit (default 10, max 50).

**Source:** ticket-006

**Frontend Impact (Tweedledee):**

GET /discover?cursor=<cursor>&limit=10 returns {homepages: [{username, updated_at, preview, ...}, ...], next_cursor}. Frontend renders list, each item is a link to /{username}. Preview is shown as text (previewing the rendered HTML content). I'll need to know: is preview a string of raw text, or is it HTML (with tags stripped)? If HTML, I'll strip tags on frontend. If plain text, easier for me. Also: should preview be first 200 *characters* or first 200 *words*? Characters is simpler. Return has_next flag (boolean, true if more results exist) so I know whether to show 'load more' button. Cursor is opaque—I'll just pass it back as-is. Limit max 50: I'll honor that in my requests (default 10, max I'll request is 50).

**Backend Impact (Tweedledum):**

GET /discover?cursor=<opaque>&limit=10 (no auth). Query: SELECT user_id, username, updated_at, rendered_html FROM homepages WHERE users.status='active' ORDER BY updated_at DESC, id ASC LIMIT 11 (fetch +1 to detect has_next). Cursor opaque (base64({updated_at, user_id})). Returns 200 with {homepages: [{username, preview: string, updated_at}, ...], next_cursor: string|null}. Limit: default 10, max 50. Invariant: cursor pagination stable under concurrent updates (updated_at+id total order). Preview: plain text (first 200 chars, HTML tags stripped) to avoid frontend sanitization overhead. Failure modes: concurrent updates same page → may appear on multiple pages (acceptable v1); deleted homepage → disappears from later pages (acceptable).
