## Scenario 037: Kohl includes a blockquote and a link in her markdown, sees both render correctly in the preview

**GUID:** 01KRXTA3XPB15WS3APKGDFPEW9
**Severity:** silent-wrongness

**Setup:**

Kohl has the editor open and wants to include a blockquote (indented quote) and a reference link in her markdown.

**Trigger:**

Kohl types markdown: '> This is a key finding from the paper

See [reference link](https://example.com/paper) for details.'

**Expected:**

The preview pane renders the blockquote as indented, italicized, or visually distinct from regular text (standard blockquote styling). The link renders as a clickable hyperlink with the link text and URL intact. Kohl can click the link and it opens in a new tab.

**Concern:**

Blockquotes and links are common in research notes. If either doesn't render, Kohl's notes look broken or unstructured. Links are actionable — if they don't render or aren't clickable, the preview is incomplete.

**Property:**

Markdown blockquote and link rendering
