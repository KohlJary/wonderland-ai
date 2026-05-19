## Contract Note 006: Editor Save Failure and Recovery

**GUID:** 01KRXRVTH8CN33JBC24R0B09QK
**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Ticket 007 specifies localStorage buffering and 'Clear localStorage after successful save,' but does not address: (a) what happens if POST /notes fails? (b) should I retry automatically or prompt the user? (c) if the POST succeeds on the server but the response is lost (network partition), how do I know?

**Proposed Change:**

Define the failure contract: (a) if POST /notes returns 4xx or 5xx, should I preserve the localStorage draft and show an error, or clear it? (b) Can the frontend assume the POST is idempotent (same title/body = same result), or should I request an idempotency key from the backend? (c) For v1, is simple error handling (show 'Save failed, try again') acceptable, or do I need to implement automatic retry with exponential backoff?

**Source:** The localStorage buffer prevents data loss during page reloads, but the failure recovery path is unspecified. This affects component state shape (do I track 'saving' / 'error' / 'retry_count' states?) and UX (what does the user see when Save fails?).

**Frontend Impact (Tweedledee):**

Simple error handling: Save button is disabled during the POST, if it fails I show an error message and the button re-enables for manual retry. This requires tracking {isSaving: boolean, error: string | null} in component state. More complex: I need idempotency support (track request ID, support automatic retry), which adds {requestId, retryCount} to state. For v1, I propose the simple path (manual retry), with automatic retry + idempotency as fast-follow.

**Backend Impact (Tweedledum):**

No idempotency in v1. Each POST /notes creates a new note (unique id). Each PATCH /notes/:id updates the existing note in-place. If Tweedledee sends POST /notes, gets 200, but the response is lost to network partition, the note is persisted server-side and Kohl's next interaction will create a duplicate (this is a known gap for v1, acceptable because: (a) localStorage preserves the draft so Kohl can see and manually dedupe, (b) the App is single-device single-user (no concurrent edits triggering this scenario), (c) idempotency requires request IDs, which adds client-side state complexity we're deferring). Error responses: (1) 4xx (400 Bad Request on validation failure — invalid title, tag name too long, etc.) means the request was malformed; client should preserve localStorage, show error, let user fix and retry. (2) 5xx (500 Internal Server Error, 503 Service Unavailable) means server failure; client should preserve localStorage, show 'Save failed, try again later', let user retry manually. (3) Network timeout (no response) is treated as 5xx by the client. Clear localStorage only after receiving 200 response with full persisted note. This preserves Kohl's keystroke buffer across all failure modes.
