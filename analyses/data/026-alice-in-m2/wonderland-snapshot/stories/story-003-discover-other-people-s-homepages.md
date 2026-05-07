## Story 003: Discover other people's homepages

**Persona:** Priya, 25, curious about internet culture and indie web. Likes stumbling on small, personal sites. Wants to find 'things that are real' made by humans, not algorithms.

**Situation:**

Priya has a homepage herself. She wants to find other homepages on the platform — not through a feed algorithm, but through serendipity or explicit browsing.

**Need:**

As Priya, I want to see a list of recently updated homepages or browse a directory of users, so that I can discover new people and pages without an algorithm deciding what I see.

**Acceptance:**
- A 'Discover' or 'Browse' page shows recently active users with a timestamp ('updated 3 days ago')
- List is sortable by join date or last-updated date
- Each entry shows username and (optionally) a short bio or first line of their page
- Clicking a name takes you to their public homepage
- Pages are discoverable by default; users can't hide themselves (for MVP)

**Tier:** core

**Confusion-flags:**
- Privacy: the directive says pages are public by default, but does that mean *listed* in the directory by default, or just accessible if someone has the URL? The difference is real. Priya wants discovery; a user who wrote a private journal might be horrified to be listed.
- Spam and abuse: with no moderation, who prevents a user from using their homepage to post harassment? The directive doesn't mention a code of conduct or reporting mechanism. For an MVP, do we assume good faith, or do we need guardrails now?
