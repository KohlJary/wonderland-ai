# ADR-001: Session persistence and history shape in pomodoro tracker

## Context

A pomodoro tracker must hold session state across app restarts (story: return-to-previous-session-after-app-restart), accumulate session records across time horizons (story: review-today's-session-count, weekly and all-time), and export that history in a form suitable for external use (story: share-session-history-as-proof-of-effort). The directive names multi-user capability as future work but present design is single-user local. The question is whether the persistence layer is shaped for single-user convenience (local SQLite with schema tailored to single-user reads) or for future multi-user composition (normalized schema, user_id as primary partition, records as immutable facts).

## Decision

Design the persistence layer for future multi-user composition: (1) every session record is an immutable fact keyed to (user_id, session_id, timestamp); (2) settings are per-user metadata; (3) history reads are windowed queries (today, week, all-time) against this fact store, not materialized views. In this first iteration, user_id is implicit (single logged-in user), but the schema makes user_id explicit so adding multi-user auth is a schema-level change, not a reshaping of the fact model.

## Tradeoffs

- Single-user queries are slightly more verbose (filtered by implicit user_id) than a user_id-free schema would be, but this is negligible.
- Window queries (today/week/all-time) require explicit time-based aggregation rather than pre-aggregated tables. If analytics become expensive, materialized views can be added later without schema redesign.
- Settings storage as per-user rows (rather than per-user blobs) trades schema simplicity for backward compatibility and auditability — a choice toward multi-user.
- The design closes off 'guest session' flows (where a session doesn't belong to a logged-in user) unless the schema changes to make user_id nullable. If guest sessions are strategically valuable, this is a real cost; if they're not in scope, it's a non-issue. What would have to be true: a user story that demands guest usage.

## Status

Proposed
