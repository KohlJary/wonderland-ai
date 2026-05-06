## Contract Note 004: Session state: language preference + consent status + audit trail

**State:** agreed
**Contract Version:** v1 (same as 002, clarified: session carries language + consent state; consent_audit table is backend-only for compliance; GET /user/consent-history and POST /user/consent/withdraw endpoints for GDPR access + exercisability)

**Current Shape:**

Sessions currently carry user_id and auth token. No language preference, no consent state.

**Proposed Change:**

Extend session state to include: { user_language_preference (source + target), eu_jurisdiction_detected (boolean), consent_given (boolean), consent_timestamp, consent_version }. Additional (for audit): { consent_withdrawn (boolean), consent_withdrawal_timestamp }. Question: does the session object itself carry the consent audit trail, or does consent live in a separate table keyed by (user_id, session_id) that the frontend never sees directly? And: is consent per-session (each login, consent re-requested) or per-user (consent persists across logins)?

**Source:** Ticket 002 (session initialization), Ruling 004 (consent audit trail), Story 5 (EU consent flow)

**Frontend Impact (Tweedledee):**

I will build consent flow UI that checks session.eu_jurisdiction_detected and session.consent_given on mount. If detected && !given, I render the consent dialog. If given || !detected, I skip it and show language-preference form. If the consent state is not present in the session object by the time my app loads, I'll have to make an additional request to fetch it, which breaks the onboarding UX (blank screen → consent appears after a delay). I need consent state available immediately when the session is created. Also: I need to know if consent is per-session or per-user so I know whether to re-ask on second login.

**Backend Impact (Tweedledum):**

Session state carries language_preference (dict: source_language string, target_language string), eu_jurisdiction_detected (boolean), eu_consent_given (boolean), eu_consent_timestamp (datetime). These fields are immutable post-session-creation — set once at login, never modified for that session. Consent is per-session, not per-user: if you log in from a second device, you get a fresh session with a fresh consent decision (you may consent on device A and not on device B). Audit trail lives in a separate consent_audit table keyed by (user_id, session_id), not on the session object itself. Session object is frontend-visible; consent_audit table is backend-only and compliance-audit-visible. Your question about 'when is consent available': it is available in the session object at the moment the session is created (after the consent form submits). On app load, the frontend receives the session object with consent_given already set; no additional request needed. The contract is: session creation returns the full session object including language preference and consent state, ready for immediate UI use.

**Resolution:**

Agreed. Clear split: session object is frontend-visible, audit table is compliance-visible. Withdrawal prevents future sends, doesn't delete past messages. I'll surface residual-rights explanation per Ruling 001.
