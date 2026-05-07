# ADR-001: Separate ephemeral session state from persisted audit trail

## Context

A pomodoro tracker holds two distinct categories of state: the live session (timer, break countdown, UI animation state) and the record (completed sessions, settings, history). Naive implementations blur this line by attempting to recover partial session state on restart, or by writing the timer value to the database every second, or by maintaining session records in the database before they're complete. This creates complexity in recovery logic, noise in the audit trail, and ambiguity about what 'truth' is when the running timer and the database disagree.

## Decision

Maintain a hard boundary: ephemeral state (the live timer and break countdown) lives only in RAM and is never persisted. When the app starts, any in-flight session is abandoned — the user restarts the timer from zero. Persisted state (completed sessions and settings) lives only in the database, is write-once on completion or immediate-on-change, and is never held in memory except as a cache for display. The app's source of truth for history and settings is always the database; the app's source of truth for 'what is happening right now' is always the in-memory session state.

## Tradeoffs

- Session in progress is lost on crash/restart — the user restarts the timer. This is correct behavior (the timer is an interface to intent, not a record), but it requires that restarting feels frictionless.
- No session recovery. If the user closes the app mid-session, they restart. This is a constraint on the UI (it should make starting a new session feel instant) but it's also clarity — there's no async recovery, no 'was this session completed or interrupted' ambiguity.
- Settings and history are persisted synchronously and immediately. This keeps the database simple and the app's state legible — what the user sees in the history tab is exactly what's in the DB, no eventual consistency.
- The in-memory session state object must be minimal and completely independent from the database schema. Coupling them would re-blur the boundary. This is a design discipline, not a technical constraint, but it's worth naming.

## Status

Proposed
