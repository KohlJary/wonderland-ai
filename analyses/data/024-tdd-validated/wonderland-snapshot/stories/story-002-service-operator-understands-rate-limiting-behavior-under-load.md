## Story 002: Service operator understands rate limiting behavior under load

**Persona:** Casey, 35, an SRE responsible for the message API in production, on-call during incidents

**Situation:**

The service is under unexpected load. Casey wants to understand: is the rate limiter working as a shield, or is it creating a bottleneck that makes things worse? When they look at logs and metrics tomorrow, will they understand what happened?

**Need:**

As Casey, I want rate limiting to be observable and tunable in production, so that I can verify it's protecting the service rather than just rejecting legitimate traffic.

**Acceptance:**
- Metrics are emitted for each rate-limit rejection (timestamp, client IP, request count at time of rejection)
- The rate limit threshold (10/minute) is tunable at runtime without redeploy
- When I read production logs, I can distinguish between 'client hit their quota' and 'something else failed'
- The rate limiter's state (current request count per IP) is inspectable or can be dumped for debugging

**Tier:** enrichment

**Confusion-flags:**
- I don't know if 10/minute is the right threshold for normal usage — if this limit is too strict, operators will just disable it. The team should validate this against real usage data before shipping.
- The X-Forwarded-For logic: in a broken proxy scenario, an attacker could spoof headers and bypass the limit. Is this an acceptable risk, or should there be validation?
