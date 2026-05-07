## Scenario 006: Verification token is single-use; reuse fails or is idempotent

**Severity:** silent-wrongness

**Setup:**

User registers (verified=false). Verification token issued and stored server-side with TTL.

**Trigger:**

User verifies successfully (token consumed). Same token used again in a second verify request.

**Expected:**

Second verify fails (400/401 'token_consumed') or succeeds idempotently. No silent reuse accepted.

**Concern:**

If token consumption is not tracked, stolen tokens can be reused, creating an authorization bypass window where attackers can re-verify accounts.

**Property:**

For all verification tokens T and users U: if T verifies U once, subsequent uses either fail (400/401) or succeed idempotently (no side effects). A leaked token cannot verify a different user.
