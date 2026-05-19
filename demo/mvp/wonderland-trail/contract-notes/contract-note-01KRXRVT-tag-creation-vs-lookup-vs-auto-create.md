## Contract Note 005: Tag Creation vs. Lookup vs. Auto-Create

**GUID:** 01KRXRVTH8CN33JBC24R0B09QJ
**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Backend ticket 006 mentions POST /notes/:id/tags accepts 'an existing or new tag' but doesn't specify: (a) does the endpoint accept a tag name (string) and auto-create if missing, or does it require tag_id (number) of a pre-existing tag? (b) is there a GET /tags endpoint, and if so, in v1 or fast-follow?

**Proposed Change:**

Clarify the tag association contract: (a) POST /notes/:id/tags request body — is it {tag_id: number} or {tag_name: string}? (b) If tag_name, does the backend auto-create tags on first association, or are tags pre-populated? (c) Should the frontend call GET /tags on mount to populate a dropdown, or should v1 allow free text entry without lookup?

**Source:** Ticket 009 says 'Support fetching existing tags from GET /tags endpoint (fast-follow: autocomplete; v1 is list-input only)' — but it's ambiguous whether GET /tags exists in v1, and whether it's required or optional.

**Frontend Impact (Tweedledee):**

Confirmed: auto-create-by-name is the right call for v1. I will implement tag input as free-text entry (comma or space-separated, or individual tag-chip buttons for removal). No GET /tags lookup on mount required. This keeps the editor lightweight and avoids a second round-trip on load. If autocomplete becomes important (fast-follow), I'll revisit and add GET /tags call, but v1 doesn't need it. User types tags freely, backend auto-creates, and I get back the full tag objects in the response.

**Backend Impact (Tweedledum):**

Backend implements auto-create-by-name for tags in v1. When POST /notes or PATCH /notes/:id includes tag_names: [string], the backend: (1) checks each name in the tags table; (2) for any name not found, creates a new tag (INSERT); (3) associates the note with all tag IDs (INSERT into note_tags junction table). This is all one transaction: if any constraint is violated (e.g., tag name exceeds length), the entire note operation fails. GET /tags endpoint returns {tags: [{id, name}]} in no particular order (v1); filtering by user/ownership is deferred (single-device scope). For Tweedledee's concern about lookup: in v1, he does NOT need to call GET /tags before saving. He buffers tag names client-side, sends them in POST /notes, and the server auto-creates. GET /tags is available in v1 (so it's not a surprise later) but not required for the save flow. Invariant enforced: each tag_name is globally unique within the system (one tag with name 'rust' exists; multiple notes can reference it). Cost: if Kohl shares this app with a collaborator later, we need to scope tags to user/project (violates the current invariant); that's a schema change. Acceptable for v1 single-user.
