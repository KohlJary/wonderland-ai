## Requirement 014: Core CRUD operations: create, edit, delete notes with markdown bodies and optional tags

**GUID:** 01KRXR66PGCDA33PSG8FDT2QJV
**Slug:** core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
**Kind:** scope
**Confidence:** operator_stated
**Source interview:** scope-interview
**Source question:** shipped_v1_definition

**Body:**

v1 ships with full note lifecycle: create a note (title + markdown body + zero-or-more tags), edit it, delete it. All operations persist to SQLite and survive page reload and server restart. Tags are per-note, optional but supported (one or more per note if provided).

**Operator quote:**

> Developer can clone, run, and have a working notebook. Complete with tagging.
