## Story 005: Delete my account and have all my data purged (GDPR)

**Persona:** Kai, 19, in the EU. Signed up, used the platform for a month, decided it wasn't for them. Now wants out completely — no trace.

**Situation:**

Kai submitted a deletion request. They want to know: when they click 'delete my account,' is their data *really* gone? No backups hiding it, no email archives, no logs with their content?

**Need:**

As Kai, I want to delete my account and have all my personal data, including my homepage and any information about me, permanently removed from the system, so that I have control over my digital footprint.

**Acceptance:**
- Account deletion is accessible from account settings (no buried link)
- Deletion requires password confirmation or email confirmation (not just a checkbox)
- After deletion: homepage is no longer accessible (returns 404)
- After deletion: username is no longer listed in directory
- After deletion: any comments or activity Kai created (if applicable) are purged or anonymized
- Deletion is immediate (not a 30-day grace period) for GDPR compliance

**Tier:** core

**Confusion-flags:**
- GDPR is complicated and the directive mentions it but doesn't specify the legal framework. Is there a Data Processing Agreement with users? A Privacy Policy? Those are not my domain, but they affect Kai's trust. This feels like a Queen of Hearts question.
- Backups and logs: if Kai's data is in database backups, do those backups need to be purged too, or is 'live deletion' enough for GDPR? This is a security/compliance decision I can't make, but it affects the deletion UX.
