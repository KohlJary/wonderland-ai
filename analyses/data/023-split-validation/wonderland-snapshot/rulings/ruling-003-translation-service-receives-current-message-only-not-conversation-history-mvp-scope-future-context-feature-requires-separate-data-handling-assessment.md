## Ruling 003: Translation service receives current message only, not conversation history (MVP scope); future context feature requires separate data-handling assessment

**Severity:** high
**Domain:** data-handling
**Source:** architectural proposal from Cheshire Cat; GDPR Art. 28 processor scope

**Citation:**

GDPR Art. 5(1)(c) (data minimization); GDPR Art. 28 (scope of processor obligations)

**Finding:**

The Cat's proposal limits translation service input to the current message only, not the full conversation history. This is the correct minimization stance for the MVP. Sending conversation history to the translation service would expand the scope of PII shared with the processor (more messages, more user context, more metadata) without proportional benefit to the user experience in the MVP phase. This would require a broader DPA and more extensive audit logging. The proposal correctly defers this to a future feature.

**Required Remediation:**

Translation service integration must NOT send conversation history or user context in the MVP. The API call to the translation service includes: (message_id, message_text, source_language, target_language). It does NOT include: prior messages, user identity, conversation metadata, or sender name. When the future feature 'send context for pronoun resolution' is proposed, a separate security and compliance assessment is required before implementation. Document this boundary in the ADR (Cat artifact) and in code comments.

**Acceptance Criteria:**
- Translation service call sends only: message text, source language, target language
- Translation service call does NOT send: user ID, sender name, conversation ID, message history, timestamps, or metadata
- API implementation in Tweedledum enforces this boundary (code review checks)
- Future feature: 'context-aware translation' is blocked until Queen rules on the data-handling implications

**Residual Risk:**

Translation quality may suffer without context (pronouns, references may be ambiguous). This is a UX tradeoff, not a security issue. Accept for MVP; revisit in fast-follow if user feedback indicates the quality impact is unacceptable.

**Compliance Implications:**

GDPR Art. 5(1)(c) (data minimization); GDPR Art. 28 (processor scope). Limiting processor scope reduces compliance obligations.

**Audit Reference:**

Compliance Map entry: 'Translation service data minimization (MVP)'; ADR reference in Cat's translation-service-integration ADR.
