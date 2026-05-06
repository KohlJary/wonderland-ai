## Ticket 005: BLOCKER: Translation routing decision (sync library vs. async service)

**Sources:** message-translation-schema-asymmetric-visibility-model
**Owner:** product
**Tier:** v1
**Estimate:** 1–2 days decision time (not an implementation ticket)
**Status:** open

**Dependencies:**
- Blocks: backend-message-schema-and-storage, frontend-message-input-and-conversation-render-monolingual-view
- Blocked by: —
- Soft: —

**Description:**

This is not a Tweedle ticket. This is a business/risk decision that unblocks the Tweedles' implementation. The question: should translation happen synchronously (in-process library, e.g., LibreTranslate or Argos Translate) or asynchronously (call an external service like Google Translate or AWS Translate, queue the job, return immediately to the user with 'translation pending')? This decision affects latency SLO, error handling, cost model, GDPR surface, and the Tweedles' ticket estimates. Sync = simple, low latency, higher operational cost, limited language pairs. Async = higher latency (0.5–5s), simpler ops, more language pairs, more complex error handling. Queen will want input on GDPR implications (data in-flight to external service vs. local processing). Once this decision is made and Queen's compliance ruling lands, tickets 2 and 3 can shift from 'translation is stubbed' to 'translation actually works'.

**Acceptance:**
- Decision is made: sync library or async service
- Queen has issued her ruling on data residency and GDPR implications
- Tweedles have acknowledged receipt and can commit to revised timelines for tickets 2 and 3

**Risk:**

High. This is the critical path blocker. Without it, the Tweedles are guessing. Push for decision by EOD Thursday.
