## Contract Note 013: Read homepage by username

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none yet

**Proposed Change:**

GET /{username}. No auth required. Lookup user by username (case-insensitive), if exists and active, fetch homepage record, return {username, rendered_html, updated_at}. If user doesn't exist or is deleted, return 404. If user exists but has no homepage yet (rare; just created account), return 200 with empty/default content (question: what do we show?).

**Source:** ticket-005

**Frontend Impact (Tweedledee):**

GET /{username} returns {username, rendered_html, updated_at}. Frontend parses username from URL path, GETs /user/{username} (or /homepages/{username}—which endpoint pattern?), displays rendered_html if present, handles 404 gracefully ('user not found' or 'user has no homepage' message). Meta tags: set title to '{username}'s homepage' for SEO. Case-insensitive lookup: I'll assume case-insensitive (feels friendlier—user@example.com claimed 'alice', can visit /alice or /ALICE). Question: if user exists but has no homepage (edge case), return 200 with empty rendered_html or 404? I prefer 200 {rendered_html: null or ''} so I can distinguish 'user exists but empty' from 'user not found'. Return updated_at in both cases (or null if no homepage)?

**Backend Impact (Tweedledum):**

GET /{username} (no auth). Query: SELECT rendered_html, updated_at FROM homepages WHERE user_id IN (SELECT id FROM users WHERE LOWER(username) = LOWER(?) AND status = 'active'). Username lookup case-insensitive (COLLATE NOCASE or LOWER()). Invariant: deleted users' homepages not visible (status='deleted' excluded). Returns 200 with {username, rendered_html, updated_at}. If user doesn't exist or is deleted → 404. If user exists but has no homepage → 200 with {username, rendered_html: null, updated_at: null}. Optional: Cache-Control public, max-age=60 for client caching.
