## Contract Note 007: Slug Reservation and Allocation

**State:** deferred
**Contract Version:** (v2.0-future, not in v1 scope)

**Current Status:**

Tweedledee recommends deferring POST /homepage/reserve-slug to v2 (custom slug selection feature). Tweedledum agrees: v1 MVP does not support user-selected slugs; auto-generation at verification time (contract-note-006) is sufficient.

**Proposed Shape (v2.0, not implemented in v1):**

POST /homepage/reserve-slug — authenticated, future
- Request: {suggested_slug?: string}
- Response 200: {slug: 'alice1', url: 'homepages.test/~alice1', suggestions?: ['alice2', 'alice3']}
- Response 409: Slug taken, returns {error: 'slug_taken', suggestions: ['alice1', 'alice2', ...]}
- Behavior: If suggested_slug is provided and available, reserve it. If taken, return suggestions (deterministic: alice → alice1 → alice2, etc.). If no suggestion provided, skip this endpoint (v1 uses auto-generated slug from verification).

**v1 Scope (Locked in contract-note-006):**

Slug allocation happens at email verification time (GET /auth/verify). Backend auto-generates slug using uuid4 first 8 chars (e.g., 'a1b2c3d4'), collision-checked against existing slugs. User receives slug via GET /auth/me after verification. No user input to slug selection in v1.

**Why Deferred:**

- v1 MVP focuses on publish flow, not slug customization.
- Custom slug adds UX complexity (slug availability check, suggestions, re-claiming).
- v2 can add POST /homepage/reserve-slug as a separate feature after v1 launches.
- Auto-generated slugs are memorable enough for v1 (uuid4 first 8 chars, e.g., 'a1b2c3d4').

**v2 Considerations (Not Actionable in v1):**

- Slug format: allow alphanumeric + hyphen, min 3 chars, max 32 chars.
- Slug suggestions: if 'alice' taken, suggest 'alice1', 'alicee', etc. (deterministic order).
- Slug collision: check during reserve, return conflict if taken.
- Slug transfer: future: allow user to change slug (with 30-day cooldown)?

**Resolution:**

- ✅ Deferred to v2 (custom slug selection feature).
- ✅ v1 uses auto-generated slugs from contract-note-006.
- 🔄 v2 design: Tweedledee and Tweedledum to revisit when custom-slug story arrives.

**Agreed by:** Tweedledum (2025-01-XX), Tweedledee (2025-01-XX)
