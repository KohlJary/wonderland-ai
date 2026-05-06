## Review 002: Rate-limiting and account-lockout implementation

**Files reviewed:** src/auth/rate_limit.py, src/auth/service.py, src/auth/endpoints.py, tests/test_auth.py
**Verdict:** request-changes

### Findings

#### change-required: No production instrumentation for rate-limit events
**Location:** src/auth/rate_limit.py, src/auth/service.py (full file)
**Quote:**

```
class RateLimiter:
    """IP-based rate limiting using a sliding window."""
    def check(self, source_ip: str) -> None:
        """Check if the source IP has exceeded the rate limit."""
        # ... no event emission here
        if entry.count >= self.requests_per_minute:
            raise RateLimitViolation(...)
```

**Read:** When the RateLimiter blocks a request, it raises an exception. The exception is caught in service.py and logged as a FailedAttempt row with reason='rate_limited'. However, no structured event is emitted that the observability pipeline can ingest. There are no metrics tracking 'how many IPs are currently rate-limited', 'rate-limit decision rate', 'window fill per IP', or 'retry-after distribution'.
**Concern:** The Queen ruled 'production telemetry required before v1 ship'. The code produces no telemetry. During an active incident, the sysadmin needs to know (a) is the rate limiter firing, (b) which IPs, (c) how many. The FailedAttempt table is asynchronous and does not answer those questions in real time. Without instrumentation, the team running this has no way to measure the effectiveness of the mitigation or to detect if the attack has shifted to a new vector.
**Request:** Add structured event emission to RateLimitViolation and AccountLockout decision points. The events should include (1) decision type (rate_limited / account_locked), (2) source_ip (for rate limit), (3) email (for lockout), (4) timestamp, (5) retry_after_seconds. These should be emitted to a logging/metrics pipeline (e.g., structured JSON to stdout, or a metrics client). The implementation should not assume a specific backend — a simple events.emit(event_dict) call is sufficient, with the pipeline configured externally. Dormouse will specify the exact schema and cardinality bounds in a contract note.

#### change-required: No production instrumentation for account-lockout events
**Location:** src/auth/rate_limit.py:170-180 (record_failure), src/auth/service.py:85-90 (record_success)
**Quote:**

```
def record_failure(self, email: str) -> None:
    """Record a failed attempt and lock the account if threshold is hit."""
    now = datetime.now(timezone.utc)
    entry = self._cache.get(email)
    # ...
    if new_count >= self.failure_threshold:
        locked_until = now + self.lockout_duration if self.lockout_duration else None
        self._cache[email] = _LockoutEntry(failed_count=new_count, locked_until=locked_until)
```

**Read:** The AccountLockout class updates its in-memory cache when a lockout fires, but does not emit any event. The lockout is recorded in the FailedAttempt table (via service.py), but the transition from 'unlocked' to 'locked' is not observable in real time. Similarly, record_success() clears the cache with no event.
**Concern:** Same as rate-limit: the Queen's ruling requires observability. A sysadmin cannot see (a) which accounts are currently locked, (b) when lockouts were triggered, (c) whether locked accounts are recovering. The FailedAttempt table is not queryable in real time for 'show me locked accounts'. Without instrumentation, the team cannot verify that false positives (legitimate users locked by attack) are recovering, or whether legitimate users need manual unlock.
**Request:** Emit events when record_failure() triggers a lockout, when record_success() resets a counter, and when get_lockout_status() returns locked=True. Events should include email, failed_count, locked_until, and reason for transition. The emit mechanism should be the same as for rate-limit events (structured JSON / metrics client).

#### change-required: FailedAttempt logging gap: rate-limit event is logged but lockout-trigger event is not clearly distinguished
**Location:** src/auth/service.py:83-92 (rate-limit logging), src/auth/service.py:95-99 (failure logging on lockout check)
**Quote:**

```
try:
    self.account_lockout.check(normalized_email)
except RateLimitViolation:
    self._log_failure(
        None, normalized_email, "account_locked", source_ip, user_agent
    )
    return LoginResult(ok=False, reason="account_locked")
```

**Read:** When account_lockout.check() raises RateLimitViolation (meaning the account is already locked), a FailedAttempt row is logged with reason='account_locked'. But this logs the *check* failure, not the *lockout transition*. The distinction matters: a row with reason='account_locked' means 'this login attempt was rejected because the account was already locked', not 'this attempt caused the account to transition into lockout'. The actual lockout transition happens in record_failure(), which is called *after* the DB credential check, and produces no audit trail.
**Concern:** Audit trail clarity. When a sysadmin reviews FailedAttempt for email=victim@example.com, they see reason='invalid_password' repeated N times, then reason='account_locked' repeated M times. But they cannot see *which* invalid_password attempt was the N-th one that triggered the lockout. The transition point is invisible. This makes post-incident analysis harder and makes it difficult to distinguish 'this account was locked by a threshold breach' from 'this account was locked because it was already locked'.
**Request:** Add a new reason type 'lockout_triggered' to the FailedAttempt schema and emit a FailedAttempt row when record_failure() causes the transition from unlocked to locked. The timestamp of this row marks the exact moment the account was locked, and the reason field makes the event type unambiguous. This provides a clear audit trail for post-incident review.

