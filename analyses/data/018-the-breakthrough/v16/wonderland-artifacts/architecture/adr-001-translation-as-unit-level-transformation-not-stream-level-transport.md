# ADR-001: Translation as unit-level transformation, not stream-level transport

## Context

Five user stories surface different semantic demands on translation (fluency, accuracy, verification, unified-view moderation). Naive approach: translate messages inline as they arrive. Better approach: recognize that a message and its translations are a single semantic unit, and the translation is part of the message contract, not a side effect of transport. This matters because it shapes where translation happens (send-time, not read-time), how originals are stored (alongside translations, not separately), and what GDPR scope applies (message-unit scope, not translation-request scope).

## Decision

Store messages with translation as a unit. On send: user submits message in source language → system translates synchronously (or queues translation task) → message record includes both original and translation(s) → record is persisted as a unit. On read: UI displays original + translation together (with UI affordance to hide original if reader prefers); do not translate on read. For v1, support two-language pairs (EN ↔ DE, EN ↔ JA) in both directions, unidirectional flow (one user's outbound + incoming). Yuki's unified-language-view is deferred to v1.1 and will require a new read-time affordance (not retranslation—just reordering the display of stored translation variants). Sophie's accuracy story is core to accessibility, but quality signaling (model confidence, verification status) is deferred; v1 launches with model-generated translation and explicit disclaimer in UI.

## Tradeoffs

- Storing originals alongside translations increases storage cost and complicates right-to-be-forgotten (GDPR deletion must atomically remove message + translations). This is acceptable because message deletion is a unit operation, not a field-level operation. Tradeoff named explicitly for Queen's audit.
- Translate-on-send (not read) means translation latency is in the send flow, not invisible. For users on slow connections, this may increase perceived send time. Acceptable for v1 given 2-3 second target; revisit if telemetry shows users aborting sends.
- Side-by-side original + translation UI takes up more screen real estate than translation-only view. Yuki's unified-language-view is deferred; for v1, Henrik's accuracy need (see original) takes priority over James's clutter concern (don't see original). If James-type users provide feedback, add a per-user toggle; this is a read-time preference, not a storage change.
- Accuracy: v1 uses off-the-shelf translation model (Google Translate API or equivalent) without human-in-the-loop verification. Sophie's concern is real—mistranslation is accessibility failure. Mitigated by: (1) UI clearly signals this is machine translation, not human, (2) original always visible so Sophie can spot-check, (3) moderation tools allow flagging mistranslations, (4) v1.1 roadmap includes human-verification flow for critical messages. This is a feature-completeness gap, not an architecture gap.
- Two-language-pair limitation is scoped intentionally (three-week runway). English as hub language (EN ↔ DE, EN ↔ JA) is a data dependency decision for the Rabbit; if EN ↔ JA + EN ↔ DE can share the same pair model, cost is one model. If separate models required, cost is two. This will affect ticket estimate.
- Yuki's unified-language-view is deferred. Architecture supports it (all translations stored as variants of the same message), but the read-time UI logic to select which translation to display is not in v1. This is an enrichment feature, not a blocker.

## Status

Proposed
