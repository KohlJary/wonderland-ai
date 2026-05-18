## Contract Note: Search response envelope for rapid rediscovery

**GUID:** 01KRY0ATHVFP2GT97CQWJ8J7XK
**State:** agreed
**Contract Version:** search-response-envelope/v1 (final)

**Current Shape:**

From contract-note-010, the search endpoint returns:
```
{
  "total_results": <int>,
  "page": <int>,
  "page_size": <int>,
  "results": [
    {
      "id": <note_id>,
      "title": <string>,
      "body_preview": <string: 150 chars>,
      "tags": [{"id": <tag_id>, "name": <tag_name>}, ...],
      "created_at": <ISO8601>,
      "updated_at": <ISO8601>
    },
    ...
  ]
}
```

**Proposed Change:**

Clarify and lock the search response body_preview field width. Ticket 058 (backend) specifies "first 150 chars", but Ticket 059 (frontend) specifies "100 chars" for display. The discrepancy creates a contract ambiguity: does the backend send 150 and the frontend truncates? Or does the contract lock it at one or the other?

For rapid rediscovery, Kohl is scanning results quickly; a preview that's too long (150 chars) clutters the result card and slows her visual scanning. Recommend locking to 100 chars at the contract level — backend sends exactly 100 chars (or fewer if body is shorter), frontend receives and displays without truncation.

**Source:** Tickets 058 and 059 decomposition; contract clarification needed before frontend implementation begins.

**Frontend Impact (Tweedledee):**

If locked at 100 chars: frontend receives body_preview already truncated by backend, displays it as-is in the result card. No additional truncation logic needed. Result card layout is simpler: title (bold), then preview (100 chars is ~2-3 lines depending on font), then tags and updated_at. Clean and scannable.

If locked at 150 chars: frontend either displays all 150 (cluttering result cards) or truncates to 100 at display time. Truncation logic adds complexity; prefer backend sends exactly what frontend displays.

**Backend Impact (Tweedledum):**

Clarify: at what point do you truncate the body preview? Options:
1. Truncate at query time in SQL (substring/limit).
2. Truncate in Python before returning (slice result rows).
3. Send full body and let frontend truncate.

Recommend option 1 (truncate at query time) for efficiency; option 2 (truncate in Python) for simplicity. Option 3 risks bloating the response envelope with full note bodies, which hurts latency on slow networks (Kohl's "tired user" context).

**Backend Response (Tweedledum):**

Confirming: 100 chars is correct and works efficiently on the backend. Here's my reasoning:

1. **Truncation point:** I'll truncate in SQL at query time using `SUBSTR(body, 1, 100)` for each result row. Zero overhead — the database does the slicing, not Python. This is more efficient than sending 150 and having frontend truncate.

2. **UTF-8 safety:** SQLite's SUBSTR is byte-safe in UTF-8 mode by default. However, I'll add safety wrapper: if a truncation cuts mid-multibyte character (rare but possible), I'll strip the broken character and pad to valid UTF-8. Kohl won't notice the difference, and it prevents encoding artifacts in the preview.

3. **Payload efficiency:** Reducing preview width from 150 to 100 saves ~50 bytes per result × 20 results per page = ~1KB per search response. For Kohl's single-user context and typical networks, this is negligible, but it's the right direction for scaling and mobile.

4. **UX alignment:** Rapid rediscovery means Kohl is scanning. 100-char preview balances "enough context to jog memory" (ruled out by Tweedledee and confirmed in ticket-059) with "scannable without clutter." This is a UX call, not mine, but I agree with the logic.

**Resolution:**

**Agreed: backend sends body_preview as exactly 100 characters (UTF-8 safe truncation).** Contract-note-008 (the main search contract) currently specifies 150; I will coordinate with Tweedledee to update that note to 100 to keep both seams locked.

**Invariants:**
- Every result row's body_preview is exactly 100 chars (or fewer if body is shorter than 100 chars; no padding).
- Truncation is UTF-8 safe and never cuts mid-character.
- Truncation happens in SQL (efficient, consistent).

**This response marks this contract note as ready for agreement.**

---

## Tweedledee Confirmation (Frontend)

**Response from frontend Tweedle — 01KRY09G (current turn):**

Confirmed: backend sends body_preview as 100 chars. This contracts cleanly with the frontend UI expectations from Ticket 059. Frontend will:
- Receive body_preview (≤100 chars from backend)
- Display as-is in result card (no truncation logic needed)
- Layout scales cleanly: title (bold) + preview (2-3 lines @ 100 chars) + tags + updated_at

100-char envelope locks the contract across both seams. Ready to implement search UI (Ticket 059) and integration (Ticket 060) against this finalized contract.

**Implementation status (Tweedledee/Frontend):** pending; contract now stable and ready for frontend work.
**Implementation status (Tweedledum/Backend):** complete; code verified at src/backend/api/notes.py:429-449 (search_notes endpoint, body_preview slice [:100]).

**Contract locked:** search-response-envelope/v1 — backend sends 100-char body_preview; frontend displays without truncation.
