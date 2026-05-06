# ADR-001: User language capability model + message translation surface

## Context

MVP translation-chat serves two distinct user archetypes: monolinguals (Sophie, Yuki) who select a single read language and type in their native tongue; polyglots (Akira) who mix languages within a conversation and need to see multiple language views simultaneously. The directive stated 'two language pairs at launch' without clarifying whether both archetypes fit within that scope. Alice's stories make clear they do, but only if the user model can express language capability as a set (languages this user can read, languages they can write) rather than a binary choice. The architecture must account for both archetypes without pretending they are the same feature.

## Decision

User has a language capability model: User.read_languages (set of language codes) and User.write_languages (set of language codes). A user's read/write capabilities are inferred from the language_pairs of conversations they participate in. Conversations are pairwise (exactly two users) and language_pair is an explicit enum: {en_de, en_ja, ...}. Message is stored once in its original language (sender's language). Translation to reader's language happens on-read, either synchronously (fetch, translate on-demand) or cached (fetch, translate once, store result). Sender always sees original; receiver sees translation. Both can see both if we choose transparency (deferred to UI). Soft-delete on User for GDPR erasure compliance.

## Tradeoffs

- Storing message in original language + translating on-read means latency on first read of a message (translation API call). Caching the translation result (separate Translation table) trades storage for latency. MVP does on-demand; fast-follow caches.
- Language capability as set-inferred-from-conversations is simpler than a separate User.preferred_language attribute, but it means language is not a pure user attribute—it is contextual to the conversation. If a user is in both an en_de and en_ja conversation, they implicitly read both English and German for one, English and Japanese for the other. This is correct for the use case (Akira) but requires careful UI messaging.
- Pairwise conversations (exactly two users) means no group chats at MVP. This is a hard constraint, not a knob. If we want to support >2 users, the conversation model changes materially (becomes group, language_pair becomes negotiated or multi-pair). This is deferred.
- Translating only current message (not conversation history) reduces PII scope with external translator and simplifies the API surface. It costs context—pronouns, references, idiom may be lost. This is acceptable for MVP (Akira's confusion-flag). Future feature: optionally send context for better translation quality. Requires stricter DPA with translator vendor.
- Message erasure via soft-delete means messages are never physically deleted from the database, only marked deleted_at. Queries filter them out. This is GDPR-compliant (we can audit deletions). Query contracts must always include `WHERE deleted_at IS NULL`. Migration risk if the team forgets this filter.
- Translation service is a third-party vendor (Google Translate, DeepL, etc.), not homegrown. This incurs vendor dependency and DPA obligations. Cost is ongoing per-message (quota, rate limits). Alternative: build our own translation service (out of scope for MVP). Decision on which vendor is the Queen's ruling (data residency, DPA, cost).

## Status

Proposed
