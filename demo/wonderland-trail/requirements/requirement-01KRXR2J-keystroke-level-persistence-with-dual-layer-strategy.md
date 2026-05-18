## Requirement 011: Keystroke-level persistence with dual-layer strategy

**GUID:** 01KRXR2J0DSCX2GC81886C2JA5
**Slug:** keystroke-level-persistence-with-dual-layer-strategy
**Kind:** constraint
**Confidence:** operator_stated
**Source interview:** constraints-interview
**Source question:** unsaved_edits

**Body:**

The app must not lose content. Strategy: localStorage on every keystroke (fast, local, survives browser restart), with explicit 'Save' button that writes to the backend SQLite database. This gives the user two safety nets: keystroke-level recovery via localStorage, and deliberate persistence via the button press.

**Operator quote:**

> Save on every keystroke (safest, may impact performance at scale); localStorage on every keystroke, db only saves when button is pressed
