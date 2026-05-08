# ADR-001: Pomodoro Timer: Local-First with Optional Cloud Sync

## Context

The five user stories describe session timers (focus + break), daily review, persistent settings, and optional gamification. Together they imply two persistent stores: ephemeral session state (today's sessions, current break) and durable user data (settings, optionally streak/history). The team needs to know whether these sync across devices or live locally only.

## Decision

Adopt a local-first architecture: all session state and settings persist to local storage (device-level database or filesystem). This works for web (IndexedDB) and mobile (SQLite) without requiring a backend. Daily review reads from local storage only. If gamification is added later, streak state also persists locally. The open question is whether to add optional cloud sync (a future ADR if the user story evolves).

## Tradeoffs

- Closed: no server, no user accounts, no cross-device sync. This is acceptable if each user runs the app on one device, or accepts that sessions on device-A are invisible to device-B.
- Open: if a future story requires 'view my sessions from any device' or 'backup my data,' we move the durable schema to a backend and add sync logic. That is a separate architectural decision, revisited when the requirement clarifies.
- Open: gamification (streak) staying local means the streak resets if the user uninstalls and reinstalls. If 'streak persists across reinstall' becomes a requirement, that forces cloud storage.
- Gain: no authentication, no CORS, no rate limiting, no backend uptime dependency. The app works offline by design.
- Gain: schema is simple — one local store per user (no multi-tenancy, no migrations across server versions).

## Status

Proposed