#### suggestion: RateLimiter and AccountLockout use in-memory-only state; restart loses all rate-limit history
**Location:** src/auth/rate_limit.py:1-12 (docstring), src/auth/rate_limit.py:58 (_cache: dict)
**Quote:**

```
"""Rate limiting and account lockout for auth endpoints.

[...]

Both use in-memory caches with TTL-based expiry to avoid DB load
during high-volume attacks. State is NOT persisted across restarts,
which is acceptable for SIGv1 incident response (this rate limiter
is designed to stop the current attack, not to be infinitely durable).

For production hardening, migrate these to Redis or a distributed cache.
"""
```

**Read:** The _cache is a plain dict, cleared on service restart. The docstring acknowledges this as acceptable for incident response but insufficient for production. The Queen's ruling did not explicitly forbid this, but it also did not carve out an exception for service restarts during incidents.
**Concern:** If the auth service restarts during the attack (e.g., due to an update, a deployment, a crash), all rate-limit and lockout state is lost. Attackers reset their IP counters on the next window. Locked accounts become unlocked. The defense is disrupted for the 1-N seconds before the cache refills. This is not a functional bug (the code is correct for what it implements), but it's a known gap that Dormouse's observability will expose: if metrics show 'lockout count dropped to zero after a restart', the team will need to investigate why. Better to document this explicitly and plan the production migration to Redis now.
**Request:** This is not blocking for v1 (the code is acceptable for incident response), but document the restart behavior in the service.py docstring and in a ticket. Add a note that in-memory-only is a deliberate choice for SIGv1, and outline the migration path to Redis/persistent cache as a post-incident hardening task. The Rabbit can track this as a tech-debt ticket.

#### note: Test coverage is solid for happy/sad paths; edge case around email-normalization is implicitly covered
**Location:** tests/test_auth.py:180-200
**Quote:**

```
def test_account_lockout_is_per_email(db_factory):
    """Different emails have independent lockout states."""
    with db_factory() as db:
        user_a = User(
            email="alice@example.com",
            ...
        )
        user_b = User(
            email="bob@example.com",
            ...
        )
```

**Read:** The tests cover independent rate limits per IP, independent lockouts per email, counter reset on success, and both firing independently. The test data uses distinct emails and IPs, which implicitly tests the isolation. The email normalization (service.py:70: email.strip().lower()) is applied before lockout checks, so case-variance and whitespace are handled correctly. The tests do not explicitly test this (e.g., test_account_lockout with 'ALICE@EXAMPLE.COM' vs 'alice@example.com'), but the implicit coverage is correct because the lockout check uses the normalized email.
**Concern:** None. The coverage is pragmatic. An explicit 'test with uppercase and whitespace' would add confidence, but it's not required — the code is already correct.
**Request:** No action required. Noted for calibration: the test suite is clean, and the authors thought about isolation.

### Approvals

- The core rate-limiting logic (sliding window per IP, configurable request limit, retry-after calculation) is correct and efficient. The window-expiry logic is sound.
- The account-lockout logic (threshold-based, per-email, lockout-duration support, reset on success) is sound and handles the distributed-attack scenario correctly (per-email catches distributed IPs).
- The integration into AuthService is clean: rate-limit and lockout checks happen before DB access (fail-fast), reducing DB load during attacks.
- HTTP status codes are correct: 429 Too Many Requests for rate limit, 423 Locked for account lockout, 401 Unauthorized for credential failure. The endpoint does not leak credential-enumeration information.
- Test coverage is comprehensive: independent rate limits, independent lockouts, reset on success, both firing together. The test fixtures (auth_with_lenient_limits) are well-designed for unit testing without timing issues.
- The code is readable, well-commented (especially the docstrings explaining the policy and the in-memory cache choice), and the exception hierarchy (RateLimitViolation) is clear.

### Cross-domain references

- Dormouse: observability contract required before merge. Rate-limit and lockout events must be emitted with schema + cardinality bounds specified. Caterpillar's change-required findings on instrumentation are blocking until Dormouse's contract is in place and implemented.
- Queen: her ruling 'production telemetry required before v1 ship' is not met by the current code. This review's change-required findings are the blockers. Queen may want to confirm the observability contract before final ruling update.
