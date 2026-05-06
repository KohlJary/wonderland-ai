## Contract Note 001: Login endpoint rate-limit and lockout contract

**State:** agreed
**Contract Version:** 1.0

**Current Shape:**

Pre-incident: POST /login accepts {username, password}, returns {session_token} on success or 401 on bad creds.

**Agreed Change:**

Add rate-limit enforcement (10 attempts/min per IP) and account lockout (10 failures/30min). Incident-response version 1.0. Error responses: 429 rate_limit_ip (Retry-After: 60), 423 account_locked, 401 invalid_credentials. Backend enforces invariants; frontend displays appropriate error state.

**Source:** T37 credential-stuffing incident; rate-limit deployment in auth_service.py and http_middleware.py

**Frontend Impact (Tweedledee):**

Three error states now reachable from /login:
- 429 rate_limit_ip: Display "too many attempts from your IP" + countdown timer (Retry-After header) + link to unlock (pending contract-note-002). User cannot retry /login until window resets.
- 423 account_locked: Display "account locked after 10 failed attempts" + recovery path (email recovery link per contract-note-002) + "account auto-unlocks in 30 min" fallback. User can unlock immediately via recovery OR wait 30 min for auto-unlock.
- 401 invalid_credentials: Display "invalid username or password" (unchanged from pre-incident).

**Backend Impact (Tweedledum):**

auth_service.py implements attempt_login(username, password, source_ip) -> (success: bool, error_reason: str | None). Audit log records all attempts (success, failure reason). In-memory state for incident response (production would use Redis). Lockout state cleared on successful auth. Rate-limit sliding window per IP, account lockout TTL 30min per Queen ruling 006. Migration cost: none — incident-response state is ephemeral. SHIPPED in http_middleware.py + auth_service.py (verified running, attack halted, 47 accounts locked, 0 successful breaches per Dormouse observation).

**Contract Version 1.0 covers:**
- GET /login endpoint signature: POST /login with {username, password} → {session_token} | error response
- Error response envelope: HTTP status + JSON {error: error_code, detail: message, [retry_after: seconds]}
- Rate-limit behavior: sliding 15-minute window per IP, counter increments on failure, resets when window slides
- Lockout behavior: counter increments on failure, account locked when count >= 10 within 30-minute window, auto-unlock after 30 min OR manual unlock via recovery flow (contract-note-002)

**Resolved:**
- ✓ Backend implementation shipped and running (Dormouse confirms nominal telemetry)
- ✓ Error surfaces mapped to HTTP status codes (429, 423, 401)
- ✓ Rate-limit window and lockout TTL per Queen's rulings
- ✓ Audit logging enabled (ready for Dormouse telemetry + Queen's breach investigation)

**Awaiting:**
- Contract-note-002 resolution (unlock authorization primitive) to finalize frontend UX

**Dissent records:** none — contract-note-002 is where the real negotiation lives
