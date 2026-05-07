## Story 002: Edit my homepage in Markdown

**Persona:** Priya, 34, a writer and activist. She has a laptop. She knows enough HTML to be dangerous but prefers not to write it. She wants her page to look intentional but isn't going to hire a designer.

**Situation:**

Priya claimed her username and now sees a blank page. She wants to add a bio, a list of her writing links, and maybe a little color to make it feel like hers.

**Need:**

As Priya, I want to edit my page in a simple text format (Markdown) and see it render to a readable, styled page, so that I can control my presentation without wrestling with HTML or paying for hosting.

**Acceptance:**
- I can open an editor and write Markdown (bold, italic, headers, links, lists)
- I see a live preview of how it will look
- I can save and publish my changes
- My page is publicly visible at my URL immediately after publish
- I can go back and edit anytime — old version is replaced (no version history needed for MVP)

**Tier:** core

**Confusion-flags:**
- The directive mentions XSS — am I sanitizing Markdown input? What HTML tags do we allow? If we strip all HTML, can I embed images or just link to external ones?
- Does 'lightweight styling' mean I can add inline CSS, or is styling limited to predefined themes? The latter is safer but less personal.
- Are there any limits on page size/character count to prevent abuse?
