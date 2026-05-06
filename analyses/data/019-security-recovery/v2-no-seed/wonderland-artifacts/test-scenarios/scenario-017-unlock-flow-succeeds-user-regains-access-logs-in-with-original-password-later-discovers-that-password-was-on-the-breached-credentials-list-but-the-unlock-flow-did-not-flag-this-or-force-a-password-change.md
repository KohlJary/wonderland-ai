## Scenario 017: Unlock flow succeeds, user regains access, logs in with original password, later discovers that password was on the breached-credentials list but the unlock flow did not flag this or force a password change

**Severity:** silent-wrongness

**Setup:**

User's password is in the 4,127 attempted credentials from the attack. They were not directly attacked (their account was not targeted) but their credential is live in an attacker's list. User is collateral-locked via IP-based rate-limit. User requests unlock via email/SMS, receives valid token, submits token, unlock succeeds. User logs in with their original password (which is still on the breached list). User is authenticated and logged in. Later, user receives a breach-notification email indicating their password was in a leaked list.

**Trigger:**

User successfully unlocks account and logs back in with the same password that is on the breached credentials list.

**Expected:**

Unlock endpoint confirms the password is safe to use, or upgrade the unlock flow to include a 'change password' step if we know the password was compromised. If the password is on the breach list, force a password change as part of the unlock flow, not as a downstream notification.

**Concern:**

The unlock flow is designed to re-authorize the account owner (email/SMS proves they control the account). But it does not cross-check whether the password itself is compromised. We ship the unlock, the user regains access with a live-compromised password, and they discover the compromise later via notification, not via the unlock UX. The unlock flow appears to work (user is authenticated and logged in), but a layer of risk is hidden: the user is authenticated with a password that is known-compromised and live in an attacker's database. This is silent wrongness because the user's account *is* recovered, but the recovery is incomplete.

**Property:**

For all users U who unlock successfully, if password(U) is on the breached-credentials list, then the user must not regain login access with that password. Either the unlock flow prevents login with a breached password, or it forces password change as a precondition of regaining access.

**Implies:**
- Implies architectural decision about whether the unlock flow includes password-change logic. This is the Cat's domain — does ADR-001 (unlock authorization) scope to include password-change as a conditional step, or is password-change a separate downstream flow?
- Implies observability concern for Dormouse: once we know which credentials succeeded during the attack (Queen's investigation), we need telemetry on 'user unlocked with a breached password' to detect whether this silent-wrongness scenario is actually biting users.
