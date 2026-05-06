## Contract Note 002: Account recovery and unlock authorization

**State:** awaiting-backend-response
**Contract Version:** (draft)

**Current Shape:**

On account lockout (423 status), /login returns error. No recovery path exists. Lockout expires after 30 minutes (TTL per Queen ruling 006). No second-factor unlock mechanism.

**Proposed Change:**

Add an unlock authorization primitive that validates account ownership *independent* of password (email token, SMS OTP, security question, etc). This unblocks: (1) locked-out users regaining access before 30-min TTL, (2) the attack surface being resilient to stolen passwords, (3) the Queen's ruling on 'unlock must not be possible for attackers with breached password.'

**Source:** Cheshire Cat ADR 'Decouple unlock authorization from initial authentication'; Queen ruling 'Unlock must not be possible for attackers with breached password'; Rabbit tickets for unlock UX (slug=implement-account-unlock-workflow-for-rate-limited-users-email-link-or-sms, slug=add-unlock-account-cta-to-login-page-for-locked-out-users-who-know-their-credentials)

**Frontend Impact (Tweedledee):**

**If email-token recovery (most likely given infrastructure):**
- Locked-out user sees: "Account locked. Unlock via email recovery link."
- User enters email address or uses account email on file
- I send POST /account/request-unlock-email with {account_id OR email}
- Backend sends email with time-limited token (TTL TBD, per Tweedledum)
- User receives email, clicks token link → navigates to /unlock?token=XXXX
- I validate token on client (optional UX) OR POST to /account/unlock?token=XXXX → backend validates + clears lockout
- Response: 200 OK + session token (user logged in) OR 401/410 (token expired)
- User-facing SLA: email delivery (5-30min) + user clicking link (variable) = Alice's 5-min story may be at-risk for email recovery

**If SMS OTP recovery:**
- Locked-out user sees: "Account locked. Enter OTP sent to your phone."
- I POST /account/request-unlock-sms with {account_id OR phone}
- Backend sends SMS with 6-digit OTP (TTL ~5min)
- User enters OTP in UI
- I POST /account/unlock-sms with {otp} → backend validates + clears lockout
- Response: 200 OK + session token OR 401 (invalid/expired OTP)
- User-facing SLA: SMS delivery (~30s-2min) + user entry = Alice's 5-min story is achievable

**If security question recovery:**
- Locked-out user sees: "Account locked. Answer security question."
- I display pre-configured security questions from account profile
- User enters answer
- I POST /account/unlock-question with {question_id, answer} → backend validates + clears lockout
- Response: 200 OK + session token OR 401 (wrong answer)
- User-facing SLA: immediate (no network delay beyond request/response)

**My preference: email-token + SMS-OTP hybrid**
- Email is low-friction (user already knows their email)
- SMS is fast (meets 5-min SLA)
- Hybrid = email primary, SMS as backup if email missing or user prefers SMS
- But this requires both services to exist; if only one exists, I'll wire whichever is available

**Contract questions for Tweedledum:**
1. **Which recovery primitive do you want to implement for v1?** Email token, SMS OTP, security question, or hybrid? This determines the contract shape.
2. **If email token:** What's the token TTL? What HTTP endpoint do I call to request the email? Does the backend send email sync (return immediately) or async (I poll for status)?
3. **If SMS OTP:** What's the OTP format (6 digits, alphanumeric, etc.)? What's the TTL? SMS provider (Twilio, etc.) — does it have quota/rate-limit implications during a burst of unlock requests?
4. **If security question:** Are the questions pre-configured in user profiles, or do I fetch them dynamically? How many attempts before lockout of the unlock path itself?
5. **General:** Does successful unlock clear the 423 account_locked state immediately, or does it clear the account's failed-attempt counter and rely on the 30-min TTL to expire naturally? (Affects whether user can immediately retry /login after unlock.)

**Backend Impact (Tweedledum):**

[awaiting your response]

**Estimated contract finalization:** Once you fill in backend impact and pick the recovery primitive, I can finalize the contract version (v1.0) and ship the unlock UX.

**Risk:** If email-token recovery is the choice, Alice's 5-min SLA story may need to shift to "within 30 min with most unlocks arriving within 5 min" depending on email delivery times. If SMS OTP, we're good. This shapes Alice's story acceptance criteria.

**Dissent records:** none yet — waiting for your clarity on which path
