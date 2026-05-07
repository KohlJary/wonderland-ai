## Contract Note 003: Markdown publish and content POST contract

**State:** agreed
**Contract Version:** v1 (markdown-publish-post-with-response)

**Current Shape:**

Not yet specified

**Proposed Change:**

POST /homepage/:slug with Content-Type: application/json, body: {content: "# markdown string"}. Response 200 {status: 'published', content_html: '<h1>markdown string</h1>', slug: 'alice', published_at: '2024-01-15T10:30:00Z'} or error 400 {error: 'validation', details: 'XSS detected in content'} or 413 {error: 'payload_too_large'}. Backend parses markdown server-side, validates for XSS (no script tags), stores raw markdown in database. Frontend submits raw markdown (not HTML). No versioning in v1 — POST overwrites prior content. Backend returns rendered_html + published_at timestamp in response so frontend can immediately display share confirmation with preview.

**Source:** ticket-003 (backend contract), ticket-004 (frontend editor)

**Frontend Impact (Tweedledee):**

Frontend: (1) builds markdown text from editor, (2) POSTs to /homepage/:slug with {content: raw_markdown}, (3) handles 200 success → show 'Published!' with rendered preview and share URL, (4) handles 400 errors → show error message, (5) handles 413 → show "Content is too large" message, (6) does NOT send HTML, does NOT parse markdown on client (backend is source of truth for parsing). Frontend receives rendered_html in response; can display it in share confirmation modal or link preview.

**Backend Impact (Tweedledum):**

Database: content table with (id, homepage_id, markdown_content, rendered_html [pre-rendered on write], published_at, updated_at). Markdown parser: remark + remark-sanitize (no raw HTML allowed, no script tags, no onclick handlers). Pre-render on write, cache in DB (GET /content always returns cached version). XSS boundary: all user input escaped before rendering via sanitize library. Content size limit: 1MB max (enforced at request body parsing layer before markdown parsing). Failure mode: if markdown parser fails (e.g., malformed input), store raw content and return 422 {error: 'markdown_parse_error', details: 'Parser encountered invalid syntax at line N'} (don't corrupt the write; let frontend decide whether to retry or ask user to revise). Idempotency: POST /homepage/:slug is idempotent; multiple identical requests produce the same result (last-write-wins). Authorization: POST only allowed if user owns the slug (token must match user_id of homepage owner).

**Resolution:** agreed — seam composes. Backend returns parsed HTML in response; frontend displays it immediately in share confirmation. No further coordination needed for v1.

**Resolution:**

Agreed. Frontend submits raw markdown, backend parses and returns rendered HTML in response. POST response shape: {status: 'published', content_html, slug, published_at}. Error responses: {error: 'code', message: 'string'} with appropriate status codes (400, 413, 422). Frontend displays rendered preview in share confirmation modal.
