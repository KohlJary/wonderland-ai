## Contract Note 012: Edit homepage endpoint

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none yet

**Proposed Change:**

POST /homepages (authenticated). Body: {raw_markdown}. Backend validates ownership (user owns their homepage), parses markdown, sanitizes, stores both raw + rendered, returns {raw_markdown, rendered_html, updated_at}. If homepage doesn't exist yet, create it. Idempotent: sending same markdown twice returns same result. Return 200 on success, 400 if markdown invalid, 401 if unauthenticated, 403 if user is not the owner.

**Source:** ticket-004

**Frontend Impact (Tweedledee):**

POST /homepages {raw_markdown} from authenticated user. I show loading spinner while request is in flight. You asked whether I want rendered_html in response or fetch separately—**please include rendered_html in response** so I can show live preview immediately without a second GET. Response shape: {raw_markdown, rendered_html, updated_at} works. On error (400 for invalid markdown), I show error message and keep textarea populated (user can edit). On success, I update the preview display and update the 'last saved' timestamp. Ownership is implicit (I'm authenticated, you check my token); I don't send user_id. Idempotency: note that POST to same content twice is safe (returns same result); I won't rely on this but won't break if it happens.

**Backend Impact (Tweedledum):**

POST /homepages (auth required, JWT header). Body: {raw_markdown}. Validates: (1) request user_id from JWT matches active user, (2) raw_markdown ≤ 100KB, (3) markdown parses. Parses, sanitizes, upserts homepage (INSERT OR UPDATE on user_id FK). Returns 200 with {raw_markdown, rendered_html, updated_at}. Ownership enforced implicitly (JWT user_id is owner; no second check needed). Idempotency: identical markdown twice → identical response (last-write-wins). Failure modes: concurrent edits → last-write-wins (no merge); user deletes account mid-edit → atomic transaction (edit fully commits or fully fails).
