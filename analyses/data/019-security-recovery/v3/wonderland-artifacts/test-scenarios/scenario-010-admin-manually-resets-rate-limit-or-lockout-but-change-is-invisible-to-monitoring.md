## Scenario 010: Admin manually resets rate-limit or lockout but change is invisible to monitoring

**Severity:** degradation

**Setup:**

Rate limiter has IP A rate-limited; account lockout has email E locked. Admin calls reset_ip() and unlock_account() to remediate.

**Trigger:**

reset_ip('203.0.113.42') and unlock_account('alice@example.com') are called.

**Expected:**

The caches are cleared. An observable event is emitted for each reset (e.g., 'auth.rate_limit_reset' and 'auth.account_unlocked' with reason='admin_reset', tagged with admin_id/timestamp).

**Concern:**

The current implementation pops the keys from the dict but does not emit signals. During incident response, when the SRE manually resets rate limits or unlocks accounts, Dormouse has no visibility into these actions. This makes incident forensics harder and creates a gap where an attacker could claim 'the unlock failed' without telemetry to prove otherwise.

**Property:**

For all admin-initiated resets R, there exists an observable audit event A that records the action, actor, target, and timestamp.

**Implies:**
- Requires instrumentation in RateLimiter.reset_ip() and AccountLockout.unlock_account().
- May require passing an admin_id or actor context into these methods.
