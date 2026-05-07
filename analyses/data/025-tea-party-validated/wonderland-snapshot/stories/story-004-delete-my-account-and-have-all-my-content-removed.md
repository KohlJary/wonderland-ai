## Story 004: Delete my account and have all my content removed

**Persona:** Sam, 29, a EU resident (GDPR scope). They decided this platform wasn't for them and want to leave cleanly. They don't want their page lingering or any of their data sitting on someone's server.

**Situation:**

Sam's account has been dormant for a month. They're logging in to close it out.

**Need:**

As Sam, I want to delete my account and know that all my content, pages, and personal data are completely purged from the system, so that I can trust this platform respects my right to be forgotten.

**Acceptance:**
- There is a 'Delete Account' button in account settings
- Clicking it requires a confirmation (or email confirmation) to prevent accidents
- My page is immediately inaccessible (returns 404 or 'page deleted')
- My username becomes available for someone else to claim
- All my data is purged within [X days] per GDPR (I assume EU law specifies this; Queen of Hearts will know)
- I receive an email confirming deletion

**Tier:** core

**Confusion-flags:**
- GDPR is mentioned but I don't know the exact retention windows or what 'purge' means operationally. Is this backups, logs, comments by others on my page? The Queen of Hearts needs to clarify.
- If someone else has linked to my page before deletion, their link will break. Is that acceptable, or do we need redirect/archival logic?
- If I delete and someone else claims my username, can they see any cached or archived version of my old page? (Probably not, but the definition of 'purge' matters.)
