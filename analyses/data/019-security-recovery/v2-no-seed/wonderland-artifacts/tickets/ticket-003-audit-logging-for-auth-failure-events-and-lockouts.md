## Ticket 003: Audit logging for auth failure events and lockouts

**Sources:** dormouse-observation-credential-stuffing
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 0.5–1 hour, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: rate-limit-middleware, lockout-ux-update

**Description:**

Log each failed auth attempt and each lockout event with: timestamp, IP, username, source User-Agent, response code. Logs should be queryable for incident review (grep/awk is acceptable; structured logging is better if available). No encryption required for this immediate version; the Queen may rule stricter retention later.

**Acceptance:**
- Each failed auth is logged with IP, username, User-Agent
- Each lockout event is logged with user ID, trigger time, unlock time (if auto-unlock is implemented)
- Logs are queryable for incident review
- Logs do NOT include plaintext passwords

**Risk:**

If log volume becomes a concern post-incident, we may need rotation/compression. Acceptable in v1. Add to post-launch.
