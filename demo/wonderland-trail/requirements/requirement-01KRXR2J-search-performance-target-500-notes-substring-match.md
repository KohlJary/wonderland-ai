## Requirement 012: Search performance target: ~500 notes, substring match

**GUID:** 01KRXR2J0DSCX2GC81886C2JA6
**Slug:** search-performance-target-500-notes-substring-match
**Kind:** constraint
**Confidence:** operator_stated
**Source interview:** constraints-interview
**Source question:** search_performance

**Body:**

The notebook targets a personal scale (~500 notes maximum). Substring search across titles, bodies, and tags is the requirement. No full-text indexing or ranking is needed; simple LIKE queries or in-memory filtering will suffice at this scale.

**Operator quote:**

> ~500 notes target
