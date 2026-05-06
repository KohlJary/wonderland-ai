## Ticket 001: Implement rate-limiting on /login endpoint per Queen ruling

**Sources:** dormouse-observation-credential-stuffing
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 0.5–1 hour, 85% confident
**Status:** open

**Dependencies:**
- Blocks: lockout-ux-update
- Blocked by: —
- Soft: —

**Description:**

Ship rate-limit middleware on /login endpoint. Exact rate shape (requests per IP, requests per username, window duration, response behavior) TBD by Queen ruling. Implementation should be straightforward middleware insertion; the tuning is the Queen's call. Get the Queen's specific values, ship the code, do not wait for perfect architecture.

**Acceptance:**
- Rate-limit middleware is inserted into the /login request pipeline
- Exceeding the limit returns HTTP 429 (or Queen-specified status)
- Rate-limit state is tracked (in-process cache is acceptable for now)
- Logs include rate-limit trigger events with IP, username, timestamp

**Risk:**

If the Queen's ruling requires state that outlives process restart (e.g., Redis), expand to 1.5–2 hours for integration. Assume in-process for now; pivot on her ruling.
