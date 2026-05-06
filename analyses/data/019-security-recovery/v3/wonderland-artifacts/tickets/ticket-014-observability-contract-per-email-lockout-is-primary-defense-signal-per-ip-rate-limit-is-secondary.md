## Ticket 014: Observability contract: per-email lockout is primary defense signal; per-IP rate-limit is secondary

**Sources:** ADR: Auth defense-in-depth; scenario 4 (distributed IP); Queen's ruling #3 (observability required)
**Owner:** Dormouse
**Tier:** v1
**Estimate:** 0.5–1 day, 85% confident
**Status:** open

**Dependencies:**
- Blocks: ticket #8 (Tweedles: implement rate-limiting and lockout observability)
- Blocked by: —
- Soft: ticket #11 (Tweedles: confirm /password-reset scope) — reset-flow observability should be specified in the same contract

**Description:**

The Cat's ADR clarifies that per-email account lockout is the catch-all defense against distributed credential-stuffing attacks, while per-IP rate limiting is a secondary friction layer that reduces enumeration efficiency from a single source. The Queen's observability ruling requires that breach-notification work can determine which accounts were compromised during the attack window. The observability contract must make explicit which signals are primary (per-email lockout events trigger user notification and breach-notification investigation) and which are secondary (per-IP rate-limit events are diagnostic, not primary). Output: contract note specifying metrics/events with dimension priorities and alarming thresholds.

**Acceptance:**
- Contract specifies which events are observable: per-email lockout triggers, per-IP rate-limit triggers, unlock/reset methods
- Contract names primary signals (per-email lockout events) vs. secondary diagnostic signals (per-IP rate-limit events)
- Contract specifies alarming thresholds and dashboards for each signal class
- Contract clarifies that FailedAttempt audit table is the source of truth for breach-notification work; in-memory cache state is not relied upon for compliance

**Risk:**

If observability contract does not clarify signal priority, operators may over-weight per-IP rate-limit events in their incident response, missing the fact that per-email lockout is the actual defense.
