## Scenario 021: An image URL in markdown renders as an <img> tag with the URL

**GUID:** 01KRXT9P2QWG3M7HXFBYEWFK7F
**Severity:** curiosity

**Setup:**

The editor body contains the markdown: `![alt text](https://example.com/image.png)`. The URL is arbitrary and we're not testing image fetch (that's the browser's job).

**Trigger:**

The Preview component renders the markdown.

**Expected:**

An <img> tag appears in the preview with `src='https://example.com/image.png'` and `alt='alt text'`. The browser attempts to load the image. If the image loads, it appears. If the image 404s, the browser shows the alt text or a broken-image icon.

**Concern:**

I want to surface whether relative vs. absolute URLs are handled correctly. If the user writes `![alt](./image.png)`, does it resolve relative to the app origin or fail silently? This is a UX question, not a bug — but it's worth checking.

**Property:**

For all image markdown `![alt](url)`, the rendered preview contains an <img> tag with src and alt attributes matching the markdown.
