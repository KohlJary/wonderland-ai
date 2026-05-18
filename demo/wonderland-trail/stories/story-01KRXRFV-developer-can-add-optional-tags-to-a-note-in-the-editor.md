## Story 013: Developer can add optional tags to a note in the editor

**GUID:** 01KRXRFV251BRQPQMWQTZBXJSY

**Persona:** Dev Maya: adding the tagging surface. She modifies the editor to accept a tags input (comma-separated or tag-select widget), stores tags alongside title and body, and ensures tags are persisted to localStorage. She's setting up the categorical metadata surface that Kohl will use to organize her notes.

**Situation:**

The editor persists title and body; Maya now needs to add tags. The requirements say tags are optional per note but supported. She needs a UI surface to add/remove tags and ensure they're stored together with the note content.

**Need:**

As Maya, I want the editor to accept zero or more tags per note, and persist them to localStorage alongside the title and body, so that Kohl can categorize her notes.

**Acceptance:**
- The editor has a tags input field that accepts comma-separated tag values (or a tag-select UI)
- Tags are stored as an array in localStorage together with title and body
- On page load, tags are restored from localStorage
- A note can have zero tags, one tag, or multiple tags
- The tag display is clear: Kohl can see what tags are assigned and can add/remove them without confusion

**Tier:** core

**Confusion-flags:**
- Tag input UI design not specified — assuming comma-separated or simple text input for now. If there's a UX preference (tag chips, autocomplete, etc.), that should come from Alice.
- No tag search/filter logic in this story — this story is only capture + persist. Searching by tag is a follow-on story.

**Realizes requirements:**
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
