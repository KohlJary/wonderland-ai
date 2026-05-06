# ADR-001: Third-Party Translation Service with Synchronous On-Read Model

## Context

Three-week MVP for real-time chat with message translation. Two language pairs at launch. GDPR scope requires explicit data-flow boundaries and processor agreements. Real-time user experience requires low latency and visible status signals. Persistence strategy determines both compliance surface and implementation complexity.

## Decision

Integrate third-party translation service (vendor TBD, pending Queen's processor-agreement review). Persist original messages only; translate on read, not on write. Deliver via WebSocket with visible translation-status signals. Timeout and graceful degradation to original message if translation exceeds SLA (propose: 2 seconds).

## Tradeoffs

- Closes: custom model tuning, in-house training, offline-first translation scenarios, truly stateless HTTP backend, post-send message edits with re-translation.
- Opens: predictable translation cost, third-party SLA liability, simpler GDPR deletion obligations (single data copy), lower operational complexity for v1.
- Requires decision: which third-party translator (Google, AWS, DeepL, etc.) — Queen must review processor agreement before final choice.
- Requires decision: WebSocket state management strategy (sticky sessions vs. shared cache) — Tweedles to propose after this ADR.
- Uncertain: whether 2-second translation timeout is acceptable to users — Alice's story and Hatter's test scenarios will constrain this.

## Status

Proposed
