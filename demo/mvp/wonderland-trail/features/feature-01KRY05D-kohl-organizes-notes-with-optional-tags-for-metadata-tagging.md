## Feature 010: Kohl organizes notes with optional tags for metadata tagging

**GUID:** 01KRY05DYSF1FQT90922AMPAGW
**Kind:** capability
**Sources:** 01KRXTYZG7J2YNVMG16Y6PFVSD:tag-input-and-display, 01KRXTZRG7K2YNVMG16Y6PFVSE:tag-input-and-association-in-the-editor, 01KRXU1ZG7L2YNVMG16Y6PFVSF:note-and-tag-schema-with-crud-endpoints
**Personas:** Kohl
**Stack span:** full-stack
**Tier:** v1

**Description:**

Kohl can add zero or more tags to a note while editing, persisting them alongside the note's body. Tags appear in the editor as input + display. The backend stores tags in a normalized schema and returns them with the note on load. Kohl can later browse notes by tag (secondary discovery path).

**Constituent tickets:**
- *(to be decomposed in M3)*
