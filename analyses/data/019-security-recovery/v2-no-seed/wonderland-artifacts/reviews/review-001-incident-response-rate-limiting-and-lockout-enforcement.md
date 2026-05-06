## Review 001: Incident-response rate-limiting and lockout enforcement

**Files reviewed:** auth_service.py, http_middleware.py
**Verdict:** request-changes

### Findings

#### block: Credential validation is a placeholder that always succeeds
**Location:** auth_service.py:190-195
**Quote:**

```
def _validate_credentials(username: str, password: str) -> bool:
    """
    Placeholder credential validation.
    In production, would check against salted password hash.
    """
    # For this incident response, we'll assume a simple check.
    # Real implementation would use bcrypt or argon2.
    if not username or not password:
        return False
    return True  # Placeholder — replace with real check
```

**Read:** This function returns True for any non-empty username and password pair. It does not validate the password against any stored hash or reference. Every login attempt that clears the rate-limit and lockout checks will succeed regardless of whether the password is correct.
**Concern:** The rate-limit halts the attack by volume; the lockout prevents retries. But the code removes the final gate — credential validation — entirely. An attacker who passes through the rate-limit and lockout (which they eventually will, as the window expires) will authenticate successfully without a password. The Queen's ruling assumes the rate-limit + lockout are defenses *around* credential validation, not replacements for it. This is a correctness bug.
**Request:** Replace the placeholder with actual credential validation. Check the username and password against whatever credential store your system uses (password hash, OAuth token validation, whatever). If the credential store isn't available yet, route to the Queen for a decision on what constitutes a valid credential in this incident. 'Return True' is not defensible even under time pressure.

#### suggestion: Unused import
**Location:** auth_service.py:14
**Quote:**

```
import hashlib
```

**Read:** The hashlib module is imported but never used in the file.
**Concern:** Unused imports create cognitive noise for future readers (why did the author import this? is there code missing?) and can mask accidental removals of code that was using it.
**Request:** Remove the unused import.

#### note: X-Forwarded-For header lacks trusted-proxy validation
**Location:** http_middleware.py:28-32
**Quote:**

```
def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, respecting X-Forwarded-For header.
    In production, validate that X-Forwarded-For comes from trusted proxy.
    """
    # Check X-Forwarded-For (set by reverse proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (closest to client)
        return forwarded_for.split(",")[0].strip()
```

**Read:** The function trusts X-Forwarded-For headers without verifying they come from a trusted reverse proxy. An attacker can set any X-Forwarded-For value in their request, spoofing their source IP.
**Concern:** In incident response, this is acceptable — the observed attack is from 203.0.113.42, a single IP, so spoofing would only hurt the attacker by redirecting the rate-limit elsewhere. But in the fast-follow hardening (after the immediate incident is contained), this needs to be addressed. IP rate-limiting is only effective if the IP is real.
**Request:** This is a fast-follow concern, not a blocking issue. Document it as a known limitation for the incident phase. In the next cycle, validate X-Forwarded-For against a configured list of trusted proxy IPs.

#### suggestion: Redundant rate-limit check between middleware and handler
**Location:** http_middleware.py:60-68 and http_middleware.py:165-171
**Quote:**

```
// In middleware (lines 60-68):
if auth_service.is_ip_rate_limited(client_ip):
    await _send_error_response(...)
    return

// In handler (lines 165-171):
if error_reason == "rate_limit_ip":
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many login attempts from this IP",
```

**Read:** The middleware short-circuits with an error response if the IP is rate-limited (line 60). If somehow an IP-rate-limited request reaches the handler anyway, the handler also raises an HTTPException for rate-limit (line 167). The rate-limit check in `attempt_login` (auth_service.py line 152) runs a third time. The same invariant is checked three times.
**Concern:** Defensive coding is fine — catching the same condition twice ensures a breach in one layer doesn't sink the check. But redundancy at this scale creates confusion about where the actual check is, and makes future changes harder (if a reader fixes the check in middleware but not the handler, the redundancy becomes a bug). Acceptable for incident response, but worth noting.
**Request:** No change required for this review. Document in a follow-up that the middleware short-circuit is the primary rate-limit check, and the handler check is defensive. Simplify in the next cycle if confidence in the middleware is high.

