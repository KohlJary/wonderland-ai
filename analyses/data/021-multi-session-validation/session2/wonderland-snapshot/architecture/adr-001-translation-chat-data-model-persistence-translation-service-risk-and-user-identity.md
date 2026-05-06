# ADR-001: Translation-chat data model: persistence, translation service risk, and user identity

## Context

The directive specifies two-user translation chat with EU consumer scope (GDPR applies), basic auth, and two language pairs at launch. The skeleton provides SQLAlchemy + FastAPI + React boilerplate. The scope does not specify: (1) whether message content is persisted and for how long, who accesses audit trails, and how user data-subject rights (GDPR 15-20) are honored; (2) whether translation happens backend (external service, plaintext exposure) or frontend (client-side, no processor risk, but harder UX); (3) how users are identified and matched into language groups, and whether this surface is exploitable for user enumeration. These three decisions are load-bearing—they shape the Message and User models, the API contract, the third-party risk profile, and the compliance ruling scope.

## Decision

Provisional model: (A) Messages are persisted indefinitely unless deleted by subject request (GDPR 17); audit trail of send/receive events is system-only, not exposed via API; (B) Translation happens backend via a processor API (DeepL assumed, EU-based, DPA in place); plaintext crosses the processor boundary; (C) Users self-identify language preference on signup (not inferred); language matching is explicit (user selects target language, backend finds one other user with matching pair, creates a conversation entity). Details are open per tradeoff list below.

## Tradeoffs

- Indefinite message persistence means GDPR right-to-deletion must delete from DB + any translation service (if translation is persisted). This is open: do we cache translations or re-call the API? Trade complexity for deletion compliance.
- Plaintext translation means the processor sees the message before sender sees the reply. Trade off private client-side translation (hard, limited language pair support) against processor risk (requires DPA, data residency checks, border-crossing rules). Assume processor for now; if GDPR interpretation forbids it, we switch to client-side and accept UX cost.
- User enumeration via language matching: if user enumerates /api/users?language=German, they can count users. Mitigate by making matching opaque (backend picks the partner, user sees only active conversation) or by not exposing the user list. Current decision: no /users endpoint, only authenticated /conversations endpoint (read own conversations only). Escalate if threat model requires stricter isolation.
- No user edit/delete in scope means user records are immutable until GDPR subject-request triggers deletion. This is simpler but creates a record-keeping burden: if a user requests deletion, we must know which messages and conversations to delete. Mitigate by having deletion-safe identifiers (UUIDs, not sequential IDs).
- Two language pairs at launch (EN↔DE, EN↔JP) means the Message model has language_pair or sender_language + recipient_language fields. Open: do we model symmetric pairs (EN-DE covers both directions) or directed edges (EN→DE and DE→EN as separate, allowing asymmetric translation settings)? Assume symmetric for now.
- Basic auth is unspecified: stateless token per session (guest session, no User table) or persistent user account (User table, password hash, session tokens)? Current assumption: User table with email/password signup (email verified before matching allowed), sessions via JWT or session ID. If you prefer guest sessions, the Message model loses sender_id attribution and matching becomes ephemeral.
- Audit trail storage is unspecified: in the messages table (created_at, updated_at, deleted_at soft-delete), in a separate audit table (message_events), or in application logs (not queryable)? Assume created_at + soft-delete for now; audit table if compliance needs queryable event history.

## Status

Proposed
