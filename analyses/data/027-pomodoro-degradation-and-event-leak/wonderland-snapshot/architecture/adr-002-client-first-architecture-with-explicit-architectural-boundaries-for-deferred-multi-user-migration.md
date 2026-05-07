# ADR-002: Client-first architecture with explicit architectural boundaries for deferred multi-user migration

## Context

Five user stories have accumulated describing the pomodoro tracker's surfaces: session lifecycle (start/complete), break flow, session review (today and historical), and settings. Each story implies persistent state. The directive specified 'single-user local app' with 'design with a real database so multi-user can be added later' — a constraint that resolves into an architectural choice.

The tension: single-user local apps and multi-user distributed systems have different load-bearing surfaces. Single-user means client-side persistence (IndexedDB, SQLite WASM) and no authentication. Multi-user means server persistence, identity verification, and synchronization. These cannot coexist in the same code without abstraction. Further, if the abstraction permits multi-user silently (by refactoring existing code), we defer the decision but embed the choice, creating technical debt that becomes compliance debt later.

The user stories show what surfaces the app needs: durable session history, temporal queries (today vs. all-time), user settings, and notifications. The question is whether these surfaces are served by a client-side store with a clear migration path to server-side (requiring new code, not refactoring), or whether we build the server abstraction now and run it against a local database initially.

## Decision

Build the persistence layer as a server-shaped interface (API contract) abstracted from transport. Implement transport initially as a local in-process service (IndexedDB or SQLite WASM as the backing store). This gives the team:

1. A single persistence interface that both frontend and eventual backend can speak to, eliminating the need to refactor the application layer when multi-user is added.
2. Clear separation between session/history logic (shared between single-user and multi-user) and identity/sync logic (added later).
3. A concrete contract for the Tweedles to negotiate now, rather than guessing the shape later.
4. Architectural enforcement of the M1 client-only constraint: no server-side persistence code, no auth layer, no multi-user data-migration logic exists in M1. Porting to server-side persistence in M2 requires new code at the service boundary, not refactoring of existing application code.

The interface itself stays client-side until multi-user is needed; the abstraction is the load-bearing part, not the server.

Notification delivery: for single-user, use browser/OS notification APIs (no server needed). When multi-user arrives, the notification surface becomes part of the server contract; the abstraction point is the same either way.

## Tradeoffs

- Adds a small indirection layer now (an API abstraction) that single-user operation does not strictly need. The cost is minimal — a few function signatures and a fetch mock — but it is real.
- Closes the door on 'just run SQLite on the client and add a server later by moving the file.' That path would be cheaper upfront but more expensive overall (refactoring the entire app layer to speak to a server). We're choosing the path that costs more to describe but less to execute.
- Opens the door to running the same application logic against a local service, then a remote service, without the application layer knowing the difference. This is the path to multi-user without a major rewrite.
- DEFERRED ARCHITECTURAL BOUNDARIES — named explicitly; M1 implementation must enforce these at the code/architecture level, not operationally:
  • Persistence location: Which side of the service boundary owns the data store (client-side device, or server)? M1 assumes client-only; server-side migration in M2 requires new persistence service code.
  • Authentication assumption: Does the architecture assume authentication will exist, or does it assume single-user implicit identity (device-owner)? M1 assumes no auth layer; multi-user in M2 requires new identity service code.
  • Data migration on multi-user transition: When migration happens, will users' historical data transfer with them, be deleted, or be re-aggregated? M1 assumes no migration logic; data-governance rules in M2 require new migration service code.
  The constraint: if M1 code could silently become multi-user in M2 without crossing the service boundary (without new code), then the decision is embedded, not deferred. The service boundary must be real enough that answering these questions requires new service code, not refactoring of existing code.

## Status

Proposed
