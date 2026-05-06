## Story 011: Locked-out user unlocks their account and regains access within their 5-minute SLA

**Persona:** James, 28, book club member from a shared corporate network. He's not involved in the credential-stuffing attack — he was just collateral on the same IP pool. He has a weekly book discussion starting in 4 minutes.

**Situation:**

James got rate-limited because his office IP (203.0.113.42) is the attack source. He sees the error message telling him to unlock via email. He clicks the link. Now what? His discussion is in 4 minutes. The unlock flow needs to work in < 5 minutes total, or he misses his slot.

**Need:**

As James, I need to unlock my account and log back in in under 5 minutes total, so that I can make my book discussion on time and trust that the system won't strand me during future incidents.

**Acceptance:**
- James clicks 'Unlock via email' and receives an unlock email within 30 seconds
- The unlock email contains a clickable link that unlocks the account when clicked
- After clicking the link, James is logged back in (or redirected to a 1-click login) within 10 seconds
- The entire flow (error message → email arrival → click link → back in) is under 5 minutes 95% of the time
- If email delivery is delayed, James receives a fallback unlock option (security question, SMS, or immediate escalation to support) within 2 minutes of requesting unlock
- After successful unlock, James's original session is restored or replaced such that he can immediately return to the book discussion he was in before the lockout

**Tier:** core

**Confusion-flags:**
- Session restoration is the hard part here. Does James's original browser session (pre-lockout) need to be refreshed, or do we issue a new session? If new, we need transparent re-auth, which adds steps.
- Email delivery is outside our control — Sendgrid/Mailgun can have delays. The 5-minute SLA includes their delivery time, which is risky. Do we need SMS as the primary unlock path, or email as primary + SMS as fallback?
- If James's unlock link lands in his spam folder, he won't see it. Is there a resend-link mechanism, and does it eat into the 5-minute window?
