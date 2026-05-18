## Scenario 088: Kohl's search result for 'async' returns a preview that jogs her memory without revealing the full note

**GUID:** 01KRXVGHT2Y73C5JV7SEK1JJ76
**Severity:** degradation

**Setup:**

Kohl has a note titled 'Async Rust patterns' with a body that's 2000 characters long. She's searching for 'async' to remember which patterns she tested.

**Trigger:**

Kohl's search for 'async' returns results. She sees the result for 'Async Rust patterns' and reads the preview.

**Expected:**

The preview shows approximately the first 150 characters of the body (or the first sentence, whichever is shorter). The preview is enough to remind her of the context without forcing her to click and open the full note.

**Concern:**

If the preview is too short (50 chars), it's useless. If it's the full 2000 chars, it defeats the purpose of a list view. If the preview cuts off mid-word or mid-emoji, it looks broken.

**Property:**

Result snippets are exactly 150 chars and gracefully handle truncation
