# ADR-003: Translation service architecture: commit to polyglot mesh model

## Context

ADR-002 deferred the hub vs. mesh choice pending team decision. Tweedledum's concern surfaces that the deferral is blocking implementation: the message schema, routing logic, and service contract differ fundamentally between models. Story-003 (Yuki's story) provides the deciding constraint: it explicitly requires honesty about which language pairs work and rejects silent routing. The hub model can only satisfy story-003 by either building mesh anyway or marking German↔Japanese as v2. Mesh satisfies story-003 directly at v1.

## Decision

The translation service architecture is a polyglot mesh: any language pair can be added independently with no mandatory pivot language. English is not special in the architecture—it's one language among many. The message data structure tracks original_lang + translations (implementation detail of the map/array shape to be negotiated in contract-002). The routing and translation service contract must handle the full N-language surface without special-casing English.

## Tradeoffs

- Latency: German↔Japanese may be slower than German→English→Japanese if the translation service is optimized for English as a hub. This is a service-level choice, not an architecture problem. The architecture must not hide this latency by routing through English and pretending it's direct.
- Translation service scaling: Adding a new language requires at minimum one new model (to/from the new language to each existing language), not just two (English pivot). This is more expensive than hub model scaling, but there's no hidden cost in the architecture itself—the service tier scales with the actual problem, not with a fiction.
- Signup UI complexity: The language-pair matrix for Yuki is honest (German speaker sees she can talk to English and German speakers, but not Japanese speakers at v1). This is more complex than hub model UI (everyone can talk to English speakers), but it delivers story-003's core need: transparency.
- Implementation debt: If the translation service itself is hub-oriented (all models are X↔English), Tweedledee and Tweedledum will need to handle German↔Japanese routing client-side or push back on the service contract. That's a service negotiation, not an architecture problem.
- No hidden English-as-pivot: The architecture cannot route German→English→Japanese and call it 'German→Japanese.' This closes the door on a false simplification, which is correct—the cost is upfront honesty, not hidden complexity later.

## Status

Proposed
