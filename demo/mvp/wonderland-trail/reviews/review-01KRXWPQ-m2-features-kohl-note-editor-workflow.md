## Review 024: M2 Features — Kohl Note Editor Workflow

**GUID:** 01KRXWPQNHYR1VJ1PYE679XR6Y
**Files reviewed:** .wonderland/features/feature-01KRXRMP-kohl-can-create-and-save-experimental-notes-with-title-and-body.md, .wonderland/features/feature-01KRXRMP-kohl-can-organize-notes-with-tags-and-read-them-in-markdown-preview.md, .wonderland/features/feature-01KRXRMP-kohl-can-find-past-notes-by-title-or-content-search.md
**Verdict:** accept

### Findings

#### suggestion: Feature 003 description under-specifies search behavior
**Location:** feature-01KRXRMP-kohl-can-find-past-notes-by-title-or-content-search.md:14–16
**Quote:**

```
Kohl can search or browse saved notes to retrieve previous experimental records. The note list displays titles and tags, making discovery fast.
```

**Read:** The feature description frames the capability as 'search or browse' and emphasizes tags as the discovery mechanism. The underlying story (story-01KRXRME-kohl-finds-a-past-note-by-title-or-content) specifies live substring search with case-insensitive matching as the acceptance criterion.
**Concern:** When M3 decomposes this feature into tickets, the ticket author will need to know whether 'search' means live text filtering (the story's explicit requirement) or tag-based browsing (which the feature description emphasizes). The ambiguity is resolvable but creates a contract question at decomposition time.
**Request:** Revise the feature description to make explicit that the search capability is live substring matching across title + body, case-insensitive. Example: 'Kohl can type a search term and instantly see notes whose title or body contains that term (substring, case-insensitive). Tags provide optional secondary filtering.'

### Approvals

- Rabbit has correctly grouped the foundation stories (schema, endpoints, localStorage persistence, markdown rendering, tag system) into three coherent user-facing features.
- Each feature names a distinct Kohl workflow moment: recording a note (Feature 001), organizing while writing (Feature 002), retrieving past notes (Feature 003).
- Feature personas are consistent and grounded in Alice's Kohl stories; sources trace correctly to actual story artifacts on disk.
- The operator's directive on full-text search v1 is reflected in Feature 003's title and sources, closing Alice's prior composition concern.
