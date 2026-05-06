## Ticket 004: Frontend: Audit view + translation provenance (polyglot moderator)

**Sources:** 002-polyglot-moderator-sees-a-conversation-in-its-original-languages-and-translations-side-by-side, 004-user-can-tell-if-a-message-was-translated-by-a-machine-or-needs-human-follow-up
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: frontend-message-input-and-conversation-render-monolingual-view
- Soft: —

**Description:**

A second view mode (permission-gated, accessible only to users with 'moderator' role or language-pair expertise). Render a conversation with original messages and translations side-by-side in a table: [original_language | original_text | target_language | translated_text | service_used | confidence_score | human_verified_flag]. This satisfies Story 002 (Jin's audit view) and Story 004 (translation provenance visibility). The data is already in the backend; this ticket is purely UI — fetch GET /conversation with ?include_translation_metadata=true and render the expanded view. Gate this view behind a permission check (placeholder: check for 'moderator' role in the user context; actual RBAC is fast-follow).

**Acceptance:**
- Moderator can access an 'audit view' of a conversation (URL or toggle)
- Audit view displays [original_language | original_text | target_language | translated_text | service | confidence | human_verified]
- Translation provenance is visible (which service, confidence score, human_verified flag)
- View is permission-gated (placeholder permission check; real RBAC in fast-follow)
- Scenario: Jin sees Klaus→Maya exchange with German original, English translation, service='google', confidence=0.92, human_verified=false

**Risk:**

Low. This is a presentation-layer ticket. The data is already there. Permission model is stubbed; real RBAC will refine it without breaking this.
