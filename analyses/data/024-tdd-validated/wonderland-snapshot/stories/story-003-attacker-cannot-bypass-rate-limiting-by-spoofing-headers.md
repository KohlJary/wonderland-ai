## Story 003: Attacker cannot bypass rate limiting by spoofing headers

**Persona:** Security-conscious deployment team reviewing the implementation

**Situation:**

The rate limiter uses X-Forwarded-For when present. The team is asking: if an attacker can control that header, does the rate limit become useless?

**Need:**

As a deployment team, I want the rate limiter to be safe against header spoofing by default, so that the limit actually protects the service.

**Acceptance:**
- Documentation clearly states whether X-Forwarded-For is trusted or validated
- If X-Forwarded-For can be spoofed, there is a configuration option to ignore it and use remote address only
- The implementation does not silently fall back to an empty client ID if both headers are missing

**Tier:** core

**Confusion-flags:**
- This might be the Queen's concern more than mine — security implications often touch architecture. I'm flagging it because the limiter's effectiveness depends on correctly identifying clients, and I'm not sure the team has thought through the spoofing scenario yet.
