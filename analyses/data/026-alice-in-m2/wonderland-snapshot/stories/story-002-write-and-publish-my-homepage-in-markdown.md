## Story 002: Write and publish my homepage in Markdown

**Persona:** Sam, 34, a writer and essayist. Writes in Markdown in their text editor at home. Wants the editor to feel lightweight and not get in the way of thinking.

**Situation:**

Sam has a draft essay about film criticism that's ready to publish. They want to paste it into an editor, maybe add a simple bio section above it, and have it live immediately.

**Need:**

As Sam, I want to write or paste Markdown into an editor, see a live preview, and publish it to my homepage, so that my words are live without needing to learn HTML or deal with a complex UI.

**Acceptance:**
- Editor has a text input area and a live preview pane (two-column or toggle)
- Markdown renders correctly: headings, bold, italic, links, lists, code blocks
- Publish button saves the content and updates the live page immediately
- Unpublished drafts can be saved without publishing (at least one draft slot, or auto-save)
- XSS is not possible: raw HTML input is escaped or sanitized; script tags do not execute
- Editor works on desktop and mobile (mobile may be single-column; both must be usable)

**Tier:** core

**Confusion-flags:**
- Styling: the directive mentions 'lightweight styling' but doesn't specify what that means. Can Sam add colors, fonts, custom CSS? Or just Markdown formatting? This feels like a Cat decision, but the UX consequence is real: does the editor feel like a blog CMS or a text file?
- Images: no mention of image support. Can Sam embed images with Markdown syntax? If so, where do images live? This is a scope question but also a user need — Sam might have a film still to include with the essay.
- Versioning: can Sam edit a published page and see history? Or is it overwrite-and-live? For an essayist, overwrites are usually fine, but the question feels worth asking.
