## Story 015: Kohl records an experimental note with title and body

**GUID:** 01KRXRMEHCCPN14TM6J8PGJD7S

**Persona:** Kohl, 30, AI Researcher. Running iterative experiments; needs to capture observations, hypotheses, and results quickly during active work sessions without breaking focus.

**Situation:**

Kohl is mid-experiment: initial results are coming in, and he needs to jot down what he's observing before the detail fades. He opens his note app, types a title (experiment name + date), writes markdown-formatted observations (headers for sections, code blocks for hyperparameters), and expects it to persist.

**Need:**

As Kohl, I want to write notes with title and formatted body (markdown) and have them persist across browser sessions, so that I don't lose observations when I close the app or my browser crashes.

**Acceptance:**
- Kohl can type a title and body in a two-pane editor layout
- The editor renders markdown (headers, code blocks, lists, links) live in a preview pane as he types
- Kohl's text survives a page reload — all typed content is still there when he returns to the app
- Kohl can distinguish the title from the body visually

**Tier:** core

**Confusion-flags:**
- The 14 foundation stories mention tags but don't anchor them in Kohl's workflow — do tags matter for his note-finding need, or are they a fast-follow? The foundation work is there; the user story was missing.
- localStorage is the persistence mechanism in the foundation stories, but from Kohl's POV it's invisible — he just needs 'notes survive page reload.' The foundation layer handles the how; this story names the why.

**Realizes requirements:**
- —
