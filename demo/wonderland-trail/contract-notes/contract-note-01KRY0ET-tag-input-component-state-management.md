## Contract Note 022: Tag input component state management

**GUID:** 01KRY0ET90M86AFHY4NA85BAEF
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

Implicit in contract-note-004 and contract-note-019; no formal specification of how frontend collects, validates, buffers, and sends tag names.

**Proposed Change:**

Formalize tag input state: (1) Tag input component maintains local React state: tags: string[] (user-entered tag names, post-validation). (2) Validation on entry: strip whitespace, reject if empty, reject if >100 chars, reject if non-alphanumeric-dash characters. Display user feedback inline for each validation failure. (3) Deduplication: client-side rejection if user tries to add duplicate tag name (case-sensitive). (4) When note is saved via Save button, tags array is sent in POST/PUT request body as tag_names: string[]. (5) When note is loaded from GET endpoint, response tag_names and tag_ids are populated into the tag input component's state. (6) If save fails with 400 (validation error on server), tags array remains in local state for retry. If save succeeds (200), tags array is cleared only after browser navigation away from editor or explicit user action.

**Source:** Ticket 071 (tag-input-component) and ticket 072 (tag-note-association) need to define where tag state lives and how it flows through the save cycle. Contract-note-004 specifies the request/response envelope; this note specifies client-side state management boundaries.

**Frontend Impact (Tweedledee):**

I will implement tag input as React component managing local state: tags: string[], validation fn, dedup logic. On Save: merge tags into the note object being sent. On Load: extract tags from returned note and populate input. UI states: empty (no tags yet), populated (user has entered tags), error-validation (invalid tag rejected), pending-sync (tags in flight with request).

**Backend Impact (Tweedledum):**

Leave empty for Tweedledum to respond.
