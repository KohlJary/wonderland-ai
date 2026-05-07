# ADR-001: Single-user Pomodoro tracker with multi-user schema foundation

## Context

Seven stories have accumulated describing a pomodoro tracker with session timing, break management, history review at multiple timescales, customizable intervals, and explicit intent to design the schema for future multi-user support. The stories imply three distinct data flows: (1) real-time session lifecycle (start → timer → notification → break), (2) historical aggregation (today's count, this week, all-time), (3) configuration persistence (user settings). The architecture must support single-user local operation immediately while keeping the schema clean enough that multi-user addition later doesn't require reshaping.

## Decision

Design the data model around three entities: User (a singleton in single-user mode, but keyed to permit multi-user later), Session (immutable record of a pomodoro with start/end timestamps and duration), and Settings (user preferences for session and break lengths). The frontend manages session lifecycle and notifications locally; the database persists Sessions and Settings. History aggregation queries run against the Sessions table. The User entity exists as a schema placeholder even in single-user mode — it has no auth but it has a user_id foreign key on Session and Settings rows. This costs nothing in single-user operation and eliminates the reshaping work when multi-user is added.

## Tradeoffs

- The schema includes a User table that is unused in single-user mode — small cost in schema complexity for large gain in future-proofing. Alternative: store everything as user-agnostic singletons and add User later (reshapes every table). This decision trades present simplicity for future tractability.
- Notifications are client-side (browser notification API or equivalent), not persisted — a session's completion is an event, not a stored artifact. This is correct for a local app, but means notification history cannot be rebuilt from the database. Alternative: persist notification events (adds schema and query complexity for a feature the user doesn't need). Staying with client-side is right.
- The break is modeled as state within the lifecycle (session ends → break begins → break ends → ready for next session) rather than as a separate Breakrecord entity. This is simpler and correct for single-user; multi-user would not change this. Keep it.
- Settings are per-user and persist globally (no session-specific interval overrides). This matches the story; future sessions are scoped to the user's current settings. If session-level customization is ever needed, the schema can be extended.

## Status

Proposed
