## Contract Note 008: Markdown Publish and Content Storage

**State:** agreed
**Contract Version:** v1.0-publish

**Finalized Shape:**

**POST /homepage/:slug/content** — authenticated, owned-slug-only
- Request: Content-Type: application/json, {markdown_content: string (max 1MB)}
- Response 200: {slug, published_at, updated_at}
- Response 400: {error: 'markdown_content_missing' | 'markdown_content_too_large', message: '...'}
- Response 422: {error: 'markdown_parse_failed', message: 'Invalid markdown syntax at line 5: ...'}
- Response 403: User does not own this slug (authenticated but slug belongs to another user).
- Behavior: Validates markdown_content (non-empty, ≤1MB). Parses markdown server-side using remark + sanitize (no raw HTML). Pre-renders to HTML, stores both markdown and rendered HTML in content table. Overwrites prior content (no versioning in v1). Returns slug + timestamps.

**GET /homepage/:slug/content** — unauthenticated (API endpoint for debugging, v2 may remove)
- Response 200: {raw_markdown, published_at}
- Response 404: Slug does not exist or content not published.
- Behavior: Returns stored markdown + timestamp. Does not return rendered HTML (frontend doesn't consume this; it gets HTML from GET /homepage/:slug public page).

**GET /homepage/:slug** — unauthenticated, public page
- See contract-note-009 (Public Homepage Delivery)

**Database Schema:**
- `content` table: id, homepage_id (FK), markdown_content (text), rendered_html (text, pre-rendered), published_at, updated_at
- Markdown parser: remark + remark-sanitize (strip raw HTML, script tags, onclick handlers)
- XSS boundary: all user markdown is escaped during rendering; rendered_html is safe for direct HTML insertion

**Invariants:**
- A content row always has both markdown_content and rendered_html populated (no partial writes).
- rendered_html is deterministic from markdown_content (same markdown → same HTML, always).
- No draft/published distinction in v1; content is published immediately on POST.
- A homepage has at most one content row (overwrites on subsequent POST).

**Frontend Assumptions (Confirmed):**
- Frontend sends markdown_content as plain string, no escaping.
- Frontend does NOT send pre-rendered HTML.
- Frontend does NOT receive content_html in POST 200 response (receives only slug + timestamps).
- Frontend renders markdown client-side in preview (for UX feedback while editing), but published version is server-rendered.
- On error (400, 422, 413), frontend displays error message to user and returns to editor with content intact.
- Frontend has NO conflict resolution if POST fails mid-flight; user retries manually.
- Frontend has NO automatic retry logic.

**Backward Compatibility:**
- v1.0 only; no prior versions.

**Failure Modes Handled:**
- Markdown parser fails (e.g., deeply nested lists, malformed syntax): return 422 {error: 'markdown_parse_failed', message: '...'}, do NOT corrupt stored content.
- Content size exceeds 1MB: return 413 {error: 'markdown_content_too_large', message: 'Max 1MB'}.
- User not authenticated: return 401 (handled by auth middleware).
- Slug does not exist: return 404 (created separately by registration/verification flow).
- User not owner of slug: return 403 with error message.
- Database write fails (rare): return 500 (internal server error), do not return to user (Dormouse observes).

**Known Limitations:**
- No content versioning in v1; overwrites are permanent.
- No draft/published distinction; all content is published immediately.
- No conflict resolution for concurrent edits (last write wins).
- No automatic retry on frontend; network failures require manual user retry.

**Resolution:**
- ✅ POST /homepage/:slug/content accepts {markdown_content: string}.
- ✅ POST returns {slug, published_at, updated_at} (no content_html).
- ✅ Error shape: {error: 'code', message: 'string'}.
- ✅ Parse failures return 422; validation errors return 400.
- ✅ No conflict resolution in v1.

**Agreed by:** Tweedledum (2025-01-XX), Tweedledee (responding)
