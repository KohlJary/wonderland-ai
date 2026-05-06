## Story 010: Locked-out user sees clear, actionable error and knows exactly what to do next

**Persona:** Maya, 31, polyglot moderator. She was moderating a cross-language thread when she got rate-limited. She has no idea why her login failed, and she has 200 people waiting for moderation decisions.

**Situation:**

Maya attempts to log in during the credential-stuffing attack. The rate-limit fires. Her browser returns an error. She has 90 seconds before the thread community escalates to management asking where she went.

**Need:**

As Maya, I need to see an error message that tells me (1) my account is temporarily locked due to suspicious activity, (2) this is not my fault, (3) exactly how to regain access, so that I can take the right action and get back to work without panic or escalation.

**Acceptance:**
- The error message appears within 1 second of failed login attempt
- The message names the reason: 'Too many failed login attempts from this location'
- The message provides the next action: 'Click here to unlock your account via email' or equivalent
- The message includes a human-readable timeline: 'You'll regain access within 5 minutes'
- If Maya's account is already unlocked (the lockout window expired), the message says so and invites immediate retry
- The message is available in at least 3 languages (English, Spanish, Mandarin) — Maya's communities use all three

**Tier:** core

**Confusion-flags:**
- The error message lives at the intersection of security (don't reveal too much about the attack) and UX clarity (tell the user what happened). I'm uncertain how much detail is safe to ship.
- Different browsers render error pages differently. Is this a custom in-app modal, an HTTP error page, or both? The shipping surface matters.
- Localization at runtime for error messages is tricky if we're rate-limiting at the middleware layer. Need to confirm the implementation surface.
