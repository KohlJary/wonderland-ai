## Story 004: Visit someone else's homepage and know it's real

**Persona:** Alex, 30, skeptical about the internet. When they find a homepage, they want to know it's really from a human, not a bot or corporate spam account.

**Situation:**

Alex clicked on a recent user in the directory and landed on a homepage. The page looks real, but has no indication of when it was created or when it was last updated.

**Need:**

As Alex, I want to see when a homepage was created and when it was last updated, so that I can tell if this is an active, real person or an abandoned/spam account.

**Acceptance:**
- Every public homepage shows 'Created on [date]' (e.g., 'Created on Nov 15, 2024')
- Every public homepage shows 'Last updated on [date]' (e.g., 'Last updated 2 days ago')
- Dates are human-readable and not too granular (day is fine; seconds is not)

**Tier:** core

**Confusion-flags:**
- Trust signals matter more here than just metadata. If we don't show update timestamps, the site will feel dead or artificial. If we do, it feels alive and real to visitors like Alex.
