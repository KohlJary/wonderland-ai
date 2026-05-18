## Requirement 008: Offline-capable app with client-side markdown rendering

**GUID:** 01KRXR2J0DSCX2GC81886C2JA2
**Slug:** offline-capable-app-with-client-side-markdown-rendering
**Kind:** constraint
**Confidence:** operator_stated
**Source interview:** constraints-interview
**Source question:** offline_markdown

**Body:**

App must function offline. Markdown rendering must happen client-side (React component, not server-side HTML generation). This implies all note data and rendering logic lives in the browser; the backend is an optional persistence layer that can be unavailable without breaking the core experience.

**Operator quote:**

> App should work offline, Markdown rendering on client
