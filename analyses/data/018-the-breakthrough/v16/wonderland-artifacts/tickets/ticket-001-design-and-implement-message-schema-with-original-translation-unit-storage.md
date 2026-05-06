## Ticket 001: Design and implement message schema with original+translation unit storage

**Sources:** adr#1: translation-as-unit-level-transformation-not-stream-level-transport, story: monolingual-book-club-member-joins-a-cross-language-discussion, story: english-only-speaker-joins-a-multilingual-group-chat
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1-2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: translate-on-send-streaming-service, dual-display-message-ui
- Blocked by: —
- Soft: —

**Description:**

Define the message record shape to store original text and translation(s) as a single unit. Include fields for: original_text, original_language, translated_text, target_language, translation_model, translation_timestamp, message_retention_flag (GDPR). Decide whether to support multi-target-language in a single message or enforce 1:1 pairing (recommend 1:1 for v1, multi-target as fast-follow). Document the schema in a contract note. No UI wiring; schema design and database migration only.

**Acceptance:**
- Message schema documented and reviewed by Tweedledee (contract negotiation complete)
- Database migration written and tested against current production schema
- Contract note includes rationale for 1:1 vs multi-target decision

**Risk:**

If team wants to support multi-target-language in v1, expand estimate to 2-3 days. If translation model choice (open-source vs API) is still undecided, that decision must precede this ticket—it affects the schema (e.g., model_identifier field).
