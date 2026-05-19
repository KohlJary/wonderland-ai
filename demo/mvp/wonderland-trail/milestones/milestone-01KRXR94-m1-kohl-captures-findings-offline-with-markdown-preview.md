## Milestone 01: Kohl captures findings offline with markdown preview

**GUID:** 01KRXR940E0Q3WA705KBQDQ84K
**Slug:** m1-kohl-captures-findings-offline-with-markdown-preview
**Order:** 1
**Deferred:** false
**Confidence:** operator_stated

**Goal:**

Establish the editor. Kohl can create a note with title and markdown body, see live preview, optionally add tags, and have her keystrokes safe in localStorage. No backend persistence yet — this milestone owns the capture moment.

**Done when:**

- Editor pane accepts title + markdown body input
- Preview pane renders markdown (headers, code blocks, lists, links, images, blockquotes) in real-time
- Tags can be added to a note during creation
- All typed content survives page reload via localStorage (keystroke buffer is resilient)
- No backend writes required for this milestone — localStorage is the persistence layer

**Consumes requirements:**

- offline-capable-app-with-client-side-markdown-rendering
- single-device-single-user-single-sqlite-file
- no-external-integrations-in-v1
- single-operator-notebook-with-no-authentication-or-setup
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
- markdown-rendering-in-a-side-by-side-preview-pane-headers-code-blocks-lists-links-images-blockquotes
