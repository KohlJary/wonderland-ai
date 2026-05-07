## Scenario 008: Pathological markdown: parser handles deeply nested, long, or spam input without timeout

**Severity:** degradation

**Setup:**

User publishes markdown with 100+ levels of nested lists/blockquotes, 50K-char lines, or 10K blank lines.

**Trigger:**

POST /homepage/:slug with {content: pathological_markdown}. Backend markdown parser begins.

**Expected:**

Parse completes in <5 seconds, renders to HTML, returns 200. No parser hang, no 500 error, no output explosion.

**Concern:**

Markdown parsers can have pathological worst-case behavior (quadratic parsing, ReDoS in regex, exponential output size). Deep nesting or long lines trigger hangs.

**Property:**

For all markdown M <= 1MB: parser completes in <= 5 seconds, output <= 10MB. No indefinite hangs on any valid input <= 1MB.
