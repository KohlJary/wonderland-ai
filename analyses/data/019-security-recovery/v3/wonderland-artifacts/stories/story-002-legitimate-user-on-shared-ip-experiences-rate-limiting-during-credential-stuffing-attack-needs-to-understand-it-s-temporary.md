## Story 002: Legitimate user on shared IP experiences rate-limiting during credential-stuffing attack, needs to understand it's temporary

**Persona:** Alex, 35, works in a corporate office with 200+ employees sharing a single outbound IP. During the credential-stuffing attack window, someone in another department also tried to log in repeatedly (unrelated incident). Now Alex gets rate-limited when they try to log in.

**Situation:**

Alex's company's shared IP address triggered the rate-limit because of concurrent failed login attempts from other people in the building. Alex is not under attack; they just share infrastructure with someone who is. They need to log in to retrieve a document before a deadline.

**Need:**

As Alex, I want to know why I'm being rate-limited and have a way to log in that doesn't require waiting or leaving the office, so that my security is protected without blocking my legitimate work.

**Acceptance:**
- The rate-limit error message distinguishes between 'too many failed attempts on your email' (account lockout) vs 'too many login attempts from your IP address' (IP rate-limit) and explains both.
- Alex can verify their identity via email-based challenge (a one-time code sent to their email) to bypass the IP rate-limit and log in immediately.
- The email-based bypass works even while the IP rate-limit is active, and doesn't interfere with the security of the rate-limit itself.

**Tier:** core

**Confusion-flags:**
- IP-based rate-limiting can't distinguish between an attacker and a legitimate user sharing the same IP. Email-based challenge is a workaround, but I'm not certain it's the *right* pattern — it adds friction and complexity. The Queen's ruling should clarify whether IP-level rate-limiting is the intended approach, or whether we should use something finer-grained.
- I'm also uncertain about the user experience during the challenge flow. Is it enough to send a code? Should we also ask security questions, or require re-verification of payment method? This feels like it needs careful thought about friction vs. false-positives.
