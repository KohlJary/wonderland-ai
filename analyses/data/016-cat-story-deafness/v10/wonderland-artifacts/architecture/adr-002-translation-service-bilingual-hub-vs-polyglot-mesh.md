# ADR-002: Translation service: bilingual hub vs. polyglot mesh

## Context

Four user stories describe a polyglot book club: Sarah (monolingual English) needs real-time German translation; Marcus (trilingual moderator) needs to see which messages are translated to spot where translation is failing; Yuki (German speaker, no English) wants to join but there's no German ↔ Japanese path; Sofia (new non-technical user) needs transparent privacy/security signals at signup. Stories 001 and 002 imply a real-time translation service with visible translation status. Stories 003 forces a structural decision: can Yuki talk to German and Japanese speakers in her first language, or does the architecture implicitly route her through English?

## Decision

Defer the choice, but surface it explicitly. The team must decide before implementation: Is the translation service a **bilingual hub** (English is the mandatory pivot; all other pairs route through English) or a **polyglot mesh** (any language pair can be added independently, with no hidden routing)? This choice changes the data model (how messages are tagged with original/translated language), the translation service contract, and the signup UI's language-pair visibility. Record this decision as an ADR with clear tradeoffs so the implementation can proceed with architectural coherence.

## Tradeoffs

- Hub model: Simple translation service (one direction: any language → English, English → any language), faster latency for English speakers, but Yuki's complaint (German ↔ Japanese routing) either silently happens through English or becomes a post-v1 feature. This feels deceptive in the signup flow (story 003 explicitly rejects silent routing).
- Hub model: Scales easily for new languages (add a model for X → English, English → X) but the message routing layer has to carry the coupling to English as a structural fact. If the team later wants to remove English as mandatory pivot, the data model has to change.
- Mesh model: Any language can talk to any language directly; no hidden routing surprises; Yuki's story is unblocked at v1. But the translation service contract gets more complex (N² language pairs, not 2N). Scaling to new languages is more expensive (each new language needs M models, one for each existing language).
- Mesh model: Latency may increase for non-English pairs if the translation service doesn't have a direct path (e.g., German → Japanese might be slower than German → English → Japanese if the service is optimized for English as hub). The architecture must be honest about this.
- Either model: The message data structure must track original language + translated language(s) visible in Marcus's story. If hub, this is simpler (original + one translation into English). If mesh, this is more complex (original language + potentially multiple translations, or visibility of which translation the user is reading).
- Either model: Sofia's story (story 004) implies the signup flow must show users which language pairs they can use. Hub model makes this simpler (everyone can talk to English speakers; new language pairs are post-v1). Mesh model requires the signup flow to show the full pair matrix, which is clearer but more complex.

## Status

Proposed
