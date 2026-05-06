## Story 004: User can create an account and log in with basic auth

**Persona:** Sarah (same as above), but first-time user. Needs to get an account before she can chat.

**Situation:**

Sarah has never used the translation-chat app before. She lands on the homepage and needs to sign up, create a password, and then log back in. She wants this friction-free.

**Need:**

As Sarah, I want to create an account with my email and a password, then log in with those credentials, so that my conversations are tied to me and I can access them later.

**Acceptance:**
- Sarah can click a signup link or form
- Sarah provides: email address, password (and password confirmation), optionally a display name
- The system validates the email (not already in use) and stores the account securely
- Sarah can log in with email + password and see her conversation list
- Sarah stays logged in across browser sessions (cookie/token handled)
- Sarah can log out

**Tier:** core

**Confusion-flags:**
- GDPR is noted in the directive (EU consumer scope). Does signup need explicit consent to store data? Does account creation need a privacy policy link? I'm flagging this for the Queen — it's her domain, not mine, but it blocks signup UX.
- Password reset is not mentioned. If Sarah forgets her password, what happens? Probably out of scope for MVP, but should be documented as a known gap.
- Is there a 'display name' separate from email? The stories above use 'Sarah' and 'Klaus' as identifiers; are those display names the user sets, or are they derived from email? Not specified.
