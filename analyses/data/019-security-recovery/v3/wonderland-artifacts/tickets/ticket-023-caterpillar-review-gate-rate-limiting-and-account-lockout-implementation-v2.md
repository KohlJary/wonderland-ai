## Ticket 023: Caterpillar review gate: rate-limiting and account-lockout implementation v2

**Sources:** —
**Owner:** Caterpillar
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: implementation-merge-gate
- Blocked by: implement-observability-hooks-for-rate-limit-and-lockout-events-blocking-for-queen-ruling-3, add-email-based-rate-limiting-as-primary-defense-per-queen-ruling-1, define-and-document-password-reset-rate-limit-isolation-contract-per-queen-ruling-2
- Soft: —

**Description:**

The Tweedles' first implementation shipped the core mechanics but is missing three Queen-ruled requirements: observability instrumentation, email-based rate-limiting, and /password-reset isolation contract. The three tickets above (observability, email-based limiting, isolation contract) must be completed before this review. Once they are, the Caterpillar reviews the updated implementation against: (1) the Queen's three rulings (distributed-IP defense, password-reset isolation, production telemetry), (2) the Hatter's six test scenarios (all must pass), (3) the Dormouse's observability contract (all instrumentation hooks must match the contract), and (4) code quality (performance, logging, test coverage). Change-required verdict until all three are done. Approve only when the implementation fully satisfies the ruling set and scenario set.

**Acceptance:**
- Observability hooks are present and match Dormouse's contract
- Email-based rate-limiting is implemented and tested against distributed-IP scenarios
- /password-reset isolation contract is documented and approved
- All six Hatter test scenarios pass
- All four Caterpillar review categories are resolved (code quality, test coverage, HTTP status codes, escape hatches)
- Approval verdict is issued (not change-required)

**Risk:**

If the three blocking tickets are incomplete or misaligned with the ruling set, this review will be delayed. Sequence the three tickets before scheduling the review.
