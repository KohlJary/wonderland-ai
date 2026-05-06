## Story 004: Join a chat as a second user (fast-follow)

**Persona:** Jordan, 30, wants to test the MVP with a friend who speaks German, needs a way to get into the chat without going through a login page.

**Situation:**

Jordan and their German-speaking friend want to try the MVP. There's no database of users yet, no account creation. They need a simple way to get two people into a chat together.

**Need:**

As Jordan, I want to join a chat with a link or code so that I can test the MVP without friction.

**Acceptance:**
- I receive a link or code.
- I click it or paste it.
- I'm in the chat and can send/receive messages.

**Tier:** fast-follow

**Confusion-flags:**
- This feels like it depends on the auth story. Is it a token in the URL? A session cookie? The directive says 'basic auth' but fast-follow messaging doesn't feel like it needs HTTP basic auth. I'm unclear on what the auth *is*.
