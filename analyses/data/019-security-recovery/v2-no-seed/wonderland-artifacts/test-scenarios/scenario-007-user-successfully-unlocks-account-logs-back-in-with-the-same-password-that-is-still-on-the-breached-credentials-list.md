## Scenario 007: User successfully unlocks account; logs back in with the same password that is still on the breached-credentials list

**Severity:** silent-wrongness

**Setup:**

User's password was in the 4,127 attempted credentials. The attack was halted before any succeeded against their account. User receives unlock email, clicks token, resets nothing (because they don't know their password is compromised), and logs back in with the original credential. The session is now live and valid, but the password is known to the attacker.

**Trigger:**

User completes unlock flow and logs in without changing password.

**Expected:**

System should detect that the user's password is on the known-breached-list and either: (a) force an immediate password-change as a condition of unlock, or (b) flag their session with elevated monitoring and alert them post-login that their password was in the breach list and offer forced change.

**Concern:**

Alice's story says 'regain access without friction.' But if we let users regain access with a known-compromised password, we have not actually solved their problem—we have just hidden it. The friction of forced password-change is real but necessary. If we skip it, the user thinks they are safe and they are not.

**Property:**

For all accounts A that were unlock-targets during the attack window and whose passwords P are on the breached-credentials list, access to A must be preceded by either (a) P being reset, or (b) active notification that P is compromised and immediate change required.

**Implies:**
- Implies architectural decision: does the unlock flow have visibility into the breached-credentials list? Does it enforce password-change? Needs Cat clarification before Tweedledee ships unlock UX.
- Implies Alice's story 'regain access' acceptance criteria: does 'regain' mean 'regain with uncompromised credentials' or just 'regain the account'? Story needs refinement based on this scenario.