#### note: Lockout window does not refresh on attempted access during lockout
**Location:** auth_service.py:81-96
**Quote:**

```
def is_account_locked_out(username: str) -> bool:
    key = f"lockout:{username}"
    now = datetime.utcnow()
    
    if key not in _incident_store:
        return False
    
    lockout_entry = _incident_store[key]
    lockout_until = lockout_entry["until"]
    
    if now < lockout_until:
        return True
    
    # Lockout expired; clean up
    del _incident_store[key]
    return False
```

**Read:** When an account is locked out, subsequent login attempts do not extend the lockout window. The `until` timestamp is set once when lockout is triggered (line 121) and is not updated on subsequent failed attempts. The lockout eventually expires based on the original `until` time.
**Concern:** This is correct behavior. Updating the lockout window on each failed attempt would allow attackers to keep accounts locked indefinitely by continuous failed attempts. The current implementation prevents this. However, future readers might expect the lockout to extend on each attempt, so the intent deserves a comment.
**Request:** Add a comment explaining why the lockout window is fixed: 'Lockout window is not refreshed on subsequent attempts; this prevents attackers from keeping accounts locked indefinitely by continuous failures.' Optional; the code is correct without it, but clarity helps future readers.

#### note: Session token is a placeholder, not a real token
**Location:** http_middleware.py:150-154
**Quote:**

```
if success:
    # Return session token (placeholder)
    return {
        "session_token": f"token_{hash(username)}",
        "username": username,
    }
```

**Read:** The session token is `f"token_{hash(username)}"`. This is the same for every login by the same user, and it's derived from the username (a public value). This is obviously a placeholder, not a real token.
**Concern:** In incident response, this is fine — it's clearly a placeholder. But the code comment on line 140 says 'caller should issue session token,' and this code IS the caller, literally issuing a nonsense token. When the session audit layer ships (ADR-002 in the thread), this needs to be replaced with a real token issuer that generates unique, unpredictable tokens. The current placeholder is acceptable because it's obviously wrong; a *plausible-looking* placeholder would be dangerous.
**Request:** When ADR-002 (session audit layer) ships and a real session token issuer is available, replace this placeholder. No change required for this review; the current placeholder is clear enough not to be dangerous.

### Approvals

- The rate-limit and lockout state machines are well-structured. The sliding-window logic correctly limits attempts per IP per minute (auth_service.py:44-73), and the account lockout state machine correctly counts failures in a 5-minute window and prevents re-triggering (auth_service.py:109-124). The invariants are clear and documented.
- The audit log is comprehensive and well-designed for incident investigation. Every login attempt is recorded with timestamp, username, source IP, success/failure, and reason (line 107-112 and elsewhere). The Dormouse and Queen have what they need to parse breach scope.
- The contract between backend and frontend is explicitly named (lines 142-149). The return values are specific: (True, None) on success; (False, 'rate_limit_ip') | (False, 'account_locked') | (False, 'invalid_credentials') on failure. This is good foundation for the Tweedledee contract negotiation.
- The `/incident/status` endpoint is the right interface for operational visibility (http_middleware.py:197-202). It exposes locked_accounts, failing_source_ips, and recent_failures_10min — exactly what the Dormouse and Queen need to monitor the incident in real time.
- HTTP status codes are correct: 429 for rate-limit (RFC 6585), 423 for lockout (WebDAV convention), 401 for invalid credentials (RFC 7235). The Retry-After header on 429 is present and correct.

### Cross-domain references

- The credential validation placeholder (blocking finding) needs clarification from the Queen: what is the source of truth for valid credentials in this incident? Is there a password hash store? OAuth tokens? The answer determines what _validate_credentials should call. Route to Queen for incident-specific ruling.
- The session token issue is an architectural note for the Cat and ADR-002: the current placeholder is safe (obviously wrong), but when session audit ships, the token issuer must generate real tokens. This is a dependency between this code and the session audit layer.
