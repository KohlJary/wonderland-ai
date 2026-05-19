## Scenario 274: App boots with clean session: no localStorage, backend has notes

**GUID:** 01KRY19Z4NS2MZ90DE1K35D5GE
**Severity:** breakage

**Setup:**

User opens app for the first time (or localStorage was manually cleared). Backend has 3 existing notes from prior sessions. Editor and NoteList components are mounted.

**Trigger:**

App initializes (App.tsx useEffect on mount).

**Expected:**

Both Editor and NoteList fetch fresh note state from backend. Editor shows blank form (no noteId). NoteList shows the 3 persisted notes. No localStorage state. App is ready to create a new note or edit an existing one.

**Concern:**

Currently there is NO app-level load-on-boot sequence. Editor and NoteList each independently fetch or restore, creating a race condition. If Editor.tsx mounts first and finds no localStorage, it starts blank. NoteList mounts and fetches. Both are correct individually, but there's no central coordination or transaction. If fetch fails partway through, state is inconsistent (one list has notes, the other doesn't).

**Property:**

On app boot with clean session, the frontend must reach a state where: (1) localStorage is clean, (2) all persisted notes from the backend are visible in the NoteList, (3) Editor starts blank, (4) this state is reached atomically (not partially).

**Implies:**
- Implies architectural decision: should App.tsx have a useEffect that pre-fetches all notes on boot, before rendering Editor/NoteList? Or should each component fetch independently and tolerate inconsistency? — flag for Cat.
- Implies contract gap: contract-note-002 says 'fetch persisted notes on reload' but doesn't specify who fetches (App? NoteList? both?). Need explicit boot contract.
