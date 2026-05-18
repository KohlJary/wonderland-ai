## Scenario 019: A script tag in markdown is sanitized and does not execute

**GUID:** 01KRXT9P2QWG3M7HXFBYEWFK7D
**Severity:** silent-wrongness

**Setup:**

The editor body contains markdown with an embedded script tag: '<script>alert("xss")</script>'. This might come from a user pasting raw HTML, or from a malicious note if multi-user ever happens (out of scope for v1, but the risk lives in the code).

**Trigger:**

The Preview component renders the body. The script tag is in the rendered HTML.

**Expected:**

The script tag is either stripped from the HTML or rendered as escaped text (visible as literal `<script>` in the preview). The alert does not fire. No network requests from the script. The HTML is safe.

**Concern:**

If we use a markdown library without built-in sanitization, or if we skip sanitization as an 'optimization', user content becomes executable code. This is the classic XSS vector. I'm betting the Tweedles will reach for react-markdown (which sanitizes by default), but 'sanitization' must be explicit in the test, not implicit in the library choice.

**Property:**

For all user-provided markdown M containing HTML tags (script, iframe, event handlers, etc.), the rendered preview contains no executable code and no XSS vectors.

**Implies:**
- Implies security decision about HTML sanitization library and settings — flag for Queen if this choice isn't already locked down.
