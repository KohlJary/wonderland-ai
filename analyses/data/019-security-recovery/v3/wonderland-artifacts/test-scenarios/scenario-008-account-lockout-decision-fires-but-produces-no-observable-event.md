## Scenario 008: Account-lockout decision fires but produces no observable event

**Severity:** silent-wrongness

**Setup:**

AuthService initialized with account lockout (5 failures threshold). Single email makes 5 failed login attempts from various IPs.

**Trigger:**

5th failed login attempt on the same email, crossing the lockout threshold.

**Expected:**

The 5th attempt triggers the lockout and returns reason='account_locked'. A metric or event is emitted to production telemetry (e.g., 'auth.account_locked' counter, tagged with email hash and timestamp). Subsequent 6th attempt confirms account is locked.

**Concern:**

The current implementation calls record_failure(), which increments the counter and locks the account, but does not emit any observable signal. Production has no way to detect that an account was just locked or how many accounts are currently locked. Dormouse cannot implement breach-notification logic (which requires knowing which accounts were targeted) without telemetry on lockout events.

**Property:**

For all account lockouts L, there exists an observable event E such that E records (email_hash, lockout_timestamp, locked_until) and can be aggregated into a metric tracking lockout rate and duration.

**Implies:**
- Requires instrumentation hook in AccountLockout.record_failure() to emit events when lockout is triggered.
- Dormouse owns the contract for email hashing strategy (protect PII while enabling incident debugging).
