## Milestone 03: Kohl's notebook persists across restart

**GUID:** 01KRXR940E0Q3WA705KBQDQ84N
**Slug:** m3-kohl-s-notebook-persists-across-restart
**Order:** 3
**Deferred:** false
**Confidence:** operator_stated

**Goal:**

Close the loop: explicit Save button persists localStorage to SQLite backend. Kohl's notebook now survives browser restart and server restart. Persistence strategy: localStorage captures every keystroke (fast, local recovery); Save button writes to SQLite (durable, survives page reload and process restart). localStorage remains intact after Save (option B — merge-on-load strategy), giving Kohl a keystroke buffer that survives across saves.

**Done when:**

- Save button writes all notes in localStorage to SQLite backend atomically
- After Save, a page reload fetches notes from SQLite — the durable source of truth
- localStorage persists keystroke-level edits after Save (not cleared on save); merge strategy on reload favors SQLite as source of truth if localStorage and SQLite diverge
- Notes, tags, and metadata survive server restart (SQLite is durable)
- Five-minute acceptance bar is achievable: clone → run → create note → tag → search → persist (Save button) → reload browser → note and tag still there with all content intact
- No external integrations, no auth, no multi-user — single-operator single-device notebook, as promised

**Consumes requirements:**

- keystroke-level-persistence-with-dual-layer-strategy
- five-minute-setup-acceptance-bar-clone-run-create-tag-search-persist-in-browser
