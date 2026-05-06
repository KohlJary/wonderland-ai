## Story 006: User logs in from a second device

**Persona:** Hassan, 41, runs a small business, switches between phone and laptop during his day. He has ongoing conversations with suppliers in different countries.

**Situation:**

Hassan opens the app on his laptop. He's already logged in on his phone. He wants to see his existing conversations and continue from where he left off.

**Need:**

As Hassan, I want my conversations to sync across my phone and laptop, so that I can pick up a thread on whichever device I'm using without losing context.

**Acceptance:**
- Hassan logs in on laptop with the same credentials as his phone
- His conversation list appears with all prior messages visible
- He can read a conversation thread where the last message he saw on his phone is marked or obvious
- He can reply on laptop and the message appears on his phone's conversation list within seconds

**Tier:** enrichment

**Confusion-flags:**
- This is a real user need but the MVP might ship single-device only. That's okay — it's a fast-follow. But the team should know users expect it and will build it quickly once v1 is stable.
- Conversation sync implies server-side state and probably session management beyond 'basic auth.' That's a Cat/Tweedles conversation about architecture.
