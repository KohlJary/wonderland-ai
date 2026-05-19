## Ruling 012: Merge strategy for offline localStorage vs. backend on app boot

**GUID:** 01KRXZV9D6JPK1373JST71GAWR
**Severity:** high
**Domain:** data-handling
**Source:** story Load endpoint fetches notes from SQLite with merge strategy for localStorage drift + prior ADRs on offline-first semantics

**Citation:**

Requirement 008 (offline-capable app with backend as optional persistence) + Requirement 011 (localStorage on every keystroke, db only saves when button pressed) establish the dual-layer semantics. When the app boots, Kohl's browser has localStorage (keystroke buffer, possibly offline edits), and the backend has saved notes (the authority for committed state). The merge strategy determines which version the UI presents and whether pending offline edits are preserved or discarded.

**Finding:**

Three merge strategies are coherent: (1) Optimistic: localStorage wins if it has a draft (Kohl was editing offline, her keystroke buffer is her current intent). Backend is ignored except as the fallback if localStorage is empty. (2) Pessimistic: backend wins if it has a saved note (authority semantics, backend is the source of truth, localStorage is only recovery). Offline edits in localStorage are discarded. (3) Explicit: app asks Kohl which version to use (load from backend, discard backend and keep local draft, or merge both as separate versions). Optimistic strategy is most aligned with Kohl's offline-first intent (her unsaved work is preserved). Pessimistic preserves server authority but may discard Kohl's offline edits if she was working without backend. Explicit is UX-expensive (requires decision on every boot) but is the safest for data preservation. The team must choose the merge semantics explicitly; leaving it implicit will cause bugs when Kohl's offline edits conflict with backend saved state.

**Required Remediation:**

The load endpoint must implement one of the three merge strategies deterministically. (1) If optimistic: load returns {backend_notes: [], local_draft: localStorage.current_draft || null}; frontend prefers localStorage.current_draft if present, falls back to backend notes. (2) If pessimistic: load returns {notes: backend_notes[]}; frontend ignores localStorage on boot (clears it after confirming backend state is displayed). (3) If explicit: load returns {backend_notes: [], local_draft: localStorage.current_draft || null, conflict: true_if_both_exist}; frontend shows a modal asking Kohl which version to keep. The team should choose which strategy aligns with Kohl's expected experience (preserving her offline work vs. trusting backend as authoritative vs. asking her to decide) and implement that strategy in the load endpoint response shape and the frontend bootstrap logic.

**Acceptance Criteria:**
- The load endpoint's response shape includes the chosen merge strategy (one of: optimistic/localStorage-preferred, pessimistic/backend-preferred, explicit/user-decides).
- Frontend bootstrap logic implements the chosen strategy deterministically—no silent data loss, no ambiguous conflict resolution.
- If optimistic: localStorage takes precedence if populated; backend notes are used as fallback.
- If pessimistic: backend notes are loaded; localStorage is cleared after confirmation to prevent stale draft confusion.
- If explicit: app shows a choice modal if both localStorage and backend have state; user selects which version to keep.
- The choice is documented in the ADR and the Tweedles' contract notes so future readers understand why the merge works this way.

**Residual Risk:**

If Kohl loses a backend saved note due to optimistic strategy (offline draft overwrites older backend version), she can recover it from the audit trail—but only if she explicitly asks the team to do so (no automatic version recovery UI in v1). If pessimistic strategy discards her offline edits, the data is lost irretrievably unless the app provides an explicit 'discard offline draft' warning before clearing localStorage. If explicit strategy requires Kohl to choose on every boot where localStorage and backend diverge, it creates UX friction but maximum data safety. The team should accept whichever residual risk aligns with Kohl's research workflow and data-loss tolerance.

**Compliance Implications:**

No compliance framework requirement; this is a data-integrity decision, not a regulatory one. But the merge strategy choice should be documented in the audit trail so the team can explain to Kohl why a particular version of her note is the one that persisted.

**Audit Reference:**

Merge strategy decision logged in this ruling; the load endpoint implementation will record which notes Kohl saw on boot (backend-provided vs. localStorage-provided), enabling post-hoc explanation if she questions why a note version changed.
