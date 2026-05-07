# ADR-001: Separate tables for session history and settings; transient in-memory current session

## Context

The six stories imply three data surfaces: running timer + break state, historical log of completed sessions, and user preferences. A single-user app can get away with simple storage, but the directive asks us to design with a real database so multi-user can be added later. The question is what schema shape supports both the immediate single-user flow and a future multi-user migration without major rework.

## Decision

Create three entities: `sessions` (immutable historical log), `settings` (user preferences), and a transient in-memory `current_session` that exists only during app runtime. When a timer completes, write the current session to the sessions table and reset the transient state. On app startup, load settings from database; check sessions table for any incomplete session (abandoned timer) and either resume it or discard it per user choice.

## Tradeoffs

- Transient in-memory state means the timer is not resumable across app restarts (choosing: simplicity over durability for in-flight sessions)
- Separate history table means more query complexity on the frontend to show 'today's sessions' (need to filter by date); but clean historical records and easy to migrate to multi-user later (each user gets their own partition)
- Settings as a separate table vs. config file: decision deferred, depends on Rabbit's deployment assumptions and Tweedles' tech stack (what's the deployment target?)
- No session-to-session linking yet (each session is atomic); if we later want stretch goals like 'longest streak' or 'focus-session chains', the schema supports adding a `previous_session_id` foreign key without migration pain

## Status

Proposed
