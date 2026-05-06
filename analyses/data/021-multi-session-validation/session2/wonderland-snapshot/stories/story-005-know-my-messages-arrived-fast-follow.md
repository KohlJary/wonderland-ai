## Story 005: Know my messages arrived (fast-follow)

**Persona:** Sam (the book club organizer), realizes mid-conversation that she's not sure if the person on the other end received her last message or if there's a connectivity issue.

**Situation:**

Sam sent a message but didn't see the other person respond. She doesn't know if they saw it, if the connection dropped, or if they're just thinking.

**Need:**

As Sam, I want to know that my message was delivered and received, so I'm not left wondering if communication broke down.

**Acceptance:**
- After I send a message, there's a visible indicator it reached the server (checkmark, 'sent', etc.).
- If there's a connectivity issue, I get some feedback (error toast, offline indicator, etc.) rather than silent failure.

**Tier:** fast-follow

**Confusion-flags:**
- How much UX complexity is acceptable for v1? Is a loading spinner enough, or do we need explicit 'message sent' / 'message failed' states?
