## Scenario 009: Successful login after lockout resets state but produces no observable recovery event

**Severity:** degradation

**Setup:**

Account is locked (5 failed attempts recorded). Lockout duration is set to auto-expire after N minutes. Time passes and lockout window expires. User successfully logs in.

**Trigger:**

Successful login attempt after the lockout_until timestamp has passed.

**Expected:**

Login succeeds, AccountLockout.record_success() clears the failure counter. An observable recovery event is emitted (e.g., 'auth.account_unlocked', tagged with email_hash and reason='successful_login').

**Concern:**

The current implementation clears the lockout state (via pop()) but does not emit any signal. Production cannot track whether locked accounts are recovering naturally (lockout expiry + successful login) vs. being manually unlocked by admins. This is important telemetry for understanding attack impact and user pain.

**Property:**

For all lockout clearances C (whether via expiry, successful login, or admin reset), there exists an observable event E that records the reason and timestamp, enabling incident forensics.

**Implies:**
- Requires instrumentation in AccountLockout.record_success() and unlock_account().
