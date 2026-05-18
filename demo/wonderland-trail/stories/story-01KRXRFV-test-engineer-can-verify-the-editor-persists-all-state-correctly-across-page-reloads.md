## Story 014: Test engineer can verify the editor persists all state correctly across page reloads

**GUID:** 01KRXRFV251BRQPQMWQTZBXJSZ

**Persona:** Test engineer Sam: setting up test fixtures for the offline editor. She writes integration tests (Vitest + React Testing Library) that verify the editor's input behavior, markdown preview rendering, and localStorage persistence. She's establishing the test scaffolding that Kohl's notebook will be built against.

**Situation:**

The editor, preview, and localStorage logic are all in place. Sam needs to write tests that verify all three layers work together: input capture, markdown rendering, and durability across reloads. These tests will be the specification that future developers maintain against.

**Need:**

As Sam, I want to write integration tests that verify the editor captures input, renders preview correctly, and persists state to localStorage, so that regressions are caught before code ships.

**Acceptance:**
- Test suite includes tests for title and body input capture
- Tests verify that markdown renders correctly for each required feature (headers, code blocks, lists, links, images, blockquotes)
- Tests verify that state is written to localStorage on keystroke
- Tests verify that state is restored from localStorage on component mount
- All tests pass with the editor implementation in place
- Tests are organized clearly (e.g., describe('Editor'), describe('Preview'), describe('Persistence'))

**Tier:** core

**Confusion-flags:**
- Mock vs. real localStorage: tests will likely mock localStorage to avoid side effects. That's fine, but the intent is to verify behavior, not to fully exercise the real localStorage API.
- Markdown rendering tests are tricky: the preview component likely uses a markdown library that produces HTML. Tests should verify the HTML structure/content is correct, not just that the library was called.

**Realizes requirements:**
- offline-capable-app-with-client-side-markdown-rendering
