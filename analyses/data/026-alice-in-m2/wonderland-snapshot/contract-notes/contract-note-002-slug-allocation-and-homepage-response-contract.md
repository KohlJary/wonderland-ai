## Contract Note 002: Slug allocation and homepage response contract

**State:** agreed
**Contract Version:** v1 final: slug is required account attribute, allocated at verification

**Current Shape:**

Not yet specified

**Proposed Change:**

(missing)

**Source:** ticket-002 (slug allocation), ticket-001 (registration flow)

**Frontend Impact (Tweedledee):**

If auto-allocation: /auth/verify response includes {slug: 'alice', full_url: 'https://homepages.test/~alice'}; frontend displays immediately. If explicit reservation: /auth/me returns current slug if claimed, or null if not; frontend offers "Claim your slug" as a post-verification modal; POST /homepage/reserve-slug happens when user clicks "Claim".

**Backend Impact (Tweedledum):**

If auto-allocation: users table gets slug column; /auth/verify triggers slug generation and reserves it atomically with verification. If generation fails (all variants taken), return 422 with error message. If explicit reservation: homepages table (already proposed in 007) is the source of truth; slug is optional; POST /homepage/reserve-slug is the allocation endpoint.

**Resolution:**

Story-001 acceptance criteria require slug available immediately post-verification. ADR-001 frames slug as account identity (Layer 1 owns homepage). v1 allocates auto at verification; v2 adds custom-slug selection (POST /homepage/reserve-slug and slug-edit endpoint). Marked agreed based on user story evidence.
