## Review 004: Rate-limiting and account-lockout implementation

**Files reviewed:** src/auth/rate_limit.py, src/auth/service.py, src/auth/endpoints.py, tests/test_auth.py
**Verdict:** request-changes

### Findings

#### block: Observable events for rate-limit and lockout decisions missing
**Location:** src/auth/rate_limit.py:78-116 (RateLimiter.check); src/auth/rate_limit.py:188-220 (AccountLockout.check)
**Quote:**

```
if failure_count >= self.ip_max_failures:
            # Calculate when the window will expire
            oldest_failure = self._get_oldest_failure_for_ip(source_ip)
            if oldest_failure:
                window_expires = oldest_failure + timedelta(minutes=self.ip_window_minutes)
                retry_after = max(0, int((window_expires - now).total_seconds()))
            else:
                retry_after = self.ip_window_minutes * 60

            raise RateLimitViolation(
                RateLimitStatus.IP_THROTTLED,
                retry_after_seconds=retry_after,
            )
```

**Read:** When a rate-limit or lockout threshold is exceeded, the code raises an exception (which is correct flow control), but produces no observable signal that this decision was made. There are no log statements, no metrics emissions, no event records. In production, a monitoring system cannot see that a rate-limit decision just fired.
**Concern:** The Queen ruled (ruling #3) that 'production telemetry required before v1 ship.' The Dormouse flagged that this observability is load-bearing for breach-notification work — we need to know which accounts succeeded during the attack window so we can notify users. The FailedAttempt table records credential failures, but rate-limit and lockout events are invisible. Scenarios 1, 2, and 6 from the Hatter explicitly name this gap: rate-limit decision fires but produces no observable event; lockout decision fires but produces no observable event; successful login during active attack is not distinguished from normal login. Without observability, production stays dark during the next attack, and the breach-notification ruling cannot be executed.
**Request:** Add observable instrumentation for rate-limit and lockout events. This can take the form of: (a) log statements at INFO level when a rate-limit or lockout check fires, (b) a separate telemetry event emission (if you have a metrics/observability system), or (c) database records that distinguish rate-limit/lockout events from credential failures in the FailedAttempt table. The Dormouse should write a contract specifying exactly what needs to be observable (which I expect they are doing in parallel ticket #11). Before implementation resumes, coordinate with Dormouse on the exact shape — what fields, what cardinality, what query pattern will support breach-notification determination? Once the contract is locked, emit the events according to that contract.

#### block: Successful login events during attack window are not observable
**Location:** src/auth/service.py:117-127
**Quote:**

```
            # Success — create session and reset failure counters.
            session = Session.make(
                user_id=user.id, source_ip=source_ip, user_agent=user_agent
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            # Successful login resets the lockout counter for this email.
            self.account_lockout.record_success(normalized_email)
```

**Read:** When a login succeeds, the code creates a session and resets the lockout counter. But there is no observable event recorded that a login succeeded at this time, from this IP, for this user. A successful login after the attack window is indistinguishable from a normal login in any production telemetry system.
**Concern:** The Queen's breach-notification ruling (ruling #2) depends on knowing which accounts had their credentials successfully used during the attack window. The Hatter's scenario #6 names this explicitly: 'successful login during active attack is not distinguished from normal login in observability.' The FailedAttempt table only records failures; it does not record successes. Without a way to query 'which accounts had successful logins between T1 and T2' we cannot determine which users to notify about compromise. This is not a monitoring nice-to-have — it is load-bearing for compliance.
**Request:** Add observable event or log record when a login succeeds. This could be: (a) a log statement at INFO level, (b) a separate 'SuccessfulAttempt' table or event stream, or (c) a flag in FailedAttempt that distinguishes attempts by outcome. Coordinate with the Dormouse on the exact shape. The contract should support querying: 'Give me all successful logins for any user between time T1 and T2' so that breach-notification work can determine which accounts were compromised.

#### change-required: No instrumentation for manual lockout reset operations
**Location:** src/auth/rate_limit.py:264-268 (AccountLockout.record_success)
**Quote:**

```
    def record_success(self, email: str) -> None:
        """Record a successful login for an email; resets the failure counter.

        Args:
            email: normalized email address
        """
        # Clear in-memory state for this email
        if email in self._failure_counts:
            self._failure_counts[email] = 0
            self._failure_times[email] = []
```

**Read:** When a successful login resets the lockout counter, the in-memory state is cleared but there is no record that this recovery event occurred. If an operator or the system manually unlocks an account, that action is invisible.
**Concern:** The Hatter's scenario #4 flags this: 'Admin manually resets rate-limit or lockout but change is invisible to monitoring.' During an active incident, SREs need to know when they've unlocked accounts so they can track recovery progress and alert users. Without visibility into unlock operations, the Dormouse cannot audit the incident response.
**Request:** Add an observable event when lockout is reset (either by successful login or by manual intervention). This should record the email, the unlock timestamp, and the reason (successful_login vs. manual_reset). The Dormouse's contract (ticket #11) should specify the exact format. This is secondary to the rate-limit and successful-login observability, but it completes the picture.

#### suggestion: Password-reset endpoint interaction undefined
**Location:** src/auth/service.py:1-3
**Quote:**

```
"""AuthService — login, logout, session lookup. Backed by a SQLAlchemy
session factory. Includes rate limiting (per IP) and account lockout
(per email) as of the incident response in thread incident-response.
```

**Read:** The docstring says AuthService includes rate limiting and lockout, which is correct. But there is no mention of how these controls interact with a password-reset endpoint (which does not yet exist). When /password-reset ships, will it share the same rate-limit namespace as /login?
**Concern:** The Queen ruled (ruling #1) that 'password-reset endpoint must have separate rate-limit policy from login.' The Hatter's scenario #5 flags the danger: if a locked user tries to reset their password and hits the same rate limiter, they become permanently locked and unable to recover. This is not yet blocking (since /password-reset doesn't exist), but the contract should be explicit now so that when password-reset ships, the implementation doesn't silently reuse the login rate limiter.
**Request:** Add a docstring or code comment that explains the architectural contract for password-reset rate limiting. Something like: 'Note: when /password-reset endpoint is implemented, it must have separate rate-limit controls from /login to allow locked users to self-recover. The rate_limiter and account_lockout objects in this class are scoped to login flow; password-reset must instantiate its own controls or use explicitly separate thresholds.' This is a contract note, not a code change — but it prevents future drift.

### Approvals

- The rate-limiting logic is sound: IP-based sliding-window enforcement with proper window-expiration calculation. The per-IP threshold (10 failures in 15 minutes) matches the Queen's ruling.
- The account-lockout logic is correct: per-email threshold-based lockout with exponential backoff via retry_after calculation. The 5-failure threshold and 30-minute window are appropriate for incident response.
- Both controls are DB-backed via FailedAttempt queries, which provides durability across service restarts and central enforcement across instances. The indexed lookups on (source_ip, occurred_at) and (email, occurred_at) are the right approach.
- The test coverage is comprehensive: 10+ new tests cover rate-limiting per-IP independence, lockout per-email independence, interaction between the two controls, successful login resetting counters, and edge cases. The tests are well-named and the fixtures (auth_with_lenient_limits) support controlled testing.
- The endpoint integration in endpoints.py correctly maps failure reasons to HTTP status codes (429 for rate-limited, 423 for locked, 401 for credential failure). The Retry-After headers are correctly calculated and included.
- The in-memory caching in AccountLockout (failure_counts, failure_times) is a reasonable optimization for fast-path checks before hitting the DB, and the code correctly reconstructs state from the DB on restart.

### Cross-domain references

- Dormouse owns observability: the rate-limit and lockout events must be defined in Dormouse's contract (ticket #11) before this implementation adds instrumentation hooks. Coordinate on: what fields are required, what cardinality bounds, what query patterns will support breach-notification work.
- Queen's ruling #3 (observability required before v1 ship) is blocking this implementation. The findings above name exactly what observability is missing. Before merge, the Dormouse and Tweedles need to align on the contract, and the implementation needs to emit events according to that contract.
- Alice (user-experience) flagged that successful-login observability is load-bearing for breach-notification work (ruling #2). Without it, the team cannot execute the user-notification ruling.
