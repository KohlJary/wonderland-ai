## Scenario 180: Search results display without match highlighting in title or preview

**GUID:** 01KRXY8P (assigned)
**Severity:** silent-wrongness

**Setup:**

Frontend has shipped Search.tsx. Kohl searches for 'transformer' and gets results where note titles and body previews contain 'transformer'.

**Trigger:**

Kohl looks at the search results displayed in the browser.

**Expected:**

The matching terms 'transformer' are highlighted visually (bold, colored background, or other visual distinction) in both the title and the body_preview excerpt so Kohl can visually scan and confirm she found the right note.

**Concern:**

The ticket explicitly requires 'Results highlight matching keywords in title and body excerpt' (ticket #36 acceptance criteria). The current Search.tsx implementation renders the title and body_preview as plain text with no `<span>` or HTML highlighting. The matches are invisible — Kohl sees the search worked because the note is in results, but she can't visually spot *where* the match is. This makes scanning results tedious and defeats the UX goal of 'instantly recognize the right note'.

**Property:**

For all search results where query Q appears in title T or preview P, render the occurrence of Q in T and P with visual distinction (not plain text).

**Implies:**

- Implies incomplete implementation — the highlighting feature in the ticket was not shipped. Flag for Tweedledee (frontend owner).
