# ADR-001: Message model: asymmetric translation with state machine and bidirectional conversations

## Context

Alice's three stories collectively define the real users of translation chat: Klaus (German→English, real-time thought), Yuki (Japanese→English, time-critical experiment), Sam (backend observability for support). The skeleton has an echo endpoint and a placeholder Message model. The real work requires: asymmetric view of messages (sender sees original, receiver sees translation), async translation with visible state, bidirectional conversation model (two users, shared channel), and persistent translation metadata for observability. These are not implementation details — they are the load-bearing architecture.

## Decision

Adopt a schema where (1) Message has sender_id, conversation_id, original_text, translated_text, translation_status, translation_service_response_code, created_at, delivered_at; (2) Conversation has user_a_id, user_b_id, language_a, language_b; (3) API response distinguishes sender (sees original) from receiver (sees translation) via view logic, not separate endpoints; (4) translation_status is one of [pending, translated, failed], and the frontend renders appropriate UI state for each; (5) translation_service_response_code is always recorded, even on success, to support Sam's observability needs.

## Tradeoffs

- Storing both original and translation in the same Message record uses more storage than storing original and translating on-read. Tradeoff is acceptable: GDPR delete semantics become simple (delete one record), and Yuki's lab-notes export use case gets both versions without re-calling the API.
- Bidirectional Conversation model (two users in one channel) is simpler than separate sender/receiver channels but means Conversations are strictly pairs — no group chat at MVP scope. This is acceptable and intentional; group chat changes the translation coordination problem materially and is marked as future work.
- Async translation with visible state (pending → translated → failed) adds frontend complexity versus 'translate before returning to API.' Tradeoff is necessary: Klaus and Yuki's sub-3-second latency requirement cannot be met if we synchronously call a translation API before returning the message. The message must appear instantly, translation happens in background, state updates via polling or WebSocket.
- Recording translation_service_response_code on every message (success and failure) adds a column that is mostly identical values. Tradeoff is acceptable: Sam (support) needs this data to debug, and storage cost is negligible. The alternative (only log on failure) means Sam cannot distinguish 'message sent but we never called the translation API' from 'message sent, API returned 200, everything worked.'

## Status

Proposed
