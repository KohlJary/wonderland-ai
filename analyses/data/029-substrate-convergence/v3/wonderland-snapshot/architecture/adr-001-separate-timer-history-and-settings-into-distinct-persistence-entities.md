# ADR-001: Separate Timer, History, and Settings into distinct persistence entities

## Context

A pomodoro tracker has three user roles: the person running a timer, the person reviewing history, the person configuring. Each role reads and writes at different frequencies and with different consistency requirements. The directive asks for single-user now and multi-user later. A muddled schema will break on that transition; a clear one will absorb it.

## Decision

Model the system as three entities in a single relational database:

1. **Session (Timer)**: current or in-progress session. Fields: id, status (running|paused|completed), session_length, break_length, started_at, paused_duration. Updated frequently. Immutable once completed.

2. **SessionRecord (History)**: completed sessions, append-only. Fields: id, completed_at, session_duration, break_duration, session_type (focus|break). Never updated; only written on session completion.

3. **Settings (User Preferences)**: Fields: id, focus_session_length_minutes, break_length_minutes. Read on app startup and on settings change; written on settings change only.

Data contract: Timer owns the state machine and writes completion events to SessionRecord atomically. History consumes only the completed records. Settings is independent.

## Tradeoffs

- Three tables instead of one larger blob — adds conceptual overhead but pays off immediately when multi-user arrives (single foreign key per table).
- Timer->History write must be atomic; if we later need async event processing (for analytics, for distributed systems), this decision will need revisiting. For now: single-database transaction is fit.
- Settings are reloaded on every app-restart and on explicit change; we're trading a small read cost for simplicity. If settings-read becomes a bottleneck (hint: it won't), cache is a local fix.
- No audit trail on Settings changes — we're not tracking who changed what or when. If compliance arrives later, we'll need to add timestamps and a changelog table. For single-user local app: acceptable.
- Break time is not its own session record initially; it's just a timer state. If the user story later demands 'review break patterns' separately, we'd add a third entity. For now: breaks are implicit in the session flow.

## Status

Proposed
