## Contract Note 003: Homepage content envelope (schema + rendering)

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

no contract yet

**Proposed Change:**

Homepage record: { username, raw_markdown, rendered_html, updated_at }. Markdown is stored as plaintext. On write: backend receives raw markdown, validates it's under size limit (TBD, suggest 100KB), parses with commonmark, sanitizes HTML, stores both raw + rendered. On read: returned as { username, rendered_html, updated_at } (public view) or { username, raw_markdown, rendered_html, updated_at } (owner edit view). Rendered HTML is pre-sanitized; frontend trusts it (no additional sanitization needed).

**Source:** ticket-003: homepage-schema-and-markdown-parsing

**Frontend Impact (Tweedledee):**

Frontend renders markdown editor textarea. On view-homepage, frontend receives pre-rendered HTML and displays it (no parsing needed—backend did it). On edit, frontend GETs current markdown and populates textarea. Need to clarify: does GET /user/{username} include raw markdown or only rendered? Assuming only rendered for public view; only owner gets raw markdown in edit endpoint.

**Backend Impact (Tweedledum):** _pending_
