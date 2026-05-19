## Contract Note 018: Markdown body rendering: raw text storage, client-side rendering

**GUID:** 01KRXXE8K7VBJ6YPR6YB9WJWBG
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

Contract note 001 defines body as TEXT field (max 50K), no explicit statement about format or backend processing.

**Proposed Change:**

Body field is raw markdown text (as typed by Kohl, no pre-processing). Max 50K chars, UTF-8. I parse and render on the frontend; you store as-is. Contract version: v1.0-markdown-body-raw-text.

**Source:** Ticket 038 (Build markdown preview) + concern about rendering boundary.

**Frontend Impact (Tweedledee):**

I implement markdown parsing (markdown-it), sanitization (DOMPurify, strict config), HTML rendering. Live preview pane updates as user types. Markdown formatting displayed with formatting applied, not raw text.

**Backend Impact (Tweedledum):**

Store body exactly as sent. No HTML encoding, no sanitization, no markdown processing. Frontend handles all rendering and XSS prevention.
