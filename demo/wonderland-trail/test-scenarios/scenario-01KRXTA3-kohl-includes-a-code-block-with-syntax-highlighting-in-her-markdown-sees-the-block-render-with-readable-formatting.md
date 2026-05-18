## Scenario 036: Kohl includes a code block with syntax highlighting in her markdown, sees the block render with readable formatting

**GUID:** 01KRXTA3XPB15WS3APKGDFPEW8
**Severity:** degradation

**Setup:**

Kohl has the editor open with a draft note. She wants to include a code example (Python) in her markdown body.

**Trigger:**

Kohl types markdown with a triple-backtick code block: ```python
def find_notes(query):
    return db.query(Note).filter(...)
```

**Expected:**

The preview pane renders the code block as a monospace block with light syntax highlighting (different colors for keywords, strings, function names). The code is readable and distinct from paragraph text. Line numbers are optional (nice-to-have, not required for v1).

**Concern:**

Code readability is critical for Kohl's use case (experimental notes often include snippets). If the code block renders as plain monospace without highlighting, it's harder to scan. If the block overflows the preview pane horizontally, text wraps or scrolls awkwardly.

**Property:**

Code block rendering with syntax highlighting

**Implies:**
- preview-layout-handles-long-code-lines-without-horizontal-scroll
