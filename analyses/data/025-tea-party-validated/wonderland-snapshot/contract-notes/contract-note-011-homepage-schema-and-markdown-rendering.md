## Contract Note 011: Homepage schema and markdown rendering

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none yet

**Proposed Change:**

Table: homepages (id, user_id FK unique, raw_markdown text, rendered_html text, updated_at). Markdown parser: use commonmark-py or similar trusted library. On save (edit endpoint), backend receives raw_markdown, parses with commonmark, sanitizes HTML with bleach (allow tags: a, b, i, em, strong, h1-h6, p, ul, ol, li, blockquote, code, pre, img). Store both raw_markdown (for edit form) and rendered_html (for public view). Invariant: rendered_html is always a sanitized parse of raw_markdown (never user-submitted HTML). Invariant: each user has exactly one homepage record (or none). Failure mode: parse fails (malformed markdown) -> return 400 with error; do not store. Question for pair: size limits on markdown (to prevent abuse)? Suggest 100KB max. Question: image embedding — do we allow <img> tags (assuming sanitized), or only markdown image syntax (which we can control)?

**Source:** ticket-003, ticket-004

**Frontend Impact (Tweedledee):**

Frontend has a markdown editor (textarea) for /edit-homepage view. I'll use a library like `marked` or `react-markdown` to preview the rendered output in real-time as user types (client-side parsing, just for preview—I won't store or send rendered HTML, only raw markdown to you). On /edit submit, I POST raw markdown to you; you parse, sanitize, store both, return rendered_html. I'll display the returned rendered_html to confirm the user's edits. On /view-homepage, I receive pre-rendered HTML from you and display it as innerHTML with a dangerously-set-html flag (since it's pre-sanitized on backend). Size limit (100KB markdown): I can validate client-side (warn user if approaching) and you validate server-side (reject if over). Image embedding: your sanitization allows `<img>` tags; I'll allow users to write markdown image syntax (`![alt](url)`), which you'll sanitize. Question: do we validate image URLs (block external CDN, require same-origin, etc.) or allow any? If blocking external, I need to know that client-side so I can warn before they paste an external image URL.

**Backend Impact (Tweedledum):**

Homepages table: id (PK), user_id (FK UNIQUE), raw_markdown (TEXT), rendered_html (TEXT), updated_at. Markdown parser: commonmark-py. Sanitization: bleach whitelist (a, b, i, em, strong, h1–h6, p, ul, ol, li, blockquote, code, pre, img). Size limit: 100KB on raw_markdown. Invariants: (1) each user has ≤ one homepage; (2) rendered_html is sanitized parse of raw_markdown, never user-submitted HTML. Failure modes: parse error (malformed markdown) → 400, no store; sanitization strips disallowed tags → stored correctly. Support markdown image syntax (![alt](url) → <img> → sanitized by bleach).
