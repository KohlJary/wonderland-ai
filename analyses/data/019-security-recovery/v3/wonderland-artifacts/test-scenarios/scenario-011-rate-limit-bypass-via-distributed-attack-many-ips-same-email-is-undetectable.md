## Scenario 011: Rate-limit bypass via distributed attack (many IPs, same email) is undetectable

**Severity:** silent-wrongness

**Setup:**

AttackerA makes 5 login attempts on alice@example.com from IP 203.0.113.1. AttackerB (or same attacker, different IP) makes 5 more from IP 203.0.113.2 (same minute). Alice's account is locked after 5 total failures.

**Trigger:**

Alice's 5th failed attempt (from the 2nd attacker IP).

**Expected:**

Alice's account locks. An observable metric on 'failed_attempts_per_email' (NOT per IP) increases to 5, enabling post-incident analysis: 'which emails were targeted across multiple IPs?' Without this metric, the distributed-attack pattern is invisible.

**Concern:**

The current rate-limit and lockout implementation is correct (per-IP rate limiting catches single-source bulk attacks; per-email lockout catches distributed enumeration). But there is no metric that aggregates failed attempts per email across all IPs. Production cannot distinguish between 'Alice made 5 typos from home and the office' (benign) and 'Alice was targeted by a distributed attack' (malicious). This is critical for breach notification: 'was this email targeted by a coordinated attack?'

**Property:**

For all accounts A, there exists an observable time-series metric M(A, window) = count of distinct IPs from which failed attempts were made on A within window, enabling attacker-pattern detection.

**Implies:**
- Requires a new instrumentation layer that aggregates FailedAttempt audit records into production metrics, not just raw event emission.
