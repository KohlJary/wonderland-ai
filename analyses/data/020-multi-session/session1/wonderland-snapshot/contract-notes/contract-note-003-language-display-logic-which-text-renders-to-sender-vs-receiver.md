## Contract Note 003: Language display logic: which text renders to sender vs. receiver

**State:** agreed
**Contract Version:** rendering v1 (sender→original_text, receiver→translated_text+attribution; pending/failed handled per contract-note-004)

**Current Shape:**

Skeleton does not distinguish sender from receiver rendering.

**Proposed Change:**

Frontend renders based on the current user's role in the conversation: If user is the message sender, render original_text (show the message they typed). If user is the receiver, render translated_text with attribution label: 'Original: [original_text in sender's language]'. Both cases check translation_status: if pending_translation, show 'translating...' indicator instead of translated_text; if translation_failed, show original_text with error notice ('Translation failed; showing original'). User's language preference is read from the conversation's language_pair (not from a separate user profile) — the system assumes the current user's language is already known from the conversation context.

**Source:** ADR-001 asymmetric rendering; ADR-002 visibility; ticket-004 acceptance criteria.

**Frontend Impact (Tweedledee):** _pending_

**Backend Impact (Tweedledum):**

Backend does not distinguish sender/receiver rendering — it returns both texts and the frontend logic decides. Backend responsibility: ensure sender_id is always populated correctly (no null sender), ensure translated_text is null only when translation_status = pending_translation, ensure original_text is always non-null. The asymmetry is a frontend-side concern, not a backend-side concern; the backend is read-only at this seam.

**Resolution:**

AGREED. Contract-note-005 (Tweedledee's frontend rendering) and contract-note-003 (Tweedledum's backend responsibility) describe the same asymmetry. Backend returns both texts and sender_id; frontend renders based on current-user role: sender sees original, receiver sees translated with attribution label. Pending and failed states follow contract-note-004 (show 'translating...' or 'failed, showing original'). Canonical reference: contract-note-005 for full rendering logic.
