## Contract Note 004: Edit homepage seam (POST, ownership, response shape)

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

no contract yet

**Proposed Change:**

POST /user/me/homepage { markdown: string } (requires auth, token in header). Backend: validates user owns 'me' (auth token user), parses markdown, sanitizes, stores. Response: { success: bool, rendered_html: string, updated_at: timestamp } OR { error: string }. If markdown is invalid/oversized, return 400 with error message. Optimistic: client can re-render immediately with the returned HTML; don't wait for a separate GET.

**Source:** ticket-004: edit-homepage-flow-form-save

**Frontend Impact (Tweedledee):**

Frontend POSTs textarea content to /user/me/homepage on submit. Shows loading state. On success: displays returned rendered_html and updated_at (simple preview). On error: shows error message and keeps textarea populated. No draft auto-save in v1. Ownership validation is backend's job; frontend just submits with auth token and trusts auth middleware.

**Backend Impact (Tweedledum):** _pending_
