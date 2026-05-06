## Story 002: Affected user can regain access without waiting forever or jumping through chaos

**Persona:** Yuki, 45, a polyglot moderator running cross-language community threads — she's not locked out yet, but her password might have been in the leaked-credentials list.

**Situation:**

Yuki hears through the grapevine that there's an attack and some users are locked out. She doesn't know if she's vulnerable. She logs in successfully, but the back of her mind is asking: if my credentials are in that stolen list, what do I do? How do I know if I should change my password? How do I know if my account was accessed?

**Need:**

As Yuki, I want to know whether my account was targeted or accessed during this attack, and if it was, I want a clear path to secure it (force password reset, verify recent logins, re-secure linked accounts), so that I can trust my account is mine again.

**Acceptance:**
- User can see a simple 'Account Security' status after logging in (green = no suspicious activity, yellow = check recent logins, red = password reset required)
- If activity is suspicious, there's a link to 'Recent login activity' showing IP, device, timestamp for the last 5 logins
- There's a 'Force password reset on next login' button if the user wants to be proactive
- A help article or link explains what an attack looks like and what to do if your password was compromised

**Tier:** core

**Confusion-flags:**
- I don't know if we actually know which credentials succeeded — the Dormouse said 0.2% success rate, but I don't know if that means 8 accounts were actually compromised or 0. If we don't know, do we tell users to change their password 'just in case' or wait for evidence? That's a Queen call, but it shapes the message.
- I don't know if we have 'recent login activity' instrumentation already. If we don't, showing it is a build, not a UX tweak.
- I don't know what 'linked accounts' means for us — OAuth providers, email recovery, payment methods? That's architecture-dependent.
