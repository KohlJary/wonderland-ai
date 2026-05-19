# demo/mvp/ — mvp-demo2 shipped artifact

A working full-stack markdown notebook app, **autonomously produced
by Wonderland** running on Claude Haiku 4.5 across 3 milestones
(data layer, search/tags, persistence + validation). $83.78 total
pilot spend; operator participated as gate-approver + curator
through the [Wonderland substrate](../../README.md).

This directory is the **reproducibility artifact** for the paper:
clone the repo, follow the run instructions below, exercise the
app in a browser. The shipped code lives here; the decision
provenance lives in [`wonderland-trail/`](./wonderland-trail/).

For the pilot narrative + cost breakdown + autonomous-pilot
analysis, see:
- [analysis 034 — autonomous pilot](../../src/wonderland/closet/analyses/034-mvp-demo2-autonomous-pilot.md)
- [analysis 033 — cost breakdown](../../src/wonderland/closet/analyses/033-mvp-demo2-cost-breakdown.md)

## What got built

A single-user personal markdown notebook web app — create notes,
tag them, search across title + body + tags, render markdown in
a preview pane, persist across server restarts. Per the
[notebook directive](../../src/wonderland/closet/directives/notebook.yaml).

```
src/backend/                       backend (FastAPI + SQLAlchemy + SQLite)
  main.py + db.py                  app entry + engine
  models.py                        Note, Tag, AuditLog tables — incl
                                   revision_id collision detection + state_hash
                                   tamper detection + tz-aware datetime
                                   normalization
  api/health.py                    /health endpoint
  api/notes.py                     8 endpoints: create/read/update/delete
                                   notes, tag CRUD, full-text search with
                                   LIKE-wildcard escape discipline +
                                   _safe_ilike anti-bypass helper

frontend/src/                      frontend (React + Vite + TypeScript)
  main.tsx + App.tsx               entry + view routing (URL-pathname driven)
  api.ts                           typed API client matching backend shapes
  Editor.tsx + EditorLayout.tsx    main editor pane + preview layout
  Preview.tsx                      markdown rendering, DOMPurified
  Search.tsx                       search UI with tag filter + pagination
  NoteList.tsx                     notes list view
  TagInput.tsx                     tag chip input component
  useBootNotes.ts                  custom hook: app boot + localStorage merge
  useLocalStorageDebounce.ts       custom hook: debounced LS writes

tests/                             61 tests, all passing
  conftest.py                      in-memory SQLite per test, dep override
  test_notes.py                    happy-path CRUD
  test_notes_edge_cases.py         silent-wrongness + degradation scenarios
  test_search.py                   search + pagination
  test_search_wildcard_issues.py   LIKE-metachar escape regression tests
  test_tag_scenarios.py            tag normalization + association edges
  test_health.py                   /health smoke
```

**3,371 lines of application code + 1,577 lines of tests** (test:code
ratio 0.47). Independent cold reviewer's verdict: *"competent,
above-average code for an MVP."* See the
[code quality analysis](../../paper/artifacts/code-quality-mvp-demo2.md)
for the full review.

## Running the demo

```bash
# Backend (terminal 1)
cd demo/mvp
uv sync
uv run uvicorn src.backend.main:app --reload --port 8000

# Frontend (terminal 2)
cd demo/mvp/frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Create a note (title + markdown body).
Add tags. Save. Refresh — the note persists. Search by substring in
title or body. Filter by tag. Edit. Delete. Restart the server —
everything's still there.

```bash
# Run the test suite
cd demo
uv run pytest tests/    # 61 tests, all passing
```

## The decision trail (`wonderland-trail/`)

This is the load-bearing piece for paper readers: **the same Haiku
4.5 model that wrote this code also produced 682 markdown artifacts
documenting WHY each line exists** — requirements interviewed from
the operator, milestone trajectory, user stories with persona
grounding, features with story citations, tickets with explicit
`Blocked by:` dependencies, architectural decision records with
named tradeoffs, security rulings with threat citations, contract
notes documenting frontend/backend seam negotiation, severity-tagged
test scenarios, review verdicts with file:line citations, and the
implementation artifacts mapping each commit back to the ticket it
shipped.

This is what a single-shot LLM (with or without tools) **cannot
produce**. See [`wonderland-trail/README.md`](./wonderland-trail/README.md)
for the structure + how to read it.

## Reading order, if you're new

1. **Run the app** (above) — see what shipped.
2. **Open one file at random in `src/backend/api/notes.py`** —
   note the inline contract references (`contract-note-01KRY0B8`),
   the SQL escape helpers with anti-bypass docstrings, the
   tz-aware datetime normalization.
3. **Trace a decision back through the trail.** Pick a function
   or file, find its ticket in
   `wonderland-trail/tickets/`, then find the feature it
   sources, then the story, then the requirement, then the
   architectural ADR. Five hops; each artifact is human-readable
   markdown.
4. **Read the [code quality analysis](../../paper/artifacts/code-quality-mvp-demo2.md)**
   for an independent reviewer's verdict + the honest
   limitations.

## How this relates to the paper

- The shipped code here is the artifact the paper's quality claims
  reference.
- The trail in `wonderland-trail/` is the artifact the paper's
  *maintainability* claims reference — the decision provenance
  that distinguishes Wonderland's output from a single-shot
  agent's output.
- The pilot that produced both ran on Claude Haiku 4.5 at
  substrate version 0.8.0, cost $83.78, with the operator
  participating as gate-approver (one mid-pilot substrate fix,
  documented honestly as a Tier 2 violation).
- See [`paper/`](../../paper/) for the chapter source artifacts +
  cost breakdown.
