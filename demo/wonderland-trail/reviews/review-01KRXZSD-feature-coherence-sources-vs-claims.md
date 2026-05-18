## Review 043: Feature coherence: sources vs. claims

**GUID:** 01KRXZSDBAKH3HVJWA5QWQ6Z1T
**Files reviewed:** .wonderland/features/feature-01KRXX3C-kohl-creates-and-saves-experimental-notes-with-markdown-bodies.md
**Verdict:** request-changes

### Findings

#### change-required: Feature claims durability but sources don't include backend persistence stories
**Location:** feature description + sources section
**Quote:**

```
"Kohl opens the editor, writes a title and markdown-formatted body content, and saves. The note persists to localStorage so keystrokes survive page reload and browser restart without backend dependency." Sources: localstorage-backed-note-state-layer, kohl-records-an-experimental-note-with-title-and-body
```

**Read:** Feature 004 claims Kohl's notes 'persist...across browser restart,' which implies full-stack durability (client-side keystroke buffering + server-side durable storage). The sources list only the localStorage buffering story and the Kohl persona story. Three essential backend integration stories exist on disk (save endpoint 01KRXZJRZ7SWB69XK08PXVYNEX, collision detection 01KRXZJRZ7SWB69XK08PXVYNF0, frontend save integration 01KRXZM1NPKFYDBZHDA4GRTS4Y) that enable the 'browser restart' durability promise, but they're not sourced.
**Concern:** When Feature 004 is decomposed in M3, those three backend stories will either be duplicated under another feature or orphaned. Either outcome wastes budget. More importantly, the feature's claim and its sources don't align — a future reader of this feature will see 'saves across browser restart' and expect full-stack persistence work in the sources, but will only find client-side buffering. This coherence gap is a recipe for M3 decomposition errors and M4 rework.
**Request:** Revise Feature 004's sources to include the three backend integration stories (01KRXZJRZ7SWB69XK08PXVYNEX save endpoint, 01KRXZJRZ7SWB69XK08PXVYNF0 collision detection, 01KRXZM1NPKFYDBZHDA4GRTS4Y frontend save integration). The feature remains user-facing (Kohl's core need); it just honestly names all the work required to deliver what the title promises. Alternatively, retitle Feature 004 to 'Kohl drafts notes with keystroke recovery' (client-side only) and create a separate feature 'Kohl's notes persist durably to backend' that sources the three backend stories. Either approach is coherent; the current state is not.

### Approvals

- Rabbit's decomposition of Kohl-facing features from foundation plumbing is sound in shape — the split between 'Kohl's user-facing capabilities' (create, organize, search, read) and 'project gains substrate' (schema, component structure) is coherent.

### Cross-domain references

- This is a composition-level coherence issue; no architectural decision is implied by requesting sources alignment. The Caterpillar is surfacing a pattern gap in how backend integration stories should flow into user-facing features — the team should consider a composition heuristic for future M2: when a user-facing feature's acceptance criteria name durability/persistence/integration with external systems, the feature's sources must include the integration stories that enable those criteria.
