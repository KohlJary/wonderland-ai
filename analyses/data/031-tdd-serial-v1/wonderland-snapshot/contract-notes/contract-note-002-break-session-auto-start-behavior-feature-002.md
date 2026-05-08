## Contract Note 002: Break Session Auto-Start Behavior (Feature 002)

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none

**Proposed Change:**

When a focus session completes, the break timer should auto-start without user action. The break timer uses the same Session State shape as focus sessions (type='break' instead of 'focus'). User can skip the break with an explicit 'skip' tap.

**Source:** story-002 (break must auto-start; user must explicitly skip, not accidentally skip)

**Frontend Impact (Tweedledee):**

After focus session completion, UI automatically transitions to break timer UI (no user tap needed). Break timer renders with same countdown logic as focus timer. Skip button is prominent (user must intend to skip, not accidentally tap). User cannot restart/resume a skipped break (once skipped, next action is to start new focus session).

**Backend Impact (Tweedledum):**

Break timer uses same session shape as focus ('type=break'). Auto-start is frontend-only (UI transition). Break completion logs the same way as focus: 'session_completed' event when break reaches 0ms and user does NOT skip. If break is skipped, we log 'session_skipped' event (used by feature 003 to count 'skipped breaks'). Open question (same as feature 001): what's the completion semantics — do paused breaks resume, or does pause+close = incomplete? This affects whether we log on completion or on any termination event.
