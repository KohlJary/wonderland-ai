## Story 003: System operator confirms message delivery and translation status without UI ambiguity

**Persona:** Sam, 35, support engineer at the company. Not a chat user, but responsible for understanding what users can and cannot do in the product. Sam needs to troubleshoot when users report 'my message didn't go through' or 'the translation looked wrong.'

**Situation:**

A user emails support: 'I sent a message 10 minutes ago and my colleague never saw it.' Sam needs to check the backend logs and understand what actually happened. Is the message in the database? Is the translation API hanging? Did the message reach the other user but fail to display?

**Need:**

As Sam, I want the message history and translation status to be clear in the backend (logs, database records, API response codes), so that I can debug what went wrong without reconstructing the whole flow.

**Acceptance:**
- Each message has a unique ID and timestamp in the database
- The database record shows: original text, translated text, translation service response code, whether it was delivered to the recipient, any error messages
- Backend logs include translation API calls and responses (request, response time, success/failure)
- API responses to the frontend include clear status codes (200 for success, 4xx/5xx for errors) and error messages the user can act on

**Tier:** core

**Confusion-flags:**
- The skeleton has a health endpoint but no message-specific logging or status tracking. Real chat needs observability so the Dormouse can sleep and Sam can debug. This feels like it's missing from the skeleton.
- Who sees what in the UI? Does Klaus see 'translated' or 'translating' or 'translation failed'? Does the backend distinguish between 'message sent but not yet translated' and 'message sent and translated'? The skeleton doesn't show state handling.
