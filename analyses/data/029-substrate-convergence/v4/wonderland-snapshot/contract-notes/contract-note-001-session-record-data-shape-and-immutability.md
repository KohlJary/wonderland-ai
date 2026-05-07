## Contract Note 001: Session record data shape and immutability

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Not yet defined — session records exist as implicit browser-local state

**Proposed Change:**

Session records MUST be immutable once created (a session record is {id, start_time, end_time, duration_seconds, settings_snapshot}). A settings_snapshot is a point-in-time capture of {session_duration, break_duration} as they were at session start. This means session durations are never retroactively edited; if a user changes settings mid-week, prior sessions keep their original durations. New sessions use the new settings.

**Source:** Feature 001 (session completion), Feature 004 (history review), ADR-001 (data contract question)

**Frontend Impact (Tweedledee):**

Frontend-friendly contract. I capture session settings (duration, break duration) at session *start* time and store them immutably with the session record. When a user changes settings mid-week, those new settings apply *going forward* to new sessions only — existing session records in history stay unmodified. This simplifies the history view: no need to retroactively recalculate or display 'duration was X at the time, now Y'. Settings snapshot is the source of truth for that session's length. Cost: negligible — this is how most timers work anyway.

**Backend Impact (Tweedledum):**

You've covered it — write-once enforcement makes sense.
