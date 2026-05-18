## Implementation 061: Clarify useBootNotes contract: remove misleading merge-logic JSDoc

**GUID:** 01KRY1P2772400R52B0S2CRBWP
**Side:** frontend
**Ticket:** 078
**Contract:** ticket-066 (frontend-load-on-boot): GET /notes returns list for display; Editor handles per-note buffer merging via its own useEffect when noteId is loaded
**Ready for review:** yes

**Approach:**

Rewrote JSDoc to correctly document that useBootNotes fetches the backend note list for display only. Per-note localStorage merge is Editor's responsibility (it checks timestamps and shows merge UI when loading a specific note by ID). Removed unused LocalStorageBuffer interface. Simplified implementation comments.

**Client State:**

None — this hook has no client state. It reads from backend via listNotes() and returns the fetched notes list in BootNotesState. Per-note state (Editor's keystroke buffer) is managed separately by Editor.tsx.

**Files:**
- frontend/src/useBootNotes.ts: simplified JSDoc (removed false merge contract), removed LocalStorageBuffer interface, cleaned implementation comments
