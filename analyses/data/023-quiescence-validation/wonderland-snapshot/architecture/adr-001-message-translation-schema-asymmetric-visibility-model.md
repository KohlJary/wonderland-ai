# ADR-001: Message + Translation Schema: Asymmetric Visibility Model

## Context

Two users in different languages need to exchange messages with near-real-time translation. Alice's four stories converge on a specific data model: users see their own originals (no re-translation), see the other user's original + translation. A moderator (Story 002) should see both originals and translations side-by-side. Translation provenance (machine vs. human) must be visible per Story 004. GDPR requires that users can delete their data and audit trails can be preserved (Queen's concerns). The codebase has a placeholder message model; the feature requires replacing it with one that stores originals separately from translations and tracks translation provenance.

## Decision

The system stores messages in three-layer schema: (1) **Original** — the message as written (user_id, language_code, text, created_at). (2) **Translation** — derived artifacts (original_message_id, target_language_code, translated_text, translator_service, confidence_score, is_human_verified, created_at). (3) **View** — rendered to each user based on their language preference and role (sender sees own original + others' original + translation; moderator sees original + all translations). Translations are immutable artifacts of originals; deleting an original cascades deletion of its translations (soft or hard per retention policy). Each translation record includes metadata so clients can display translation confidence/provenance (Story 004).

## Tradeoffs

- This model requires a second database table (Translations) linked to Messages via foreign key. Simpler alternative: store all versions in a single EAV-style table. Cost: query complexity increases (must JOIN or aggregate); benefit: schema is normalized, queries are composable, deletion is scoped cleanly.
- The 'translation provenance' (translator_service, is_human_verified) implies we have a way to know the difference. Where does 'human_verified' come from? This is a business decision (do we have a human QA step?) deferred to Story 004's scope. The schema can store the flag; workflow populates it. Deferring this does not block core implementation.
- Translation-latency SLO (sub-100ms vs. 1-5s) is tied to translator source. In-process libraries (local models, sync API clients) give low-latency, bounded cost, full data control. External services (AWS Translate, Google Translate, OpenAI) give high-quality but introduce dependency, latency variability, and GDPR data-transfer concerns. **This is an open decision.** Once made, API contract (sync POST vs. async job queue) becomes clear. The data model supports both; the integration pattern doesn't.
- Message retention and soft-delete policy (Queen's first question) is open. Ephemeral messages (auto-delete after N days) vs. permanent with user-delete-rights both fit this schema. Audit-logging overhead (Queen's second question) is also parametric. Schema can support all variants; implementation chooses based on Queen's ruling.
- This model allows group chats (thread_id as a grouping key) or pair chats (two-user conversation). Alice's stories assume pair; Story 002 hints at observing a pair. The schema is neutral; API contract specifies scope (POST /conversations/{id}/messages vs. group-aware endpoint). Deferred to ticket scope.

## Status

Proposed
