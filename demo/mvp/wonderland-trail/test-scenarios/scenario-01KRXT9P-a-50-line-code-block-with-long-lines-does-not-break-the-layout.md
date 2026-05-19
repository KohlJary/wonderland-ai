## Scenario 020: A 50-line code block with long lines does not break the layout

**GUID:** 01KRXT9P2QWG3M7HXFBYEWFK7E
**Severity:** degradation

**Setup:**

The editor body contains a fenced code block with 50+ lines and some lines with 120+ characters (e.g., a long SQL query or URL). The preview pane is 400px wide.

**Trigger:**

The Preview component renders the code block.

**Expected:**

The code block is readable. Either: (a) the preview pane scrolls horizontally within the code block, or (b) the code wraps to the next line, or (c) the code is monospaced and truncated with an overflow indicator. The rest of the layout is not broken. The preview pane itself does not become wider than its container.

**Concern:**

A long code block can overflow the viewport and push the layout sideways, breaking the two-pane split. If code wraps, it becomes unreadable (URLs break, syntax loses meaning). I'm expecting the code block to have `overflow: auto` or similar, but 'readable' needs to be tested, not assumed.

**Property:**

For all code blocks CB with N lines and M characters per line (N > 50, M > 120), the rendered code block fits within the preview pane's width without breaking the parent layout.
