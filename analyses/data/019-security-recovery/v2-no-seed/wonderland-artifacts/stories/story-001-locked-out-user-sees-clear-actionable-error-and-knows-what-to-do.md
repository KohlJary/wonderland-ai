## Story 001: Locked-out user sees clear, actionable error and knows what to do

**Persona:** Marcus, 28, a moderator managing a book club Discord — he's in the middle of a live discussion and got bounced mid-session.

**Situation:**

Marcus tried to log back in after a Discord sync glitch knocked him out. He's staring at a login failure. 47 other people are locked out with him. He doesn't know if it's his password, the system, or an attack. His book club discussion is happening *now* and he's missing it.

**Need:**

As Marcus, I want a clear error message that tells me *why* I'm locked out (too many failed attempts) and *what I can do about it* (contact support, wait X minutes, reset password), so that I'm not panicked and I know whether to try again or reach out.

**Acceptance:**
- Error message explicitly states 'account temporarily locked due to multiple failed login attempts'
- Message includes estimated unlock time or reset-password link (whichever applies)
- Message includes support contact info (email, phone, or help link)
- User can read and understand the message on mobile in under 10 seconds

**Tier:** core

**Confusion-flags:**
- I don't know if these 47 are victims or if their credentials actually succeeded — the Dormouse said 0.2% success rate, which might mean some succeeded. If they did, do they know? Are they still in? That changes the urgency and the message.
- I don't know if we're sending email to locked-out users automatically or if they have to discover the lockout by trying to log in. If they don't know they're locked, they'll just keep trying and get more frustrated.
- If the attack is ongoing and we're rate-limiting, will legitimate users get rate-limited too? Marcus might see 'too many attempts from your IP' even though *he* only tried once. That's a different error and a different story.
