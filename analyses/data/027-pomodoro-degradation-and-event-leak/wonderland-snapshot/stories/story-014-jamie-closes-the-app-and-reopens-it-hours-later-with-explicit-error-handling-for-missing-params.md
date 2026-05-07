## Story 014: Jamie closes the app and reopens it hours later—with explicit error handling for missing params

**Persona:** Jamie, 45, accessibility advocate. She uses the app with screen reader and keyboard navigation. She closes the app in the middle of a session. Hours later, she reopens it. The app queries her session by ID. The server returns the session state, and Jamie continues exactly where she left off.

**Situation:**

Jamie closed the app. When she reopens it, the client code queries GET /sessions/{session_id}. The server requires the query to include date params (e.g., 'as of today' or 'since yesterday'). If the client forgets those params, the server returns an explicit 400 error, not a default or silent fallback. Jamie never sees this error—the app is written to always provide those params. But when an update happens mid-development, the explicit error catches it in testing, not in production.

**Need:**

As Jamie, I want the app to remember exactly where I was when I closed it, with no silent defaults or re-initialization, so that my accessibility flow is not disrupted by opaque session recovery logic.

**Acceptance:**
- Close app mid-session: session ID is recorded locally
- Reopen app hours later: client queries GET /sessions/{session_id} with required date params present
- Server returns session state with all fields populated (language pairs, positions, settings, startTime, createdAt)
- No silent defaults applied; if a query param is missing, server returns explicit 400 Bad Request with error shape from contract
- Accessibility: session recovery is transparent to the screen reader; the UI state is identical to the pre-close state

**Tier:** core

**Confusion-flags:**
- Error handling: the contract specifies 'required date params with no defaults,' but I don't know what happens on the *frontend* when a param is missing. Is there a graceful fallback, or does the error propagate to the user? The story assumes the client is always correct—but that assumption lives in Tweedledee's code, not in this story.
- Accessibility implications: I'm assuming session recovery doesn't require user intervention (no 'choose a recovery option' dialog). If it does, I need a new story grounded in Jamie's screen-reader experience.
