## Story 004: New user understands how to authenticate without friction

**Persona:** Sofia, 52, not tech-savvy, uses email and WhatsApp daily, has never created an account on a new service in years. She's joining the book club at Sarah's invitation.

**Situation:**

Sofia gets the link, visits the app, and sees a login screen. She's not a member yet. She doesn't know if she needs a code or if she can just make a password, whether she'll get an email, or how long it takes. She's on a slow connection and slightly paranoid about data security (she's EU-based and knows GDPR is a thing, even if she doesn't know what it means).

**Need:**

As Sofia, I want signup to be four taps and one email check, so that I can join the book club in the time it takes to make tea, not in the time it takes to debug a password reset.

**Acceptance:**
- Sofia can sign up with just email and password (no phone verification, no external OAuth required at v1)
- She receives a confirmation email, clicks a link, and is immediately in the app — no waiting for admin approval
- The app tells her up front: 'We use encryption for messages, we don't sell your data, GDPR applies to your account' in clear language, not legal boilerplate

**Tier:** core

**Confusion-flags:**
- I wrote 'encryption for messages' but I don't know if v1 has end-to-end encryption or just TLS in transit. This might be a Queen-of-Hearts ruling (security mandates encryption; we confirm what level at v1) or a Caterpillar call (what's technically feasible). I'm flagging the gap.
- I said 'GDPR applies' — that's not a user story, that's a compliance fact. But Sofia is EU-based and probably expects some privacy signal. How that signal appears is the team's call, not mine. The confusion-flag is whether this story is conflating user need (privacy assurance) with compliance fact (GDPR applies).
