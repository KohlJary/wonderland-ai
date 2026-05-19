## Scenario 095: Instant filtering as Kohl types: He types 'attention' one character at a time, results update live

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY41
**Severity:** breakage

**Setup:**

App has 20 notes, 3 of which contain 'attention' in title or body. All 20 are visible in the list.

**Trigger:**

Kohl types 'a', then 't', then 't', then 'e', then 'n', then 't' — six keystrokes.

**Expected:**

After each keystroke, the results list updates to show only notes matching the prefix. 'a' shows notes with 'a' anywhere. 'att' shows notes with 'att'. By 'attent', the 3 attention notes are visible.

**Concern:**

The story says 'search results appear instantly as Kohl types (no search button required)'. This implies client-side filtering of a pre-fetched list (instant = no network round-trip per keystroke). But the tickets describe a backend /api/search endpoint. A backend search can't be instant (network latency). Either the story is wrong, the tickets are wrong, or there's a design choice being glossed over.

**Property:**

Search results update without perceptible lag (< 100ms) as the user types each character.

**Implies:**
- Implies architectural decision: client-side filter of listNotes() vs server-side /api/search endpoint. Story implies client-side; tickets imply server-side. Flag for Cat.
