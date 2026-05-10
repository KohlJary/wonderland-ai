# react-vite — React + Vite + TypeScript frontend-only skeleton

Frontend-only scaffold using Vite + React + TypeScript. The
hello-world is a counter component; tests use Vitest +
@testing-library/react. Pair with `python-fastapi` (backend-only)
for fullstack, or extend solo for a static SPA.

## What's here

- `src/App.tsx` — root component with a counter widget
- `src/main.tsx` — Vite entry point that mounts `App` to `#root`
- `index.html` — Vite HTML template
- `tests/App.test.tsx` — counter increments on click (Testing
  Library + Vitest)
- `vite.config.ts` — Vite config (vitest configured under `test`)
- `tsconfig.json` — TypeScript settings
- `package.json` — declares React, Vite, Vitest, Testing Library
- `.gitignore` — node_modules, build output

## What's intentionally left undone

- No router (intentional — pick `react-router` / `tanstack-router`
  when you have ≥2 routes)
- No state management library (intentional — `useState` works
  for v1; pick `zustand` / `redux` when state outgrows React's
  primitives)
- No styling framework (intentional — vanilla CSS in `App.css`
  is fine; pick `tailwindcss` / `styled-components` when needed)
- No API call wrapper (intentional — `fetch` is fine for v1;
  pick `tanstack/query` when there are ≥3 endpoints)

## Running

```bash
npm install
npm run dev      # http://localhost:5173
npm run test     # run vitest
npm run build    # production build to dist/
```
