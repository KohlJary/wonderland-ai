## Contract Note 002: Session state contract: language preference and consent

**State:** agreed
**Contract Version:** session-state-v1 (user_language_preference dict + eu_jurisdiction_detected + eu_consent_given + eu_consent_timestamp)

**Current Shape:**

Session carries user_id, device_id, auth_token, created_at. No language or consent data.

**Proposed Change:**

Add user_language_preference (source_language string, target_language string), eu_consent_given (boolean), eu_consent_timestamp (datetime). EU detection is backend-side (IP geolocation + explicit flag from signup). Session is immutable once created (user picks language and consent on login; can't change mid-session).

**Source:** ticket-002 (session initialization), ADR-001, story sources: user-joins-from-eu-and-sees-privacy-consent-flow, user-logs-in-from-a-second-device

**Frontend Impact (Tweedledee):**

Session object must be available on app mount (before first render). Consent state lives in session itself, not in a separate fetch — otherwise onboarding has a blank-screen gap while consent state loads. Consent is per-session (re-asked on login from new device; QA will test that independently). I read session.eu_consent_given on app mount; if true, render language-preference form. If false, render consent dialog first. Query: does the consent audit trail (consent_given + timestamp) live in the session object, or is it backend-only for compliance purposes? If audit trail is session-readable, I can display 'You agreed on [date]' for transparency. If audit trail is backend-only, I won't query it but the Dormouse and Queen will want it available for production inspection.

**Backend Impact (Tweedledum):**

Session creation extended to require user_language_preference dict + eu_consent boolean. Sessions are keyed by (user_id, device_id) — multi-device means multiple independent sessions with independent consent states. Session table grows two new JSON columns (language_preference dict, consent_flag + timestamp). Invariant: if user is EU-detected, eu_consent_given must be true before any translation happens; if false, translation service is never called. Non-EU users have eu_consent_given = true by default (consent not required). Session is read-only post-creation (language and consent immutable). Single-device assumption per ADR (multi-device out of scope v1, but code should support it for future expansion).

**Resolution:**

Session carries consent atomically, available on app mount with no blank-screen gap. Consent is per-session (re-asked on new login). Audit trail is backend-only, accessible via endpoint for user transparency. Invariant: if eu_consent_given=false, translation service never called. Non-EU users default to true.
