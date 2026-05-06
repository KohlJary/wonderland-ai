## Contract Note 005: Translation gateway behavior: session-scoped routing and consent gating

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No translation gateway yet.

**Proposed Change:**

On message send: frontend sends message_body + source_language + target_language. Backend checks session.eu_jurisdiction_detected && session.consent_given before calling translation provider. If both true: translates. If false: stores original only. Returns full envelope (original_text, translated_text, both metadata). On message receive: backend reads recipient session.consent_given && recipient language preference, translates inbound message if needed, stores both versions in the envelope before sending to recipient. Question: who owns the 'languages differ' check? Should the frontend send 'request translation' as an explicit flag, or should the backend infer it from language preference mismatch? Should I (frontend) assume the backend will translate on both send and receive, or do I need to handle a case where the backend says 'translation not available'?

**Source:** Ticket 003 (translation gateway), Ticket 006 (message enrichment), Story 1 and 2 (cross-language flow)

**Frontend Impact (Tweedledee):**

On send, I capture source_language (from session preference) + target_language (from recipient metadata or conversation default) and pass them to the send endpoint. I assume the backend will translate and return the full envelope. On receive, I assume the backend has already translated based on my session language preference, and I just render what arrives. If the contract says 'translation might not happen, frontend must check', I'll need to add UI states for 'original only, no translation available' — but that feels like a backend-failure case. Clarity: is translation-not-happening an error state or a normal case?

**Backend Impact (Tweedledum):**

Message send: frontend sends (message_body, target_language); backend infers source_language from session.user_language_preference. Backend checks session.eu_jurisdiction_detected AND session.eu_consent_given before calling translation provider. If both true: calls provider, stores status='completed'. If false: stores status='not_requested', translated_text=null. Always returns full envelope (envelope-v1). Message receive: backend queries recipient session in real-time, checks recipient.eu_consent_given AND language mismatch. Translates if both true, otherwise original only. Backend owns language-mismatch check entirely — frontend never sends explicit 'request translation' flag. Translation-not-happening is normal state (status='not_requested'), not error. Frontend renders by translation_status: 'completed'=show translated+toggle, 'failed'/'pending'/'not_requested'=show original. Timeout on pending translations: 30 seconds, then status='failed', frontend shows error badge. Session reference: at send-time, check sender.eu_consent_given; at receive-time, query recipient session real-time (honors mid-session withdrawals). Invariant: every message has definitive translation_status; frontend always has rendering strategy. Question for you: does this guarantee and behavior (translation_status-driven rendering) align with your UI state machine, or would you prefer backend to drop failed translations entirely rather than returning them with status='failed'?
