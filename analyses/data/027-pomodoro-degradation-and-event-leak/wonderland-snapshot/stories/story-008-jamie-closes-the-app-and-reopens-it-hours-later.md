## Story 008: Jamie closes the app and reopens it hours later

**Persona:** Jamie, 19, first-time user in a language pair with limited translation support (Danish→French). Uses the app sporadically when translation requests arrive.

**Situation:**

Jamie closes the app after 20 minutes of use. Hours later, a new translation request arrives and Jamie reopens the app. The app should feel continuous, not like a fresh start.

**Need:**

As Jamie, I want the app to remember what I was doing the last time I used it, even if I close and reopen it much later, so that I feel like I'm picking up where I left off rather than starting over.

**Acceptance:**
- Session is restored from disk on app reopen
- All prior state is available without requiring re-login or re-configuration
- Settings and thread list are identical to when app was closed

**Tier:** core

**Confusion-flags:**
- Does 'hours later' imply that the server may have new data? If so, how do we reconcile? Assumption: local session is source of truth for user-controlled state; server is source of truth for content that users didn't touch.
- Not clear if there's a 'stale session' timeout — should very old sessions be discarded?
