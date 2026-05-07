## Contract Note 006: Discovery listing envelope (pagination, preview)

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

no contract yet

**Proposed Change:**

GET /discover?limit=10&cursor=<cursor> (no auth). Response: { homepages: [{ username, preview: string (first 200 chars of rendered_html), updated_at }, ...], next_cursor: string | null }. Cursor is opaque (backend encodes updated_at + id for stable pagination). Ordered by updated_at DESC. If no cursor provided, start from most recent. Limit max 100, default 10. Returns empty array if no more results, next_cursor=null.

**Source:** ticket-006: homepage-discovery-listing-first-cut

**Frontend Impact (Tweedledee):**

Frontend renders list from homepages array, each item shows username (as link), preview text, updated_at. 'Load more' button uses next_cursor to fetch next page. No search/filter in v1. Handles empty list. Preview text is truncated HTML—frontend should strip tags for readability (or backend can return plain text preview?). **QUESTION: should preview be HTML or plain text? HTML lets backend control formatting but frontend has to strip tags anyway.**

**Backend Impact (Tweedledum):** _pending_
