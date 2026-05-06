## Story 009: User discovers post-incident that their password was in the upstream breach list, even though they were never attacked during this incident

**Persona:** Casey, 42, long-time user of the service, knows their password is their password (uses the same one everywhere). They weren't on the attack path during the credential-stuffing incident, but their password appears in the leak list that the attackers were using.

**Situation:**

Post-incident, the service publishes a security advisory: 'We were targeted with a credential-stuffing attack. Your password may have been in the breach list. You may want to change it.' Casey reads this and realizes: my password is compromised, even though I wasn't attacked here. I'm now thinking about every other service where I use this password, and I'm anxious.

**Need:**

As Casey, I want to change my password immediately as part of the incident recovery, and I want the service to confirm that I've done so and my account is secure again, so that I can close the loop and stop worrying.

**Acceptance:**
- Post-incident advisory identifies users whose passwords were in the breach list (distinct from users who were attacked)
- Casey can change their password without being forced into an unlock flow they don't need
- After password change, Casey receives confirmation that their account is now secure again
- The service does not imply that the old password will still work after the advisory period (social engineering protection)

**Tier:** enrichment

**Confusion-flags:**
- We're telling users about a breach that didn't breach them. This is good transparency, but it's also a channel for anxiety and false urgency.
- If Casey's password is in the upstream breach list but we never saw an attack attempt with it, how did we discover that fact? Did we have the breach list, or did we infer it?
- This story assumes we can identify which users were in the breach list and which weren't. The Rabbit's tickets don't include that capability. Is this a fast-follow or a pre-requirement for the advisory?
