## Ticket 004: Build return-to-work prompt and session resumption

**Sources:** take-a-break-and-return-to-work
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5-1 day, 85% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: break-timer-ui
- Soft: session-history-list

**Description:**

After break ends, prompt user to return to focus session or start a new one. Minimal UX: 'Ready to focus?' with CTA to start next session. This is the closure of the focus-break-focus loop. Coordinate with backend for session/break sequencing so the history log can capture the pair.

**Acceptance:**
- Prompt appears when break timer completes
- User can start a new focus session from the prompt
- Session-break pair is recorded as a logical unit in history

**Risk:**

Low. Primarily UX state management.
