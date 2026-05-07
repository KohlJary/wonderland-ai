# ADR-001: Session engine, data contract, and notification boundary

## Context

The directive names a pomodoro tracker with seven user surfaces: session execution (start, complete, break), history review (today, weekly, all-time), settings, and data mobility (export, migration). The stories describe the user-facing flows but do not name three architectural decisions that sit underneath them: (1) how notifications are delivered and what guarantees they carry; (2) what shape a session record takes and how it changes if settings change mid-history; (3) whether persistence is purely local (browser storage) or backed by a server that enables sync later.

## Decision

Defer the session engine and data contract decisions to separate ADRs, each grounded in explicit constraints. Surface those constraints now via three focused questions to Alice, the Rabbit, and the Queen: (a) What notification mechanism does the user expect, and what failure mode is acceptable if it doesn't fire? (b) Is the session record immutable once created, or does retroactive settings change affect historical duration?  (c) Does the export story require the data to be sync'd to a server eventually, or is it one-way download only?

## Tradeoffs

- Deferring the ADRs delays the start of implementation decomposition, but surface-level decomposition without these answers produces implicit contracts that will cause rework.
- Answering these questions now makes the Rabbit's decomposition and the Tweedles' contract negotiation much sharper — each story becomes a clear dependency on the architectural answers.
- Not answering them now means the first implementation PR will include the architectural decisions implicitly (buried in code), which is expensive to revisit.
- The alternative — the Cheshire Cat guessing and shipping a prescriptive ADR now — would close design space prematurely; better to surface the questions explicitly and let the team answer them together.

## Status

Proposed
