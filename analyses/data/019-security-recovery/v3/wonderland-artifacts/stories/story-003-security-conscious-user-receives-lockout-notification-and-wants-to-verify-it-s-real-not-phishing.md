## Story 003: Security-conscious user receives lockout notification and wants to verify it's real (not phishing)

**Persona:** Sam, 42, security professional, has been phished before. Receives a lockout notification email after the credential-stuffing attack. Wants to confirm it's a legitimate service notification, not a phishing attempt copying the service's email templates.

**Situation:**

Sam is skeptical by nature. They receive an email from the service explaining that their account is locked due to repeated failed login attempts. The email contains a link to unlock their account via email verification. Sam is not certain the email is legitimate and is considering ignoring it or calling customer support.

**Need:**

As Sam, I want to verify that the lockout notification is from the legitimate service and not a phishing attack, so that I can unlock my account without exposing myself to social engineering.

**Acceptance:**
- The lockout notification email contains verifiable indicators of authenticity (e.g., DKIM/SPF/DMARC headers, service-specific metadata that a phisher wouldn't include).
- The email provides a way to verify legitimacy without clicking a link (e.g., 'log in directly to the service to check your account status, rather than clicking this link').
- The service provides a support channel (email, phone, live chat) that Sam can use to verify the notification if they're uncertain.

**Tier:** enrichment

**Confusion-flags:**
- This story might be overspecifying technical details (DKIM/SPF) that are not user-facing. But the *intent* is real: security-conscious users need to be able to distinguish legitimate notifications from phishing. I want the team to keep this intent in mind even if the mechanism shifts.
- I'm also uncertain whether this tier is right. It could be core — Sam is a real user — but it's also possible that the team will decide phishing-resistance is a follow-up. Marking as enrichment to leave room for that decision, but I think it should be revisited.
