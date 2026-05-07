## Story 001: User discovers rate limit when sending rapid messages

**Persona:** Jordan, 28, a bot framework developer integrating this API for their first time, testing locally with a rapid-fire script

**Situation:**

Jordan is writing integration tests for their bot. They send 15 requests in quick succession to understand the API's behavior, expecting either success or clear failure. Instead they get a cryptic HTTP error and no clear path forward.

**Need:**

As Jordan, I want to know immediately and clearly when I've hit a rate limit and when I can try again, so that I can adjust my client code instead of assuming the API is broken.

**Acceptance:**
- When requests exceed 10/minute, the response includes HTTP 429 with a human-readable message explaining the rate limit
- The Retry-After header is present and contains the number of seconds until the next request will succeed
- The error response is consistent and predictable (same format every time) so I can parse it reliably in my client
- When I wait for the Retry-After duration and retry, the request succeeds without further delay

**Tier:** core

**Confusion-flags:**
- I don't know if 10 requests/minute is the right limit for actual users — is this tuned to real usage patterns, or a guess? If users are legitimately doing burst sends, this might feel punitive rather than protective.
- The X-Forwarded-For vs remote address fallback: I assume this is for load-balanced deployments, but I'm not certain how users behind corporate proxies (same X-Forwarded-For, different actual clients) should experience this. Does the limit feel fair to them?
