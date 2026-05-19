## Ticket 023: Frontend ``npm run build`` failed

**GUID:** 01KRXTR0215JSY98P1MWRB59CE
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, build-check-verify-failed
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** review_synthesis
**Test design:** default
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``build-check-verify-failed`` (block):

**Concern:** ``npm run build`` exited with code 2. The frontend doesn't build cleanly — could be TypeScript errors, missing imports, an orphaned component (built but never wired into the entry point), or a Vite config mismatch.

**Request:** Run ``npm run build`` locally and fix the errors below. Pay special attention to unresolved imports / missing default exports — the canonical sign that a component shipped but never got wired into App.tsx.

```
src/Preview.tsx(18,23): error TS2307: Cannot find module 'dompurify' or its corresponding type declarations.
src/Preview.tsx(19,24): error TS2307: Cannot find module 'marked' or its corresponding type declarations.
src/useLocalStorageDebounce.ts(18,27): error TS2503: Cannot find namespace 'NodeJS'.
```

**Location:** ``src/Preview.tsx:18:23``

**Acceptance:**
- Run ``npm run build`` locally and fix the errors below. Pay special attention to unresolved imports / missing default exports — the canonical sign that a component shipped but never got wired into App.tsx.

```
src/Preview.tsx(18,23): error TS2307: Cannot find module 'dompurify' or its corresponding type declarations.
src/Preview.tsx(19,24): error TS2307: Cannot find module 'marked' or its corresponding type declarations.
src/useLocalStorageDebounce.ts(18,27): error TS2503: Cannot find namespace 'NodeJS'.
```
