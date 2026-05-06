## Ticket 011: Tweedles: confirm /password-reset endpoint scope and rate-limit interaction before rate-limiting implementation

**Sources:** concern from Rabbit on password-reset flow bypass risk, concern from Dormouse on /password-reset observability gaps
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 0.5-1 hour, 90% confident
**Status:** open

**Dependencies:**
- Blocks: implement-per-ip-rate-limiting-on-login-endpoint-per-queen-s-ruling
- Blocked by: —
- Soft: —

**Description:**

Determine: (a) does /password-reset endpoint already exist in the codebase? (b) if yes, does it currently share rate-limit logic with /login, or is it separate? (c) are reset-flow rate-limit events observable in production telemetry, and are they distinct from login-flow events? If /password-reset shares rate-limit logic with /login, this blocks v1 mitigation—Queen's ruling requires separate policies to avoid locking out legitimate password-recovery flows during attacks. Surface findings as a concern with blocking implications if applicable.

**Acceptance:**
- /password-reset endpoint existence confirmed (yes/no)
- If it exists: current rate-limit policy documented (shared with /login or separate)
- If shared: blocking concern raised to Rabbit and Queen for ruling adjustment
- Observability status for reset-flow events confirmed

**Risk:**

If /password-reset exists and shares rate-limit logic with /login, v1 mitigation cannot ship without architectural change. This is a blocking risk that must be surfaced before implementation.
