## Story 006: Trust the app to retain data across sessions

**Persona:** Jamie, 26, a student who uses pomodoro to study. Jamie closes the app after a session, and when reopening it hours later, wants to know that the completed session is still in the history.

**Situation:**

Jamie finishes a study session, closes the app, goes to class. Hours later, Jamie checks the app to review the week's sessions. The data is still there.

**Need:**

As Jamie, I want the app to save my completed sessions permanently, so that I trust it as a record of my work.

**Acceptance:**
- Every completed session is written to local storage (database) immediately after completion
- Closing and reopening the app does not lose any session data
- Data persists across device restarts

**Tier:** core

**Confusion-flags:**
- The directive says 'design with a real database so multi-user can be added later.' This implies a backend, but it also says 'single-user local app.' The schema matters for future scope, but it might change the UX now (e.g., if we're designing for future sync, we need to think about conflict resolution).
