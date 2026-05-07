## Contract Note 005: Client-side state and publish flow

**State:** agreed
**Contract Version:** v1 (client-state-optimistic-ui-overwrite-semantics)

**Current Shape:**

Not yet specified

**Proposed Change:**

Frontend maintains editor state (unsaved markdown content, dirty flag) in component state only. On publish POST /homepage/:slug, frontend shows optimistic 'Publishing...' state, POSTs content, awaits 200 response, shows 'Published!' and share URL. On error (4xx), shows error message and returns to editor with content intact (no loss). No localStorage persistence of unpublished drafts in v1. If user navigates away with unsaved content, browser warns 'Unsaved changes' (standard beforeunload). No real-time sync; each publish is a full POST overwrite. Conflict resolution: if user edits content locally and POST fails mid-flight, user clicks "Publish" again (retries full content, no merge).

**Source:** ticket-004 (editor), ticket-003 (backend contract)

**Frontend Impact (Tweedledee):**

Frontend state: content string + isDirty boolean. On change, mark isDirty=true. On publish: POST to /homepage/:slug with {content}, show 'Publishing...' spinner, await response. On 200: set isDirty=false, show 'Published!' notification + share URL. On 4xx: show error message, keep content in editor (user can revise and retry). On 5xx: show 'Server error' + retry button. No optimistic updates to published content on server (publish is synchronous: POST → wait → confirm). No localStorage; if user closes browser without publishing, unsaved content is lost. This is acceptable for v1 (personas expect simple flow, not draft recovery).

**Backend Impact (Tweedledum):**

POST /homepage/:slug accepts {content: markdown_string} and overwrites prior content atomically (no merge, no conflict resolution). Response includes: {status: 'published', content_html: rendered_html, slug, published_at, version: 1} so frontend can display confirmation. Version field (optional for v1) can support future "are you sure you want to overwrite?" confirmation if backend detects published_at has advanced since user started editing (optimistic concurrency). For v1, last-write-wins is acceptable; the simple overwrite semantics mean there's no ambiguity about what the final state is. Rate limiting: allow reasonable publish frequency (e.g., 10 publishes per minute per user) to prevent abuse.

**Resolution:** agreed — seam composes cleanly. Frontend maintains simple editor state; backend is overwrite-only. No merge logic, no conflict detection (yet). Both sides are clear on loss-on-browser-close behavior (acceptable for v1).

**Resolution:**

Agreed. Frontend maintains editor state (content + isDirty) in component only. Publish is synchronous POST → await → confirm. Last-write-wins, no merge. Beforeunload warning for unsaved content. Content loss on browser close is acceptable for v1.
