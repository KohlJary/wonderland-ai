## Scenario 159: Kohl opens the note list and sees all her tags rendered as badges below each note title

**GUID:** 01KRXXYBA04FZFE3AR0DTZ7BWJ
**Severity:** silent-wrongness

**Setup:**

Kohl has created three notes: (1) 'Rust async patterns' with tags ['rust', 'async'], (2) 'FFI notes' with tag ['c-interop'], (3) 'Empty draft' with no tags. She navigates to the note list view (GET /api/notes).

**Trigger:**

The note list renders. Kohl scans the list for visual confirmation that her tag metadata is present.

**Expected:**

Note 1 displays 'Rust async patterns' as title with two badge chips below it labeled 'rust' and 'async', visually distinct from the title. Note 2 displays title with one chip 'c-interop'. Note 3 displays title with no tag chips (clean, no empty row). All badges are small, rounded pill-shaped, in a light background color with dark text (e.g., light gray bg, dark text). Tags are left-aligned below the title, wrapping if needed.

**Concern:**

If tags don't render, Kohl has lost the organizational metadata she added during creation — the note list becomes a flat wall of titles without context. If tags render but are misaligned or overflow, she can't scan them quickly. If an empty tag renders as a blank badge, it confuses her (she didn't tag that note, so why is there a badge?).

**Property:**

Tag display faithfully represents the backend's tag_names array in the note response

**Implies:**
- Note interface includes tag_names: string[] field
- Rendering logic iterates tag_names and renders each as a badge
- Empty tag_names array (no tags) results in no badge rendering (not an 'empty' or 'no tags' placeholder)
- Tag badge styling is compact and readable (font ~12px, padding ~4-8px, margin ~2px)
- Tag order matches backend order (though backend order is not specified, frontend should preserve it)
