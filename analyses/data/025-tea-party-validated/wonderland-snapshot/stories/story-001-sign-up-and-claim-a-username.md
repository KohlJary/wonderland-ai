## Story 001: Sign up and claim a username

**Persona:** Jordan, 26, a musician who wants a simple web presence without learning WordPress. They have a Gmail account and twenty minutes before their next meeting.

**Situation:**

Jordan heard about this platform from a friend and wants to get online quickly. They have never self-hosted anything before.

**Need:**

As Jordan, I want to sign up with just an email and password and get a username instantly, so that I can have a personal URL to share with people who ask for my online presence.

**Acceptance:**
- Email + password signup takes <2 minutes
- Username is claimed and available at /~username immediately
- I receive a confirmation email and can log in right away
- If my chosen username is taken, I get alternatives suggested

**Tier:** core

**Confusion-flags:**
- Do we validate email (confirmation link) before the page is live, or after? If after, a spammer could create dead URLs. If before, new users wait for email.
- Is username immutable or can it be changed? If immutable, people who pick bad usernames early get stuck.
- What's our policy on username squatting or abuse (e.g., claiming /~admin)?
