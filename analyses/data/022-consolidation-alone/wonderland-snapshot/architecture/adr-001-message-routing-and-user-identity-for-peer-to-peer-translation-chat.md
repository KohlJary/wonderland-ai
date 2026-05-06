# ADR-001: Message routing and user identity for peer-to-peer translation chat

## Context

Alice's five stories establish a user flow: Sarah and Klaus are distinct users who create accounts, initiate conversations with each other, and exchange messages with automatic translation. Klaus later retrieves the conversation history. This flow requires user identity (to distinguish Sarah from Klaus, to persist conversations across sessions) and message routing (to ensure messages reach the intended recipient and no one else). The skeleton has neither a user model nor a conversation model. The Queen has raised GDPR compliance concerns that depend on how we model identity and routing. We need to establish what the data schema looks like and what that implies for the API surface.

## Decision

Establish a three-table schema: users (with email, password, language preference), conversations (explicit table grouping two users), and messages (with sender, recipient, original text, translated text, language tags). Use token-based auth (session cookie or JWT) to persist user identity across browser sessions. Route messages to a specific recipient, not a broadcast. Store both original and translation for every message so that each user can verify translation accuracy. Use language_preference on the user table to determine which language each user receives translations in.

## Tradeoffs

- Explicit conversations table adds a row per pair but enables future features (group chats, archived conversations, conversation metadata). Implicit pairs (derive conversation from sender+recipient) are simpler for MVP but require rework if scope expands. Decision: explicit conversations. Confidence: provisional — if the team wants minimal schema, implicit pairs work.
- Token-based auth (session or JWT) requires an auth endpoint and token storage/validation. HTTP Basic (stateless, credentials per-request) is simpler for MVP and matches the directive's 'basic auth' language, but token-based is safer for production and matches Alice's 'stays logged in' better. This is open; recommend HTTP Basic for MVP simplicity, token-based for production. Decision: propose HTTP Basic for MVP. Confidence: provisional — team should decide based on security posture.
- Storing both original and translated text (not just one) doubles message storage but matches Alice's Story 002 acceptance ('Each message shows: sender name, timestamp, original text, translated text') and lets the Queen audit translation quality. Cost: 2× message size. Benefit: language-pair auditability and user confidence. Decision: store both. Confidence: firm.
- Language preference is per-user (set at signup), not per-message. This simplifies routing but assumes each user has a single language. If a user speaks multiple languages and wants to switch, this requires a profile update (acceptable for MVP). Decision: language_preference on users. Confidence: provisional — revisit if multi-language preference becomes a requirement.
- User discovery (how Sarah finds Klaus) is open. Minimal MVP: text search by email or display name. GDPR constraint: no user enumeration (the Queen will rule on this). Decision: search by email or exact username match; do not support fuzzy/partial name search in v1 (prevents enumeration). Confidence: provisional — team and Queen should align on discovery bounds.
- Audit trail scope is open and blocking the Queen's ruling. We have the basic events (signup, login, message send, translation). What gets logged, how long are logs retained, who can access them? Decision: defer to Queen's ruling. We will log: signup, login, message send (with sender, recipient, language pair, timestamp). Logs retained for 90 days (GDPR-compliant; can be extended). All other decisions deferred to Queen.
- Translation provider (Claude, Google Translate, etc.) is open and blocking the Queen's ruling on processor relationships and data residency. Decision: defer to Queen. Architecture is agnostic to the provider as long as the provider is called synchronously (message send → translate → store → return) and errors are surfaced to the sender. For MVP, Claude API is recommended (US-based, clear processor agreement); team and Queen should finalize.

## Status

Proposed
