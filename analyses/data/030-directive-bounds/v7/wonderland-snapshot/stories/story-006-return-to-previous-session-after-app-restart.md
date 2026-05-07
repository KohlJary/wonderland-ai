## Story 006: Return to previous session after app restart

**Persona:** Dev (using 'Dev' as a catch-all edge case): Someone running a session when they close the app (intentionally or by accident).

**Situation:**

Dev is mid-session when their computer crashes, or they close the app. They reopen it an hour later. What happened to their session?

**Need:**

As Dev, I want to know whether my interrupted session was saved or lost, so I can decide whether to log it manually or start fresh.

**Acceptance:**
- If Dev closes the app mid-session and reopens it shortly after, the app shows the session (incomplete or complete) clearly
- Dev can choose to complete the session as-is or discard it
- If Dev reopens much later (e.g., a day later), the app doesn't show a stale session; history starts fresh with a new session

**Tier:** enrichment

**Confusion-flags:**
- How long is 'shortly after' vs. 'much later'? I made this distinction but didn't define it. Is it 5 minutes? 1 hour? This is more of a technical call, but it affects user expectations.
- Is this even necessary? If the session is lost, users will just start a new one. This might be over-engineering. But the persona of someone whose focus was interrupted and who wants to know what happened feels real.
