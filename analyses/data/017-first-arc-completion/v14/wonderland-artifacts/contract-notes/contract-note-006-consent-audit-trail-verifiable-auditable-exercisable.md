## Contract Note 006: Consent audit trail: verifiable, auditable, exercisable

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No consent audit trail yet.

**Proposed Change:**

Create a consent_audit table (or per-session consent log): { user_id, session_id, consent_version, consent_given_timestamp, consent_given_action ('UI-accept' | 'programmatic'), consent_withdrawn_timestamp, consent_withdrawn_action, eu_jurisdiction_detected }. Every state change (given, withdrawn) is logged with timestamp. The frontend needs an endpoint to fetch and display the user's consent history and to withdraw consent. On withdrawal, the backend: (a) marks session.consent_withdrawn = true, (b) logs the withdrawal, (c) rejects new messages from that user for the remainder of the session (or immediately?). Question: does the frontend need visibility into the audit trail, or is that backend-only for compliance audits? Should the user see their consent history in the UI (GDPR right to access)?

**Source:** Ruling 004 (consent audit trail must be verifiable + exercisable), Ruling 001 (retention window + user rights)

**Frontend Impact (Tweedledee):**

I need an endpoint to query the user's consent state and history for display in settings. I also need an endpoint to withdraw consent. If withdrawal requires immediate message-send rejection, my message-send handler needs to check if consent was withdrawn and show an error. The UI should be: 'Your consent is recorded. [View history] [Withdraw consent]'. If the user withdraws, show a dialog explaining residual-rights implications ('your prior messages remain visible; you cannot retroactively withdraw them'). That dialog text comes from Ruling 001; I need to surface it accurately.

**Backend Impact (Tweedledum):**

Consent audit table: (user_id, session_id, consent_version, eu_jurisdiction_detected, consent_given_timestamp, consent_given_action ['UI-accept'|'programmatic'|'default'], consent_withdrawn_timestamp, consent_withdrawn_action ['user-initiated'|'session-expired'|'admin-revoked'], withdrawal_initiated_from_device_id). Every state transition logged at moment of change. Public endpoints: (1) GET /user/consent-history returns all consent_audit rows for authenticated user (GDPR right to access) — includes given and withdrawn timestamps, actions, jurisdiction flag. Frontend displays as timeline: 'You consented on [date]' / 'You withdrew on [date]'. (2) POST /user/consent/withdraw initiates withdrawal: backend sets session.eu_consent_given=false, logs withdrawal with timestamp, queues audit event. Withdrawal is per-session only (other active sessions for same user unaffected). Enforcement: message send handler (POST /messages) checks session.eu_consent_given at request time; if false, returns 403 Forbidden + explanation. Prior messages remain sent and visible (residual rights). On next login: fresh session, consent re-requested. Invariant: (1) every transition immutable + timestamped; (2) withdrawal never deletes prior messages or audit records; (3) consent per-session; (4) if withdrawn mid-session, messaging blocked but reading allowed; (5) consent does not carry over from withdrawn session to new session. Data retention: consent_audit table permanent (compliance requirement). GDPR right-to-be-forgotten strategy (account deletion/anonymization) deferred to future; Ruling 001 specifies retention window. Question for you: on withdrawal, should UI optimistically show 'Consent withdrawn' before server confirmation, or should it wait for POST response? Current contract assumes frontend always checks server state on send (server is source of truth), but I can support optimistic UI if you prefer.
