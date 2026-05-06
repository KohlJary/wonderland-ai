## Ticket 002: Backend: Message + Translation schema and storage

**Sources:** 001-two-monolingual-users-exchange-messages-in-their-native-language, message-translation-schema-asymmetric-visibility-model
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1.5–2.5 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-message-input-and-render
- Blocked by: define-message-translation-api-contract-for-two-user-exchange
- Soft: —

**Description:**

Implement the data model (Message table: id, sender_id, original_language, original_text, created_at; Translation table: id, message_id, target_language, translated_text, service_used, confidence_score, human_verified, created_at). Implement POST /message endpoint: accept sender_id, language code, text; store message; emit event or call translation router (routing method TBD pending business decision). Implement GET /conversation/:user_id/:other_user_id: return messages in thread, each with original + available translations for the user's language preference. No translation actually happens in this ticket — the routing is stubbed. The translation service integration is a separate ticket (fast-follow) once the routing decision lands.

**Acceptance:**
- POST /message accepts sender_id, language, text and returns stored message ID
- GET /conversation returns messages with original language + text; translation field is present but null (stubbed)
- Database schema supports audit (created_at, updated_at, deleted_at soft-delete placeholder)
- Caterpillar has reviewed schema and routing placeholder

**Risk:**

The soft-delete and audit trail semantics depend on Queen's compliance ruling. We're scaffolding the columns now; her ruling will inform whether they're actually used or replaced. If her ruling conflicts with this schema, expect 1 day of refactor.
