## Ticket 004: Display clear, actionable error to rate-limited users attempting login

**Sources:** story:locked-out-user-sees-clear-actionable-error-and-knows-what-to-do
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket:implement-rate-limiting-on-login-endpoint-per-queen-ruling
- Soft: —

**Description:**

When a user hits the rate-limit on /login (either from a single-IP bulk attack or their own repeated failed attempts), display an error message that:
1. Names the condition clearly ('Too many login attempts')
2. States the unlock time (e.g., 'Try again in 15 minutes' or 'Account locked for security. Unlock with a verification email.')
3. Offers a path forward (send unlock email, contact support, etc.)
4. Does not expose the rate-limit window duration to the attacker.

The message text and unlock-time UX depend on the Queen's rate-limit ruling and the Cat's visibility-surface confirmation. Work from Alice's story: the user locked out needs to understand what happened and what to do next.

**Acceptance:**
- Error message displays on /login when rate-limit is triggered
- Message includes condition name, unlock time, and next action
- Message does not expose attack details or internal rate-limit parameters
- Tested with both attacker-IP bulk attempts and legitimate user repeated-attempts

**Risk:**

The unlock-time UX (countdown timer, email link, etc.) depends on the Queen's ruling on lockout thresholds and the backend's state tracking. If the backend state is not yet ready when this ships, the frontend may display a time that's out of sync with the backend. Confirm the backend's lockout-state artifact is available before finalizing the message.
