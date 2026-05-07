## Ticket 011: Account deletion and GDPR data purge

**Sources:** delete-my-account-and-have-all-my-data-purged-gdpr
**Owner:** Tweedledum
**Tier:** post-launch
**Estimate:** 1–2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: account-settings-view
- Soft: —

**Description:**

Post-launch: User can delete their account via settings. Deletion cascades: user record, homepage content, session tokens, email verification records are all purged. Slug is freed for reuse (or reserved for 30 days to prevent impersonation, per security review). User receives a confirmation email before purge is irreversible.

**Acceptance:**
- User can request account deletion from settings
- Confirmation email is sent
- User must click link in email to confirm
- On confirmation: user record, content, sessions are deleted
- Slug is either freed or reserved per compliance guidance
- User receives a final 'goodbye' email

**Risk:**

Data retention obligations; Queen must review for compliance before ship. Consider audit logging of deletes.
