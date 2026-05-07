## Contract Note 010: V1 Seam Summary (Finalized)

**State:** agreed
**Contract Version:** v1.0 (locked)

**V1 MVP Seams (Agreed & Finalized):**

### 1. Session & Auth (contract-note-006)
- Endpoints: POST /auth/register, GET /auth/verify?token=X, POST /auth/logout, GET /auth/me
- Session via httpOnly cookies (SameSite=Strict)
- Slug allocated at email verification time
- User object includes: email, verified (bool), slug (uuid8 | null), created_at, hostname

### 2. Markdown Publish (contract-note-008)
- POST /homepage/:slug/content with Content-Type: application/json, {markdown_content: string}
- Response 200: {slug, published_at, updated_at}
- Error shape: {error: 'code', message: 'string'}
- Markdown pre-rendered to HTML server-side (remark + sanitize)
- No draft/published distinction; published immediately
- No conflict resolution or versioning in v1

### 3. Public Homepage Delivery (contract-note-009)
- GET /homepage/:slug returns self-contained HTML page
- GET /homepage/:slug?raw=true returns raw markdown
- Browser caching via Cache-Control (1h) + ETag
- Frontend constructs share URL as {hostname}/homepage/{slug}, hostname from GET /auth/me
- 404 for nonexistent/deleted pages

### 4. Client State & Flow (contract-note-005, no changes)
- Frontend state: content string + isDirty boolean
- No localStorage persistence of drafts in v1
- No optimistic preview beyond client-side markdown rendering
- beforeunload warning for unsaved changes

---

**Deferred to V2 or Later:**

- Custom slug selection (POST /homepage/reserve-slug) → contract-note-007
- Content versioning / history
- Conflict resolution on concurrent edits
- Optimistic HTML preview
- Automatic retry on publish failure
- Private pages / authentication for public pages
- Multi-page content
- Custom CSS / styling
- Comments / interactions
- Analytics / tracking
- Webring feature (separate epic)
- GDPR data purge (separate epic)

---

**Outstanding (Not Blocking v1 Implementation):**

- CSRF token spec → escalated to Queen of Hearts (contract-note-TBD)
- Observability hooks (metrics, structured logs, tracing) → Dormouse to specify

---

**Test Scope (Hatter):**

Hatter will write failing tests against the four finalized contracts:
1. Auth flow: register → verify → me (slug allocation timing)
2. Publish flow: POST /homepage/:slug/content with markdown validation, error responses
3. Public page: GET /homepage/:slug returns HTML, caching headers, 404 handling
4. Client state: frontend form state management, unsaved-changes warning

Tests should exercise:
- Happy paths (register → verify → publish → view)
- Error paths (invalid email, weak password, slug collision, markdown parse failure, 413 payload too large)
- Invariants (verified users always have slugs, slugs are unique, content is published immediately)
- Timing (slug allocated at verification, not registration)
- Caching (ETag changes when content updates, browser cache behavior)

---

**Implementation Order:**

1. Auth service (contract-note-006) — most dependent on
2. Content storage (contract-note-008) — depends on Auth, used by Public
3. Public page rendering (contract-note-009) — depends on Content
4. Frontend integration — all endpoints, client state management

---

**Backward Compatibility:**

All v1.0 contracts are new (no prior versions). No migration concerns for v1 launch.

---

**Agreed by:** Tweedledum (2025-01-XX), Tweedledee (2025-01-XX)

**Status:** ✅ LOCKED. Ready for Hatter to write failing tests. Implementation phase follows test completion.
