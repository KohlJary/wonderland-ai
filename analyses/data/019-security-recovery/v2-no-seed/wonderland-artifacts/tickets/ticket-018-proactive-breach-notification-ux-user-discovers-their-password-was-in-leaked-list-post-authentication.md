## Ticket 018: Proactive breach-notification UX: user discovers their password was in leaked list post-authentication

**Sources:** story: user-discovers-their-password-was-in-the-leaked-list-but-they-weren-t-on-the-attack-path
**Owner:** Tweedledee
**Tier:** fast-follow
**Estimate:** 2-3 hours, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket: investigate-whether-any-of-the-4-127-attempted-credentials-succeeded-parse-audit-trail-for-successful-logins
- Soft: —

**Description:**

Once the Dormouse completes breach investigation and confirms which of the 4,127 attempted credentials succeeded, users whose credentials were compromised need to know. This ticket adds a post-authentication notification: after login succeeds, if the user's credential was confirmed to be in the leaked list, display a prominent banner ('Your password was exposed in a recent incident; change it now') with a link to password-change flow. This is fast-follow because it depends on the Dormouse's forensic investigation completing; it cannot ship until we know which credentials actually succeeded.

**Acceptance:**
- User whose credential was confirmed in the 4,127 attempted list sees breach-notification banner post-login
- Banner includes clear explanation of what happened and actionable next steps (change password, monitor account)
- Notification only appears if user's credential was actually attempted (not blanket notification to all users)
- User can dismiss notification and use their account; dismissal does not prevent re-prompting on next login

**Risk:**

If Dormouse's investigation finds no successful credentials, this ticket becomes moot and can be closed as 'incident scope resolved.' If investigation finds widespread success, this ticket may need to be promoted to v1 depending on Queen's ruling on breach-notification timeline.
