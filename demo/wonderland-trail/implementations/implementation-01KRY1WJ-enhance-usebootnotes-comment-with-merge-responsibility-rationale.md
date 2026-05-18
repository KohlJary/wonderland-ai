## Implementation 063: Enhance useBootNotes comment with merge responsibility rationale

**GUID:** 01KRY1WJ8F88MBJ12VBV607VKB
**Side:** frontend
**Ticket:** ticket-01KRY1TK-usebootnotes-comments-incorrectly-describe-scope-of-localstorage-merge-logic-actual-merge-happens-in-editor-not-here
**Contract:** no contract change; documentation-only enhancement to existing contract-note-01KRXXCX (keystroke-buffer-localstorage-lifecycle-and-stale-detection-via-timestamps)
**Ready for review:** yes

**Approach:**

Added architectural rationale to the JSDoc comment in useBootNotes.ts explaining why per-note buffer merging is delegated to the Editor component rather than handled in useBootNotes. The three-point explanation covers scope boundaries (global vs. per-note), access to required data (server state + localStorage buffer), and separation of concerns.

**Client State:**

no state changes; comment enhancement only

**Files:**
- frontend/src/useBootNotes.ts: enhanced JSDoc comment with three-point architectural rationale for merge responsibility delegation
