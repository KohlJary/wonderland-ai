## Requirement 016: Markdown rendering in a side-by-side preview pane: headers, code blocks, lists, links, images, blockquotes

**GUID:** 01KRXR66PGCDA33PSG8FDT2QJX
**Slug:** markdown-rendering-in-a-side-by-side-preview-pane-headers-code-blocks-lists-links-images-blockquotes
**Kind:** scope
**Confidence:** operator_stated
**Source interview:** scope-interview
**Source question:** shipped_v1_definition

**Body:**

v1 ships with live markdown preview. When the developer writes markdown in the editor pane, the preview pane on the right renders it as HTML. All core markdown features ship: headers (# ## ###), code blocks (```), unordered and ordered lists, links, images, blockquotes. Inline code (backticks) and bold/italic are implicit in a markdown library's baseline. This is 'shipped' not 'nice-to-have' — it's in the operator's success bar.

**Operator quote:**

> Developer can clone, run, and have a working notebook. Complete with tagging and searching.
