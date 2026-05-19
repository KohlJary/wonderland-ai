## Contract Note 011: Note body field: raw markdown from client to server and back

**GUID:** 01KRXXBXV5YJ336SJ7AZZXYW5G
**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Note model stores body: str | None (optional on create, defaults to empty string). POST /api/notes request {title, body, tag_names}; response {id, title, body, tag_names, tag_ids, created_at, updated_at}.

**Proposed Change:**

Lock down: body field contains raw user markdown text (0–16384 chars). Server stores body as-is, without sanitization, HTML escaping, or pre-processing. Response returns body in the same form the client sent. This means Tweedledee's markdown renderer receives raw markdown and is responsible for sanitizing + rendering. No server-side markdown processing.

**Source:** Tweedledee concern: 'Does the client parse raw markdown or does the server pre-process?' Affects HTML sanitizer config and parser robustness for Tickets 038–039 (markdown preview component).

**Frontend Impact (Tweedledee):**

Confirmed: Tweedledee's markdown renderer uses a safe library (react-markdown or markdown-it + DOMPurify) to parse raw body text and render as sanitized HTML. No assumption that server pre-sanitized. Parser config: strict XSS prevention (no script tags, no dangerous protocols, sanitize inline HTML). Error handling: if body is malformed markdown, render gracefully (show what parsed + warn user). For Tickets 038–039 (preview pane), Editor sends body as-is to POST /api/notes; Preview component receives body from backend and renders it client-side. This contract locks the rendering boundary: server provides raw markdown, client provides safe rendering.

**Backend Impact (Tweedledum):**

Zero implementation change (already correct). Clarifies invariant: body is unmodified pass-through. No sanitization, escaping, or markdown processing on server. Constraint: server must preserve body exactly as sent, including any special chars / markdown syntax / malformed content. If future security ruling requires server-side sanitization, that becomes a breaking contract change requiring new version.
