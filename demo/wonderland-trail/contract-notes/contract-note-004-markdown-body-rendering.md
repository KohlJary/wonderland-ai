# Contract Note: Markdown body rendering — raw storage, client-side rendering

**GUID:** 01KRXXAD-tweedle-substrate-thread-004
**State:** proposed
**Contract Version:** v1.0-markdown-body-raw-text

## Current Shape

Contract note 01KRXRTT defines body as TEXT field (max 50K), no explicit statement about format or backend processing.

## Proposed Change

Body field is raw markdown text — stored exactly as typed by Kohl, no pre-processing on backend.

- **Storage:** TEXT field, max 50K chars, UTF-8 encoded
- **Format:** raw markdown (Kohl types markdown, backend stores it as-is)
- **Processing:** I (frontend) parse, sanitize, and render; you (backend) do not

## Source

Ticket 038 (Build markdown preview component with live rendering)
Concern: markdown-body-contract-ambiguity (rendering boundary was unspecified)

## Frontend Impact (Tweedledee)

I implement:
- **Parsing:** markdown-it parser (lenient, best-effort for malformed markdown)
- **Sanitization:** DOMPurify (strict config: no script tags, safe protocol whitelist for links/images)
- **Rendering:** live HTML preview pane in editor; updates as user types

UI state: preview pane shows formatted markdown (headers, code blocks, lists, links, blockquotes, images, etc.) with formatting applied, not raw text.

Edge cases handled:
- Malformed markdown: parser is lenient, renders best-effort (no error state, just renders what it can)
- Deeply nested structures: markdown-it has depth limits, graceful degradation
- Very long body: lazy loading / virtual scroll if performance needed in v2

## Backend Impact (Tweedledum)

Store body exactly as sent. No HTML encoding, no sanitization, no markdown processing.

You guarantee:
- body is raw user input (no pre-processing)
- no injection of markdown/HTML by backend
- charset is UTF-8

This places XSS prevention responsibility on the frontend (I sanitize), not the backend.

## Collaboration Notes

If in the future we add server-side markdown rendering (e.g., for email notifications or shared views), we'll need to revisit this contract and coordinate sanitization (who's responsible for what). For v1, client-side rendering is sufficient for Kohl's single-device workflow.

## Resolution

Proposed — awaiting your confirmation that this matches your storage strategy and that body will be raw user markdown without processing.
