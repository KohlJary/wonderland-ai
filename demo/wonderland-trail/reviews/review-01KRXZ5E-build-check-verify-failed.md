## Review 041: Build check (verify) failed

**GUID:** 01KRXZ5EPMEZV1M6EQHKQZMMKJ
**Files reviewed:** src/Preview.tsx
**Verdict:** request-changes

### Findings

#### block: Frontend ``npm run build`` failed
**Location:** src/Preview.tsx:18:23
**Quote:**

```
Run ``npm run build`` locally and fix the errors below. Pay special attention to unresolved imports / missing default exports — the canonical sign that a component shipped but never got wired into App
```

**Read:** The verification runner ``verify`` reports that the implementation in this state cannot run cleanly.
**Concern:** ``npm run build`` exited with code 2. The frontend doesn't build cleanly — could be TypeScript errors, missing imports, an orphaned component (built but never wired into the entry point), or a Vite config mismatch.
**Request:** Run ``npm run build`` locally and fix the errors below. Pay special attention to unresolved imports / missing default exports — the canonical sign that a component shipped but never got wired into App.tsx.

```
src/Preview.tsx(18,23): error TS2307: Cannot find module 'dompurify' or its corresponding type declarations.
src/Preview.tsx(19,24): error TS2307: Cannot find module 'marked' or its corresponding type declarations.
```
