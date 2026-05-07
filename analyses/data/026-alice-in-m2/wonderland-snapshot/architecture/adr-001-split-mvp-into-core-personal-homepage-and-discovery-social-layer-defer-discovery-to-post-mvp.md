# ADR-001: Split MVP into Core (personal homepage) and Discovery (social layer) — defer Discovery to post-MVP

## Context

Nine stories on the thread surface two separate user flows: (1) personal homepage ownership, editing, deletion (core) and (2) social discovery, activity feeds, webring membership (optional layer). These flows have opposite architectural consequences. Merging them into a single MVP hides GDPR complexity and scope until implementation, when fixes become expensive. The Queen flagged retention and audit obligations; the Rabbit needs to scope two separate work cadences. Alice's stories imply both flows are wanted, but one is load-bearing and one is enhancement.

## Decision

Propose two-layer MVP architecture: Layer 1 (Weeks 1–2) delivers personal homepage as atomic write-delete-purge system with no activity tracking or discovery beyond username search. Layer 2 (Week 3 or post-MVP) adds feed, activity log, webring, with intentional acceptance of GDPR complexity and event-log schema. This split makes the MVP deliverable in three weeks without hiding architectural cost.

## Tradeoffs

- Layer 1 MVP ships with no algorithmic discovery (closed door until Layer 2). Users find pages only by username search or direct sharing. This is acceptable if the MVP's value is 'I own my homepage and can share the URL'; it's not acceptable if the product's differentiation is 'serendipitous discovery.' Alice must confirm.
- Layer 2 discovery architecture (feed, activity log, view counts) will require event schema and retention policy that GDPR constrains. Deferring Layer 2 means the Tweedles can implement Layer 1 without worrying about event-log scaffolding, but it also means the architecture is not specced for the full product until Layer 2 is explicitly proposed.
- Webring membership is optional and opt-in/mutual (prevents backlink cleanup complexity). Users who want webring join it; users who don't want it simply don't claim membership. Simpler than 'everyone is in a graph and we have to maintain it.'
- 'Realness' (story 4) is solved in Layer 1 by 'the URL works and the user's email is verified'; in Layer 2 it could be enhanced by 'the user has been active recently' (requires activity tracking). What constitutes 'real' shapes the discovery algorithm.
- Layer 1 scope is tight enough for three weeks *only if* discovery is deferred. If discovery is in-scope for MVP, the Rabbit is scoping the wrong thing (a two-layer system is not an MVP).

## Status

Proposed
