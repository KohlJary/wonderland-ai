## Ticket 007: Implement no-authentication, device-local-only mode

**Sources:** use-the-app-without-accounts-or-sign-in
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5-1 day, 85% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: persistent-storage
- Soft: —

**Description:**

Ensure the app runs entirely on the device without requiring sign-in or accounts. This is a constraint, not a feature: the app should *not* prompt for or require authentication in v1. All data lives in local storage only. Coordinate with frontend so no sign-in UI appears. The persona here is someone who wants to open the app and *immediately* focus without friction.

**Acceptance:**
- App launches without sign-in prompt
- No account creation flow is exposed in v1
- All data is stored locally, not synced to a server
- User can run the app offline

**Risk:**

Low. Primarily an integration constraint — make sure no auth middleware is inserted accidentally.
