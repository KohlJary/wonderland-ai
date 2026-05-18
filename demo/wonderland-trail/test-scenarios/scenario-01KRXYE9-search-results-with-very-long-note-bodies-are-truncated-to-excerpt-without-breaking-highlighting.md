## Scenario 207: Search results with very long note bodies are truncated to excerpt without breaking highlighting

**GUID:** 01KRXYE929PR8CE0PNGR2QFKHN
**Severity:** degradation

**Setup:**

Kohl has a note with body: 30,000 characters (full research log). She searches for 'ablation'. The match is found at character 15,000 in the body.

**Trigger:**

Search endpoint returns result with body_preview truncated to 150 characters. The match might be outside the preview window.

**Expected:**

The search result displays a 150-char excerpt. If the match is outside the excerpt, the excerpt should ideally show context around the match (e.g., start 50 chars before the match, end 100 chars after). Otherwise, the matching note is returned but the preview doesn't show the match, which is acceptable (Kohl clicks to view).

**Concern:**

If the excerpt is truncated arbitrarily (e.g., chars 0-150) and the match is at chars 15,000, the preview shows no match but the note is still returned. Kohl might think the match is not there and skip clicking. Alternatively, if the highlighting logic tries to highlight a match outside the excerpt bounds, it fails or highlights the wrong text.

**Property:**

For all notes with matches outside the preview excerpt, either (a) the excerpt is repositioned to show context around the match, or (b) the preview is clear that the full note exists and can be clicked to view the full context.

**Implies:**
- Implies backend concern: When returning search results, include not just body_preview (first N chars) but also the offset of the match within the body. Frontend can then center the excerpt around the match. Flag for Tweedledum.
