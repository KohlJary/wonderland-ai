## Story 017: Kohl searches notes by title and body content

**GUID:** 01KRXWRHF0MJX3M4TYVP2PEKP2

**Persona:** Kohl, 30, AI Researcher

**Situation:**

Kohl has accumulated experimental notes over several sprints and needs to relocate a specific note. She remembers a phrase or concept from the body ('transformer attention,' 'gradient scaling,' 'ablation study') but not the exact date or tags she applied.

**Need:**

As Kohl, I want to search across note titles and bodies by keyword or phrase, so that I can find past notes without remembering their tags or creation date.

**Acceptance:**
- Search input field accepts freeform text
- Search returns notes matching the query in title or body (case-insensitive)
- Search results show matching note previews (title + first 100 chars of body, with match highlighted if possible)
- Search is performant even with 100+ notes (no noticeable lag on keystroke)
- Empty search or cleared search returns to the note list / inbox view

**Tier:** core

**Confusion-flags:**
- Should search be real-time (as Kohl types) or only on Enter / button press? Real-time is better UX but adds performance risk if note count grows. Need to pick the tradeoff.
- Should search support regex or boolean operators (AND, OR, NOT), or only simple substring matching? Simple substring is more intuitive; operators are more powerful but harder to explain. Defer to fast-follow unless Kohl's researcher instinct argues otherwise.
- Should search results be sortable (by date, relevance, title)? For v1, probably not — just return them in some stable order (most recent first, or alphabetical). Fast-follow if Kohl needs sorting.

**Realizes requirements:**
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
- findability-kohl-can-relocate-past-notes-by-content-not-just-metadata
