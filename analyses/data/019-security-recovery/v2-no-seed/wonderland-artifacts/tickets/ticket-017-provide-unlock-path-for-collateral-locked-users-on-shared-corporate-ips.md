## Ticket 017: Provide unlock path for collateral-locked users on shared corporate IPs

**Sources:** story: legitimate-user-on-shared-ip-discovers-they-are-collateral-locked-during-attack
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 4-6 hours, 65% confident; depends on whether email-based recovery already exists in codebase
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket: resolve-account-recovery-primitive-availability-and-threat-model-requirements
- Soft: ticket: implement-account-recovery-primitive-validate-email-ownership-for-unlock-authorization

**Description:**

Users on shared corporate IPs (office networks, ISP-assigned ranges) will be collateral-locked by the rate-limit on /login, even though they are not part of the attack. The current rate-limit has no way to distinguish a legitimate user from an attacker if both originate from the same IP. This ticket is a unlock path for verified account owners — prove you own the account (via email token, SMS code, or security question) and regain access regardless of the IP-based rate-limit state. This is v1 only if the team decides collateral damage is unacceptable; it can be fast-follow if the team accepts the collateral damage as the cost of incident response speed.

**Acceptance:**
- Legitimate user on shared IP can unlock their account by proving ownership (email token, SMS, or security question)
- Unlock path is available within 5 minutes of user attempting to access account
- Attacker cannot unlock stolen accounts using this path (second factor is independent of password)
- User receives clear messaging about why they are locked and how to regain access

**Risk:**

If email/SMS recovery primitives do not exist in the codebase, this ticket expands to 8-12 hours. If collateral-damage acceptance threshold is undefined, this ticket may ship in v1 or fast-follow depending on business decision mid-turn.
