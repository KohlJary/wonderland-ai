## Scenario: User publishes markdown with deeply nested structures or pathological patterns

**Severity:** degradation

**Setup:**

A user (malicious or not) publishes markdown content that is technically valid but contains pathological patterns:
- Deeply nested lists or blockquotes (100+ levels deep)
- Extremely long single line (50,000+ characters)
- 10,000 consecutive blank lines
- Unicode lookalike characters (е vs. e, О vs. 0)
- Markdown-in-markdown (nested code blocks with markdown inside them)
- Repetitive link text with huge URLs
- Valid markdown that, when rendered, produces enormous HTML (e.g., deeply nested tables)

**Trigger:**

POST /homepage/:slug with {content: "pathological markdown"}. The markdown parser begins processing.

**Expected:**

The server should:
1. Parse the markdown successfully (it's technically valid)
2. Render it to HTML without hanging or crashing
3. Store and return the rendered HTML
4. Serve the content to readers without browser performance degradation

The user should receive a 200 response with the rendered content.

**Concern:**

Markdown parsers (especially regex-based ones or those with pathological worst-case behavior) can hang on deeply nested input. remark (the recommended parser) is generally safe, but:

1. **Parser timeout** — if nested structures cause quadratic or exponential parsing time, the request could hang or timeout, causing 500 Internal Server Error or 503 Service Unavailable.
2. **Regex denial of service (ReDoS)** — if the parser or sanitizer uses regex with catastrophic backtracking, pathological input could cause hangs.
3. **Output explosion** — deeply nested markdown might expand to multi-megabyte HTML, causing memory issues or response timeouts.
4. **Browser performance** — even if the server renders successfully, the resulting HTML could be so large or complex that browsers struggle to display it.

The degradation is: the server takes a very long time to parse, or returns a 500/503, or serves HTML that browsers can't render in reasonable time.

**Property:**

For all markdown strings M ≤ 1MB, the parser must complete in ≤ 5 seconds (configurable SLA). Rendering should not produce HTML >10MB (sanity limit). The server should not hang indefinitely on any input ≤ 1MB.

**Implies:**

Implies a decision about parser timeout enforcement and output size limits — flag for Cat if the implementation does not have configurable timeouts or max-output-size limits.
