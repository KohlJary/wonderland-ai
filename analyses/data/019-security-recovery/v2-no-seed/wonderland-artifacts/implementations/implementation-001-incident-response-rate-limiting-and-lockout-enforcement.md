## Implementation 001: Incident-response rate-limiting and lockout enforcement

**Side:** backend
**Ticket:** T37-incident-response
**Contract:** half-formed; /login returns 429 (rate_limit_ip), 423 (account_locked), 401 (invalid_cred), or 200 + session_token. Awaiting Tweedledee confirmation on error response shape and session token format.
**Ready for review:** no

**Approach:**

IP-based rate-limit (10 attempts/min per source IP) + account-based lockout (5 failures in 5min triggers 15min cooldown). Enforced at middleware layer before handler. Audit log records every attempt with source IP and failure reason. /incident/status endpoint for operational visibility.

**Invariants Enforced:**
- No single IP can successfully login >10 times per minute (enforced by sliding-window counter in auth_service.is_ip_rate_limited)
- No account can have >5 failed login attempts in any 5-minute window without entering 15-minute lockout (enforced by auth_service.record_failed_attempt checking recent failures)
- A locked account cannot authenticate until lockout expires, regardless of correct password (enforced by auth_service.is_account_locked_out gating handler)
- Every login attempt (success or failure) is recorded in audit log with timestamp, username, source IP, and failure reason (enforced by LoginAttempt dataclass + audit_log append)

**Schema Changes:**

No schema changes required for incident response. In-memory stores (auth_service._incident_store, auth_service.audit_log) are sufficient for immediate mitigation. Migration to Redis + persistent audit log should follow after Queen rules on disclosure scope.

**Failure Modes Handled:**
- Attack mid-incident: IP rate-limit blocks further attempts; locked accounts can't re-attempt. If attacker has credential list for 5+ accounts, each gets individually locked.
- Legitimate user locked out: account returns 423 on next attempt. User must wait 15 minutes or contact support. UX path TBD with Tweedledee.
- Redis unavailable (future): fallback behavior undefined; incident response uses in-memory stores as default. Production migration plan needed.
- Attacker spoofs IP via X-Forwarded-For: rate-limit becomes per-forwarded-IP rather than per-source. Mitigated by proxy validation and WAF.
- Attacker targets multiple accounts: 5th attempt per account triggers per-account lockout. Distributed attack across 100 accounts means 100 accounts locked. Expected and acceptable per Dormouse observation (47 already locked).

**Files:**
- auth_service.py: core rate-limit + lockout state machines, audit logging, incident status reporting
- http_middleware.py: FastAPI middleware + /login endpoint handler, client IP extraction, error response serialization

**Open Questions for Pair:**
- Error response format: should /login return application/json {error, detail} or {error_code, message} or {type, status, errors}? Frontend must decode 429/423/401 distinctly.
- Session token shape: placeholder returns hash-based token. Real implementation needs signed JWT or opaque token w/ backend lookup?
- Lockout user experience: when account is locked, should we return 423 or 401 + detail='locked'? Different HTTP status affects browser behavior.
- Audit log retention: in-memory for incident response, but production needs persistent audit trail for forensics. Should this hit a separate audit service or persist to main DB?

**Known Limitations:**
- Incident-response scope: rate-limit thresholds (10 attempts/min, 5 failures/5min) are tuned to stop the observed attack but will need review by Queen and Dormouse for production stability.
- In-memory store: incident_store and audit_log are ephemeral. For production, migrate to Redis (rate-limit) + audit log service (persistence).
- Credential validation: _validate_credentials() is a placeholder. Real implementation needs bcrypt/argon2 password verification.
- Proxy trust: X-Forwarded-For trust model assumes reverse proxy honesty; production should validate trusted proxy list.
- IP spoofing: attacker can forge X-Forwarded-For header if reverse proxy is misconfigured. Requires careful proxy setup.
- Distributed instances: if multiple server instances, in-memory stores don't sync. Needs Redis for stateful rate-limit + lockout.
