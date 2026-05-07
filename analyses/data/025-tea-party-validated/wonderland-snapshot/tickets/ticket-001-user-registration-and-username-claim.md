## Ticket 001: User registration and username claim

**Sources:** sign-up-and-claim-a-username
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1.5-2.5 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: visit-a-specific-person-s-page-by-url, edit-my-homepage-in-markdown, discover-other-people-s-pages
- Blocked by: —
- Soft: —

**Description:**

Implement user registration flow with email verification and username availability check. User submits email + desired username, receives verification link, completes signup. Store user record with username claim. Handle username collision (suggest alternatives or reject). No password complexity rules yet — hash whatever they submit.

**Acceptance:**
- User can submit registration form with email and desired username
- System validates email format and checks username uniqueness
- Verification email is sent and contains working verification link
- User completes verification, account is created and username is claimed
- Duplicate username attempts show availability status and suggest alternatives
- User can log in after successful registration

**Risk:**

Email delivery reliability and verification token expiration logic may need iteration if mail service is flaky.
