## Story 005: Visit a specific person's page by URL

**Persona:** Casey, 22, a student. A friend texted them a link: 'check out my new site: [platform]/~friendname'. Casey clicks it.

**Situation:**

Casey has a direct link from a friend and just wants to see what they made. This is the happy path for page sharing.

**Need:**

As Casey, I want to visit someone's page by typing or clicking their URL, see their content, and understand who they are and what they do, so that I can appreciate what my friend made.

**Acceptance:**
- The URL /~friendname loads their page in under 1 second
- The page displays clearly: their content, any styling they added, is readable
- If the page is empty or doesn't exist, I see a clear message (not a 500 error)
- I can see who made this (their username is visible)

**Tier:** core

**Confusion-flags:**
- Is the page always public, or can someone hide/private their page and then only share the URL with specific people? The directive says 'public by default' — I assume that means public, period, for MVP.
- Do we show anything else on the page besides the user's content? Like 'created [date]' or a follow button? Probably not for MVP, but it affects the feel.
